"""
Sovereign Gotham - Interactive Tactical Command Line Interface (CLI)
Provides operators with air-gapped scenario evaluation, ontological intelligence auditing,
fluent Sovereign OSDK queries, and automated training dataset synthesis for SLMs.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from agents.compliance import ComplianceEngine
from agents.decider import GothamDecisionEngine
from ingestion.document_loader import DeclassifiedDocumentLoader
from ingestion.entity_extractor import OntologicalEntityExtractor
from ingestion.scrapers.dod_nsa_ingest import DoDDoctrineConnector
from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    Document,
    LinkType,
    Operation,
    Procedure,
    RecommendActionRequest,
)
from ontology.osdk_client import SovereignOSDKClient
from storage.sqlite_store import OperationalLedger
from storage.vector_store import SovereignVectorStore
from training.dataset_generator import OntologicalDatasetGenerator

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

console = Console(force_terminal=True, legacy_windows=False)


def banner():
    console.print(
        Panel(
            """[bold red]========================================================================[/bold red]
[bold red]        P A L A N T I R   G O T H A M   //   O N T O L O G Y           [/bold red]
[bold white]                  SOVEREIGN DECISION ENGINE                            [/bold white]
[bold red]========================================================================[/bold red]
[cyan]Air-Gapped Ontological Operational Intelligence & Doctrinal Decision Core[/cyan]
[dim]Powered by Declassified CIA CREST, FBI, NSA & DoD Operational Records[/dim]""",
            border_style="red",
        )
    )


def initialize_engine():
    graph = GothamKnowledgeGraph()
    vec = SovereignVectorStore(persist_directory="storage/chroma_db")
    ledger = OperationalLedger(db_path="storage/gotham_audit.db")
    decider = GothamDecisionEngine(graph, vec, ledger)
    compliance = ComplianceEngine(graph)

    # 1. Seed standard DoD Military Doctrines (JP 2-0, JP 3-60, FM 2-0)
    for proc in DoDDoctrineConnector.list_all_procedures():
        graph.add_object(proc)

    # 2. Auto seed default CREST document if available
    sample = Path(__file__).parent / "sample_data" / "cia_crest_sanitized_report.pdf"
    if sample.exists():
        payload = DeclassifiedDocumentLoader.load_file(sample)
        entities, links = OntologicalEntityExtractor.extract_from_document_payload(payload)
        for e in entities:
            graph.add_object(e)
        for l in links:
            graph.add_link(l)
        vec.add_texts(
            texts=[payload["raw_content"]],
            metadatas=[{"source": payload["source"], "id": payload["id"]}],
            ids=[payload["id"]],
        )

    return graph, vec, ledger, decider, compliance


def show_graph_stats(graph: GothamKnowledgeGraph):
    stats = graph.get_stats()
    table = Table(title="[bold green]Ontological Graph Topology[/bold green]")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold white")

    table.add_row("Total Entities (Objects)", str(stats["total_entities"]))
    table.add_row("Total Semantic Links", str(stats["total_links"]))
    table.add_row("Network Density", f"{stats['density']:.4f}")

    for k, v in stats.get("entities_by_type", {}).items():
        table.add_row(f"  * Entity [{k}]", str(v))

    console.print(table)


def run_osdk_queries(graph: GothamKnowledgeGraph):
    """Demonstrates Palantir-style fluent queries using SovereignOSDKClient."""
    console.print("\n[bold yellow][*] RUNNING SOVEREIGN OSDK FLUENT QUERIES...[/bold yellow]\n")
    client = SovereignOSDKClient(graph)

    # Query 1: Filter Documents
    docs = client.objects(Document).where(source="CIA").fetch()
    console.print(f"[bold cyan]1. client.objects(Document).where(source='CIA').count():[/bold cyan] [white]{len(docs)}[/white]")
    for d in docs[:3]:
        console.print(f"   - [green]DOC ID:[/green] {d.id} | [dim]{d.title}[/dim] (Hash: {d.provenance_hash[:12] if d.provenance_hash else 'N/A'}...)")

    # Query 2: Traverse Document -> Operation via pivot_to
    ops = (
        client.objects(Document)
        .where(source="CIA")
        .pivot_to(LinkType.REGISTERS, Operation)
        .fetch()
    )
    console.print(f"\n[bold cyan]2. Document.pivot_to(LinkType.REGISTERS, Operation):[/bold cyan] [white]{len(ops)}[/white] linked operations found")
    for op in ops:
        console.print(f"   - [green]OP CODENAME:[/green] [bold white]{op.codename}[/bold white] | Status: {op.status} | Objective: [dim]{op.objective[:60]}...[/dim]")

    # Query 3: List Military Doctrines
    doctrines = client.objects(Procedure).where(lambda p: "DOCTRINE" in p.id).fetch()
    console.print(f"\n[bold cyan]3. Available Military Doctrines in Graph:[/bold cyan] [white]{len(doctrines)}[/white]")
    for doc in doctrines:
        console.print(f"   - [yellow]{doc.id}[/yellow]: {doc.name} (Clearance required: {doc.required_clearance})")


def run_dataset_generation(graph: GothamKnowledgeGraph, output_dir: str = "training_data"):
    """Synthesizes instruction datasets for the 4 domain-specific SLMs."""
    console.print("\n[bold yellow][*] SYNTHESIZING ONTOLOGICAL TRAINING DATASETS FOR SOVEREIGN SLMs...[/bold yellow]")
    console.print(f"[dim]Output Directory:[/dim] [cyan]{output_dir}[/cyan]\n")

    generator = OntologicalDatasetGenerator(graph)
    results = generator.generate_all(output_dir)

    table = Table(title="[bold green]Generated Sovereign SLM Datasets (ShareGPT / Unsloth Compatible)[/bold green]")
    table.add_column("Domain Specialist SLM", style="cyan")
    table.add_column("Output File", style="bold white")
    table.add_column("Sample Count", style="green")

    for domain, count in results.items():
        table.add_row(
            domain.replace("_", " ").upper(),
            f"{output_dir}/{domain}.jsonl",
            str(count),
        )

    console.print(table)
    console.print("\n[bold green][✓] Datasets ready for local fine-tuning via Unsloth/QLoRA on local GPU.[/bold green]\n")


def run_simulation(
    decider: GothamDecisionEngine,
    graph: GothamKnowledgeGraph,
    target_id: str,
    role_id: str,
    scenario: str,
    roe_override: bool = False,
):
    console.print("\n[bold yellow][*] INITIATING GOTHAM DECISION CYCLE...[/bold yellow]")
    console.print(f"[dim]Scenario:[/dim] {scenario}")
    console.print(f"[dim]Target Subject:[/dim] {target_id} | [dim]Authority Role:[/dim] {role_id}\n")

    context = {
        "in_hostile_sector": True,
        "is_daytime": False,
        "in_diplomatic_compound": roe_override,
    }

    req = RecommendActionRequest(
        scenario=scenario,
        target_id=target_id,
        agent_role_id=role_id,
    )

    res = decider.recommend_action(req, context=context)

    # 1. Decision Header
    status_style = "bold green" if res.compliance_validation.compliant else "bold red"
    console.print(
        Panel(
            f"[bold white]RECOMMENDED PROCEDURE:[/bold white] [cyan]{res.procedure_name}[/cyan] ({res.recommended_procedure_id})\n"
            f"[bold white]COMPLIANCE ROE STATUS:[/bold white] [{status_style}]{res.compliance_validation.roe_status}[/{status_style}] | "
            f"[bold white]RISK LEVEL:[/bold white] [yellow]{res.risk_assessment.risk_level.value}[/yellow] (Score: {res.risk_assessment.risk_score}/100)",
            title="[bold]COA SYNTHESIS[/bold]",
            border_style="cyan",
        )
    )

    # 2. ROE & Compliance Violations
    if res.compliance_validation.violations:
        viol_tree = Tree("[bold red][!] DOCTRINAL & ROE VIOLATIONS DETECTED:[/bold red]")
        for v in res.compliance_validation.violations:
            viol_tree.add(f"[red]{v}[/red]")
        console.print(viol_tree)
        console.print()

    # 3. Course of Action Steps
    coa_table = Table(title="[bold cyan]Standard Operating Procedure Directives[/bold cyan]")
    coa_table.add_column("Step", style="bold white", width=6)
    coa_table.add_column("Tactical Directive", style="green")
    coa_table.add_column("Doctrine Constraint / Precaution", style="yellow")

    for coa in res.course_of_action:
        coa_table.add_row(str(coa.step_number), coa.directive, coa.precaution)

    console.print(coa_table)

    # 4. Ontological Evidence Links
    link_table = Table(title="[bold magenta]Graph Causal Evidence Chain[/bold magenta]")
    link_table.add_column("Source", style="cyan")
    link_table.add_column("Relationship", style="bold white")
    link_table.add_column("Target", style="cyan")
    link_table.add_column("Intelligence Notes", style="dim")

    for link in res.evidence_chain:
        link_table.add_row(link.source_id, f"-[:{link.link_type}]->", link.target_id, link.notes or "")

    console.print(link_table)

    # 5. Doctrinal Rationale
    console.print(
        Panel(
            f"[white]{res.rationale}[/white]",
            title="[bold green]Sovereign Cognitive Rationale[/bold green]",
            border_style="green",
        )
    )


def run_batch_harvest(
    graph: GothamKnowledgeGraph,
    vec: SovereignVectorStore,
    count: int = 5,
    out_dir: str = "sample_data/crest_harvested",
):
    from ingestion.scrapers.internet_archive_crest import (
        InternetArchiveCIABatchHarvester,
    )
    console.print("\n[bold yellow][*] INITIATING BATCH HARVEST OF CIA CREST DECLASSIFIED ARCHIVES...[/bold yellow]")
    console.print(f"[dim]Batch Size:[/dim] [cyan]{count}[/cyan] | [dim]Destination:[/dim] [cyan]{out_dir}[/cyan]\n")

    harvester = InternetArchiveCIABatchHarvester(output_dir=out_dir)
    docs = harvester.harvest_batch(count=count)

    table = Table(title="[bold green]Harvested CIA CREST Declassified Records[/bold green]")
    table.add_column("Doc ID", style="cyan")
    table.add_column("Title", style="bold white")
    table.add_column("Historic Marking", style="yellow")
    table.add_column("Chars", style="green")
    table.add_column("SHA-256 Custody Hash", style="dim")

    for d in docs:
        table.add_row(
            d.doc_id,
            d.title[:45],
            d.metadata.get("historic_marking", "DECLASSIFIED"),
            str(len(d.raw_content)),
            f"{d.sha256_hash[:12]}...",
        )
        doc_obj = Document(
            id=d.doc_id,
            source="CIA_CREST",
            title=d.title,
            document_date=d.date,
            classification_original=d.classification,
            summary=d.raw_content[:300] + "..." if len(d.raw_content) > 300 else d.raw_content,
            raw_content=d.raw_content,
            provenance_hash=d.sha256_hash,
            metadata=d.metadata,
        )
        graph.add_object(doc_obj)
        vec.add_texts(
            texts=[d.raw_content],
            metadatas=[{"source": "CIA_CREST", "id": d.doc_id, "title": d.title}],
            ids=[d.doc_id],
        )

    console.print(table)
    console.print(f"\n[bold green][✓] {len(docs)} documents successfully harvested, verified via SHA-256 and integrated into the Ontological Knowledge Graph.[/bold green]\n")


def run_agent_investigation(
    graph: GothamKnowledgeGraph,
    query_prompt: str,
    target_name: Optional[str] = None,
):
    from agents.sovereign_deepseek_agent import SovereignDeepSeekAgent
    console.print("\n[bold yellow][*] ENGAGING DEEPSEEK-R1 SOVEREIGN INTELLIGENCE ANALYST...[/bold yellow]")
    console.print(f"[dim]Instruction:[/dim] [cyan]{query_prompt}[/cyan]\n")

    agent = SovereignDeepSeekAgent(graph)
    result = agent.investigate(query_prompt, target_name=target_name)

    # 1. Thought Trace Panel
    console.print(Panel(
        f"[italic cyan]{result.thought_trace}[/italic cyan]",
        title="[bold yellow]🧠 DeepSeek-R1 Cognitive Reflection Chain (<thought>)[/bold yellow]",
        border_style="yellow",
    ))

    # 2. Structured Operational Decision
    import json
    console.print(Panel(
        f"[green]{json.dumps(result.decision, indent=2, ensure_ascii=False)}[/green]",
        title="[bold green]🎯 Validated Operational Directive[/bold green]",
        border_style="green",
    ))


if __name__ == "__main__":
    banner()
    graph, vec, ledger, decider, compliance = initialize_engine()

    arg = sys.argv[1] if len(sys.argv) > 1 else "default"

    if arg == "stats":
        show_graph_stats(graph)
    elif arg == "query-osdk":
        run_osdk_queries(graph)
    elif arg == "harvest-batch":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        out_dir = sys.argv[3] if len(sys.argv) > 3 else "sample_data/crest_harvested"
        run_batch_harvest(graph, vec, count=count, out_dir=out_dir)
    elif arg == "generate-datasets":
        out_dir = sys.argv[2] if len(sys.argv) > 2 else "training_data"
        run_dataset_generation(graph, out_dir)
    elif arg == "investigate":
        prompt = sys.argv[2] if len(sys.argv) > 2 else "Analyze threat actor movements in hostile sector."
        target = sys.argv[3] if len(sys.argv) > 3 else None
        run_agent_investigation(graph, prompt, target_name=target)
    elif arg == "test-violation":
        run_simulation(
            decider,
            graph,
            target_id="TARGET_CYPHER_9",
            role_id="CASE_OFFICER_ALPHA",
            scenario="Asset trapped inside foreign embassy in hostile capital. Attempt immediate kinetic breach.",
            roe_override=True,
        )
    else:
        show_graph_stats(graph)
        run_osdk_queries(graph)
        run_simulation(
            decider,
            graph,
            target_id="TARGET_CYPHER_9",
            role_id="COS_BERLIN",
            scenario="Hostile operatives closing in on Asset CYPHER_9 in Berlin sector 3. Immediate extraction required.",
            roe_override=False,
        )
