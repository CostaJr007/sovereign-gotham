"""
Sovereign Gotham - FastAPI Application Entry Point
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from api.routes import graph, ledger, router, vector_store
from ingestion.document_loader import DeclassifiedDocumentLoader
from ingestion.entity_extractor import OntologicalEntityExtractor


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: If graph is empty, seed with sample CIA CREST intelligence report
    sample_pdf = Path(__file__).parent.parent / "sample_data" / "cia_crest_sanitized_report.pdf"
    if sample_pdf.exists() and len(graph.entities) == 0:
        print(f"[Gotham Engine] Pre-seeding Sovereign Ontology with: {sample_pdf.name}")
        try:
            payload = DeclassifiedDocumentLoader.load_file(sample_pdf)
            entities, links = OntologicalEntityExtractor.extract_from_document_payload(payload)
            for e in entities:
                graph.add_object(e)
            for l in links:
                graph.add_link(l)
            vector_store.add_texts(
                texts=[payload["raw_content"]],
                metadatas=[{"source": payload["source"], "id": payload["id"]}],
                ids=[payload["id"]],
            )
            ledger.record_ingestion(
                document_id=payload["id"],
                source=payload["source"],
                provenance_hash=payload["provenance_hash"],
                classification=str(payload["classification_original"]),
                entities_count=len(entities),
                links_count=len(links),
            )
            print(f"[Gotham Engine] Loaded {len(entities)} entities & {len(links)} links.")
        except Exception as ex:
            print(f"[Gotham Engine Warning] Pre-seeding failed: {ex}")
    yield


app = FastAPI(
    title="Sovereign Gotham - Ontological Decision Engine",
    description="Operational Intelligence Operating System inspired by Palantir Gotham, powered by declassified CIA CREST/DoD records.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", response_class=HTMLResponse, summary="Operational Status Dashboard")
def dashboard():
    stats = graph.get_stats()
    entities_html = "".join([f"<li><b>{k}</b>: {v}</li>" for k, v in stats.get("entities_by_type", {}).items()])
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sovereign Gotham // Operational Intelligence Center</title>
        <style>
            body {{ font-family: 'Consolas', 'Segoe UI', monospace; background-color: #0b0f19; color: #00ff66; padding: 30px; }}
            .container {{ max-width: 900px; margin: auto; border: 1px solid #1f3a5f; padding: 25px; border-radius: 8px; background: #111827; box-shadow: 0 0 20px rgba(0, 255, 102, 0.1); }}
            h1 {{ color: #ffffff; border-bottom: 2px solid #00ff66; padding-bottom: 10px; font-size: 24px; }}
            .metric {{ display: inline-block; background: #1e293b; padding: 15px 25px; border-radius: 5px; margin: 10px; border-left: 4px solid #00ff66; }}
            .metric-val {{ font-size: 28px; font-weight: bold; color: #ffffff; }}
            .metric-lbl {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; }}
            a {{ color: #38bdf8; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            ul {{ list-style-type: square; color: #e2e8f0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Sovereign Gotham // Decision Engine</h1>
            <p>Air-gapped Operational Intelligence & Ontological Causal Reasoning System</p>
            <div>
                <div class="metric">
                    <div class="metric-val">{stats.get('total_entities', 0)}</div>
                    <div class="metric-lbl">Total Entities</div>
                </div>
                <div class="metric">
                    <div class="metric-val">{stats.get('total_links', 0)}</div>
                    <div class="metric-lbl">Typed Links</div>
                </div>
                <div class="metric">
                    <div class="metric-val">{stats.get('density', 0.0):.3f}</div>
                    <div class="metric-lbl">Graph Density</div>
                </div>
            </div>
            <h3>Ontological Distribution:</h3>
            <ul>{entities_html or '<li>No entities indexed yet.</li>'}</ul>
            <hr style="border: 0; border-top: 1px solid #1f3a5f; margin: 20px 0;">
            <p>Access the interactive Swagger API documentation at: <a href="/docs">/docs</a></p>
        </div>
    </body>
    </html>
    """
