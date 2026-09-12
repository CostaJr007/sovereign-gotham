"""
Sovereign Gotham - Automated Test Suite for Sovereign OSDK, CAPCO, Entity Resolver, and SLM Datasets
"""

import json

import pytest

from ingestion.scrapers.dod_nsa_ingest import DoDDoctrineConnector
from ontology.capco import CAPCOMarkingEngine
from ontology.entity_resolver import IntelligenceEntityResolver
from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    Agent_Role,
    ClearanceLevel,
    Document,
    LinkType,
    OntologyLink,
    Operation,
    Procedure,
    ProcedureCategory,
    SecurityClassification,
    Target_Entity,
    TargetType,
    ThreatLevel,
)
from ontology.osdk_client import SovereignOSDKClient
from training.dataset_generator import OntologicalDatasetGenerator


@pytest.fixture
def populated_osdk_graph():
    """Populates an in-memory knowledge graph with canonical objects and links."""
    g = GothamKnowledgeGraph()

    doc = Document(
        id="DOC-CIA-1984",
        source="CIA",
        title="Operation Chopin Assessment",
        summary="Intelligence memo on target Cypher-9.",
        classification_original=SecurityClassification.TOP_SECRET,
        provenance_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )

    op = Operation(
        id="OP_CHOPIN",
        codename="CHOPIN",
        objective="Extract high-value asset before compromise.",
    )

    target = Target_Entity(
        id="TARGET_CYPHER_9",
        name="CYPHER_9",
        type=TargetType.INDIVIDUAL,
        threat_level=ThreatLevel.HIGH,
        affiliations=["KGB_FIRST_CHIEF_DIRECTORATE"],
    )

    proc = Procedure(
        id="PROC-EXTRACTION-01",
        name="Tactical Hostile Sector Extraction",
        category=ProcedureCategory.EXTRACTION,
        steps=["Isolate target", "Establish cordon", "Extract to safehouse"],
        required_clearance=ClearanceLevel.SECRET,
    )

    role = Agent_Role(
        id="COS_BERLIN",
        designation="Chief of Station Berlin",
        clearance_level=ClearanceLevel.TOP_SECRET,
        decision_authority=["AUTHORIZE_EXTRACTION"],
    )

    # Add entities
    g.add_object(doc)
    g.add_object(op)
    g.add_object(target)
    g.add_object(proc)
    g.add_object(role)

    # Add links
    g.add_link(OntologyLink(
        source_id=doc.id,
        source_type="Document",
        target_id=op.id,
        target_type="Operation",
        link_type=LinkType.REGISTERS,
    ))
    g.add_link(OntologyLink(
        source_id=op.id,
        source_type="Operation",
        target_id=proc.id,
        target_type="Procedure",
        link_type=LinkType.EXECUTES,
    ))
    g.add_link(OntologyLink(
        source_id=target.id,
        source_type="Target_Entity",
        target_id=op.id,
        target_type="Operation",
        link_type=LinkType.ASSOCIATED_WITH,
    ))

    return g


# =========================================================================
# 1. SOVEREIGN OSDK TESTS
# =========================================================================
def test_osdk_filtering_and_counting(populated_osdk_graph):
    client = SovereignOSDKClient(populated_osdk_graph)

    # Where query with kwargs
    cia_docs = client.objects(Document).where(source="CIA").fetch()
    assert len(cia_docs) == 1
    assert cia_docs[0].id == "DOC-CIA-1984"

    # Where query with lambda predicate
    ts_docs = client.objects(Document).where(lambda d: d.classification_original == SecurityClassification.TOP_SECRET).fetch()
    assert len(ts_docs) == 1

    # Count method
    assert client.objects(Document).where(source="CIA").count() == 1
    assert client.objects(Document).where(source="NONEXISTENT").count() == 0


def test_osdk_pivot_to_traversal(populated_osdk_graph):
    client = SovereignOSDKClient(populated_osdk_graph)

    # Traverse: Document -> Operation
    linked_ops = (
        client.objects(Document)
        .where(id="DOC-CIA-1984")
        .pivot_to(LinkType.REGISTERS, Operation)
        .fetch()
    )
    assert len(linked_ops) == 1
    assert linked_ops[0].id == "OP_CHOPIN"
    assert linked_ops[0].codename == "CHOPIN"

    # Chained traversal: Operation -> Procedure
    linked_procs = (
        client.objects(Operation)
        .where(id="OP_CHOPIN")
        .pivot_to(LinkType.EXECUTES, Procedure)
        .fetch()
    )
    assert len(linked_procs) == 1
    assert linked_procs[0].id == "PROC-EXTRACTION-01"


# =========================================================================
# 2. CAPCO MARKING ENGINE TESTS
# =========================================================================
def test_capco_portion_parsing():
    # Top Secret with SCI compartments and NOFORN
    p1 = CAPCOMarkingEngine.parse_portion("(TS//SI-TK//NF) The satellite array confirmed transmission.")
    assert p1 is not None
    assert p1.classification == SecurityClassification.TOP_SECRET
    assert "SI" in p1.compartments
    assert "TK" in p1.compartments
    assert p1.is_noforn is True

    # Secret with FVEY release
    p2 = CAPCOMarkingEngine.parse_portion("(S//REL TO USA, FVEY) Allied operations in Northern sector.")
    assert p2 is not None
    assert p2.classification == SecurityClassification.SECRET
    assert p2.is_fvey_releasable is True
    assert p2.is_noforn is False

    # Unclassified
    p3 = CAPCOMarkingEngine.parse_portion("(U) Public statement released to press.")
    assert p3 is not None
    assert p3.classification == SecurityClassification.UNCLASSIFIED

    # Non-marking string
    p4 = CAPCOMarkingEngine.parse_portion("Just a standard sentence without parentheses.")
    assert p4 is None


# =========================================================================
# 3. ENTITY RESOLUTION & CRYPTONYMS TESTS
# =========================================================================
def test_entity_resolver():
    resolver = IntelligenceEntityResolver(similarity_threshold=0.8)

    # Register Fidel Castro
    resolver.register_canonical(
        canonical_id="TARGET-FIDEL-01",
        name="Fidel Castro",
        cryptonyms=["AMTHUG"],
        aliases=["El Comandante", "Castro Ruz"],
    )

    # Register Karl Koecher
    resolver.register_canonical(
        canonical_id="TARGET-KOECHER-01",
        name="Karl Koecher",
        cryptonyms=["CYPHER_9"],
        aliases=["Rube"],
    )

    # 1. Resolve via cryptonym
    assert resolver.resolve("AMTHUG") == "TARGET-FIDEL-01"
    assert resolver.resolve("CYPHER_9") == "TARGET-KOECHER-01"

    # 2. Resolve via alias
    assert resolver.resolve("El Comandante") == "TARGET-FIDEL-01"

    # 3. Resolve via fuzzy match
    assert resolver.resolve("Karl Kocher") == "TARGET-KOECHER-01"
    assert resolver.resolve("Fidel Kastro") == "TARGET-FIDEL-01"

    # 4. Unknown entity returns None
    assert resolver.resolve("Completely Unknown Asset") is None


# =========================================================================
# 4. DOD DOCTRINE CONNECTOR TESTS
# =========================================================================
def test_dod_doctrine_connector():
    jp2 = DoDDoctrineConnector.get_standard_procedure("JP-2-0")
    assert jp2 is not None
    assert "Joint Intelligence" in jp2.name
    assert len(jp2.steps) == 6

    jp360 = DoDDoctrineConnector.get_standard_procedure("JP-3-60")
    assert jp360 is not None
    assert jp360.required_clearance == ClearanceLevel.TOP_SECRET
    assert "D3A" in jp360.name


# =========================================================================
# 5. ONTOLOGICAL DATASET GENERATOR TESTS
# =========================================================================
def test_dataset_generator(populated_osdk_graph, tmp_path):
    generator = OntologicalDatasetGenerator(populated_osdk_graph)
    results = generator.generate_all(tmp_path)

    # Verify all 4 files were created
    assert "operations_slm" in results
    assert "humint_slm" in results
    assert "doctrine_roe_slm" in results
    assert "graph_extractor_slm" in results

    assert results["operations_slm"] > 0
    assert results["humint_slm"] > 0
    assert results["doctrine_roe_slm"] > 0
    assert results["graph_extractor_slm"] > 0

    # Verify JSONL formatting
    ops_file = tmp_path / "operations_slm.jsonl"
    assert ops_file.exists()
    with open(ops_file, "r", encoding="utf-8") as f:
        first_line = f.readline()
        record = json.loads(first_line)
        assert "conversations" in record
        assert len(record["conversations"]) == 3
        assert record["conversations"][0]["from"] == "system"
        assert record["conversations"][1]["from"] == "human"
        assert record["conversations"][2]["from"] == "gpt"
        assert "<thought>" in record["conversations"][2]["value"]

    # Verify unified DeepSeek-R1 dataset
    unified_file = tmp_path / "sovereign_deepseek_r1_agent.jsonl"
    assert unified_file.exists()
    assert results.get("unified_deepseek_r1_agent", 0) > 0


# =========================================================================
# 6. DSPARK DUAL-ENGINE DPO CURATOR TESTS
# =========================================================================
def test_dspark_dpo_curator(populated_osdk_graph, tmp_path):
    from training.dspark_dpo_curator import DSparkTrainingCurator
    curator = DSparkTrainingCurator(populated_osdk_graph)
    dpo_file = tmp_path / "dspark_dpo_pairs.jsonl"
    count = curator.curate_dpo_dataset(dpo_file)

    assert count > 0
    assert dpo_file.exists()

    with open(dpo_file, "r", encoding="utf-8") as f:
        first_line = f.readline()
        item = json.loads(first_line)
        assert "chosen" in item
        assert "rejected" in item
        assert "curator_notes" in item
        assert "<thought>" in item["chosen"]
        assert "DENY_KINETIC_BREACH" in item["chosen"]
        assert "BLOCKED_ROE" in item["chosen"]
        assert "EXECUTE_IMMEDIATE_RAID" in item["rejected"]
