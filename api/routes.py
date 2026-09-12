"""
Sovereign Gotham - REST API Endpoints (FastAPI)
Exposes Ingestion, Knowledge Graph, Compliance Engine, and Gotham Decider.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from agents.compliance import ComplianceEngine
from agents.decider import GothamDecisionEngine
from ingestion.document_loader import DeclassifiedDocumentLoader
from ingestion.entity_extractor import OntologicalEntityExtractor
from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    EvaluateRiskRequest,
    EvaluateRiskResponse,
    RecommendActionRequest,
    RecommendActionResponse,
    ValidateComplianceRequest,
    ValidateComplianceResponse,
)
from storage.sqlite_store import OperationalLedger
from storage.vector_store import SovereignVectorStore

router = APIRouter(prefix="/api/v1")

# Global singleton state for API lifecycle
graph = GothamKnowledgeGraph()
vector_store = SovereignVectorStore(persist_directory="storage/chroma_db")
ledger = OperationalLedger(db_path="storage/gotham_audit.db")
decider = GothamDecisionEngine(graph, vector_store, ledger)
compliance_engine = ComplianceEngine(graph)


class DecisionContextWrapper(BaseModel):
    request: RecommendActionRequest
    context: dict[str, Any] = {}


@router.post("/ingest/file", summary="Ingest declassified document (PDF / TXT)")
async def ingest_document(file: UploadFile = File(...)):
    """
    Ingests and parses declassified report, extracts canonical entities and typed links,
    and updates the Sovereign Knowledge Graph and Vector Store.
    """
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        payload = DeclassifiedDocumentLoader.load_file(tmp_path)
        entities, links = OntologicalEntityExtractor.extract_from_document_payload(payload)

        # Update Knowledge Graph
        for entity in entities:
            graph.add_object(entity)
        for link in links:
            graph.add_link(link)

        # Index text in Vector Store
        vector_store.add_texts(
            texts=[payload["raw_content"]],
            metadatas=[{"source": payload["source"], "id": payload["id"], "classification": payload["classification_original"]}],
            ids=[payload["id"]],
        )

        # Audit Ledger
        ledger.record_ingestion(
            document_id=payload["id"],
            source=payload["source"],
            provenance_hash=payload["provenance_hash"],
            classification=str(payload["classification_original"]),
            entities_count=len(entities),
            links_count=len(links),
        )

        return {
            "status": "SUCCESS",
            "document_id": payload["id"],
            "title": payload["title"],
            "provenance_sha256": payload["provenance_hash"],
            "entities_extracted": len(entities),
            "links_created": len(links),
            "entities_summary": [f"{type(e).__name__}: {e.id}" for e in entities],
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/ontology/stats", summary="Knowledge Graph summary and density")
def get_ontology_stats():
    return graph.get_stats()


@router.get("/ontology/graph", summary="Export full Knowledge Graph or Subgraph")
def get_graph(center_id: str | None = None, depth: int = 2):
    if center_id:
        return graph.find_subgraph(entity_id=center_id, depth=depth)
    return graph.to_dict()


@router.get("/ontology/entity/{entity_id}", summary="Fetch specific entity details and links")
def get_entity_details(entity_id: str):
    obj = graph.get_object(entity_id)
    if not obj:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found in ontology.")

    subgraph = graph.find_subgraph(entity_id, depth=1)
    return {
        "entity": obj.model_dump(),
        "connected_links": subgraph["edges"],
        "connected_nodes": [n for n in subgraph["nodes"] if n["id"] != entity_id],
    }


@router.post("/decision/risk", response_model=EvaluateRiskResponse, summary="Evaluate tactical risk")
def evaluate_risk(request: EvaluateRiskRequest):
    return decider.evaluate_risk(request)


@router.post("/decision/compliance", response_model=ValidateComplianceResponse, summary="Validate action against ROE and doctrine")
def validate_compliance(request: ValidateComplianceRequest):
    return compliance_engine.validate(request)


@router.post("/decision/recommend", response_model=RecommendActionResponse, summary="Palantir Gotham Decider / OAG Course of Action")
def recommend_action(payload: DecisionContextWrapper):
    try:
        return decider.recommend_action(request=payload.request, context=payload.context)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/audit/decisions", summary="Get recent decision audit records")
def get_decision_audit(limit: int = 20):
    return ledger.get_recent_decisions(limit=limit)


@router.get("/audit/ingestions", summary="Get recent document ingestion records")
def get_ingestion_audit(limit: int = 20):
    return ledger.get_ingestion_history(limit=limit)
