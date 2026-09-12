"""
Sovereign Gotham - Automated Test Suite
Tests Pydantic Schemas, Knowledge Graph, Ingestion, Compliance Engine, Decision Engine, and FastAPI API.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents.compliance import ComplianceEngine
from agents.decider import GothamDecisionEngine
from api.main import app
from ingestion.document_loader import DeclassifiedDocumentLoader
from ingestion.entity_extractor import OntologicalEntityExtractor
from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    ClearanceLevel,
    Document,
    LinkType,
    OntologyLink,
    Procedure,
    ProcedureCategory,
    RecommendActionRequest,
    SecurityClassification,
    ValidateComplianceRequest,
)
from storage.sqlite_store import OperationalLedger
from storage.vector_store import SovereignVectorStore


@pytest.fixture
def sample_pdf_path():
    p = Path(__file__).parent.parent / "sample_data" / "cia_crest_sanitized_report.pdf"
    assert p.exists(), "Sample PDF must exist for tests"
    return str(p)


@pytest.fixture
def populated_graph(sample_pdf_path):
    payload = DeclassifiedDocumentLoader.load_file(sample_pdf_path)
    entities, links = OntologicalEntityExtractor.extract_from_document_payload(payload)
    g = GothamKnowledgeGraph()
    for e in entities:
        g.add_object(e)
    for l in links:
        g.add_link(l)
    return g


def test_ontology_models():
    doc = Document(
        id="DOC-TEST-001",
        source="CIA",
        title="Test Surveillance Memo",
        summary="Test Summary",
        classification_original=SecurityClassification.TOP_SECRET,
    )
    assert doc.id == "DOC-TEST-001"
    assert doc.source == "CIA"

    proc = Procedure(
        id="PROC-TEST-01",
        name="Covert Evasion SOP",
        category=ProcedureCategory.HUMINT,
        steps=["Step 1: Check six", "Step 2: Change attire"],
        restrictions=["No contact with civilians"],
        required_clearance=ClearanceLevel.SECRET,
    )
    assert len(proc.steps) == 2

    link = OntologyLink(
        source_id=doc.id,
        source_type="Document",
        target_id=proc.id,
        target_type="Procedure",
        link_type=LinkType.REGISTERS,
    )
    assert link.link_type == "REGISTERS"


def test_ingestion_loader_and_extractor(sample_pdf_path):
    payload = DeclassifiedDocumentLoader.load_file(sample_pdf_path)
    assert payload["source"] == "CIA"
    assert len(payload["provenance_hash"]) == 64  # SHA256 hex length
    assert "OP_CHOPIN" in payload["raw_content"]

    entities, links = OntologicalEntityExtractor.extract_from_document_payload(payload)
    assert len(entities) >= 7
    assert len(links) >= 10

    # Ensure Target_Entity and Procedures were extracted
    proc_ids = [e.id for e in entities if isinstance(e, Procedure)]
    assert "PROC_TACTICAL_EXTRACTION" in proc_ids
    assert "PROC_HUMINT_SURVEILLANCE" in proc_ids


def test_graph_topology(populated_graph):
    stats = populated_graph.get_stats()
    assert stats["total_entities"] >= 7
    assert stats["total_links"] >= 10

    # Test ego subgraph
    sub = populated_graph.find_subgraph("TARGET_CYPHER_9", depth=1)
    assert len(sub["nodes"]) > 1

    # Test candidate procedures discovery
    candidates = populated_graph.find_procedures_for_target("TARGET_CYPHER_9")
    assert len(candidates) > 0


def test_compliance_engine_validations(populated_graph):
    engine = ComplianceEngine(populated_graph)

    # 1. Valid authorization with Chief of Station (TS_SCI)
    req_valid = ValidateComplianceRequest(
        action_name="AuthorizeExtraction",
        procedure_id="PROC_TACTICAL_EXTRACTION",
        agent_role_id="COS_BERLIN",
        context={"in_hostile_sector": True, "is_daytime": False},
    )
    res_valid = engine.validate(req_valid)
    assert res_valid.compliant is True
    assert res_valid.roe_status == "PERMITTED"

    # 2. Clearance failure (CASE_OFFICER_ALPHA has SECRET, extraction requires TOP_SECRET)
    req_clearance_fail = ValidateComplianceRequest(
        action_name="AuthorizeExtraction",
        procedure_id="PROC_TACTICAL_EXTRACTION",
        agent_role_id="CASE_OFFICER_ALPHA",
        context={},
    )
    res_clearance_fail = engine.validate(req_clearance_fail)
    assert res_clearance_fail.compliant is False
    assert res_clearance_fail.roe_status == "BLOCKED_CLEARANCE"

    # 3. ROE Breach (Diplomatic compound prohibition)
    req_roe_breach = ValidateComplianceRequest(
        action_name="AuthorizeSurveillance",
        procedure_id="PROC_HUMINT_SURVEILLANCE",
        agent_role_id="COS_BERLIN",
        context={"in_diplomatic_compound": True},
    )
    res_roe = engine.validate(req_roe_breach)
    assert res_roe.compliant is False
    assert res_roe.roe_status == "PROHIBITED_LEGAL"


def test_decider_and_audit(populated_graph, tmp_path):
    vec = SovereignVectorStore(persist_directory=str(tmp_path / "chroma"))
    ledger = OperationalLedger(db_path=str(tmp_path / "audit.db"))
    decider = GothamDecisionEngine(populated_graph, vec, ledger)

    req = RecommendActionRequest(
        scenario="Target CYPHER_9 is under active hostile pursuit. Extraction requested.",
        target_id="TARGET_CYPHER_9",
        agent_role_id="COS_BERLIN",
    )
    res = decider.recommend_action(req, context={"in_hostile_sector": True})

    assert res.recommended_procedure_id in ["PROC_TACTICAL_EXTRACTION", "PROC_HUMINT_SURVEILLANCE"]
    assert len(res.course_of_action) > 0
    assert res.risk_assessment.risk_score > 0

    # Verify audit ledger
    history = ledger.get_recent_decisions(limit=5)
    assert len(history) == 1
    assert history[0]["target_id"] == "TARGET_CYPHER_9"


def test_fastapi_endpoints():
    client = TestClient(app)

    # 1. Dashboard
    r_dash = client.get("/")
    assert r_dash.status_code == 200
    assert "Sovereign Gotham" in r_dash.text

    # 2. Stats
    r_stats = client.get("/api/v1/ontology/stats")
    assert r_stats.status_code == 200
    assert "total_entities" in r_stats.json()

    # 3. Risk Evaluation
    risk_payload = {
        "scenario": "Hostile infiltration near communication center.",
        "target_id": "TARGET_SYNDICATE_ORION",
        "procedure_id": "PROC_CYBER_COUNTERMEASURE",
        "context": {"in_hostile_sector": True}
    }
    r_risk = client.post("/api/v1/decision/risk", json=risk_payload)
    assert r_risk.status_code == 200
    assert r_risk.json()["risk_level"] in ["LOW", "MODERATE", "HIGH", "EXTREME"]
