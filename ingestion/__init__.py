"""
Sovereign Gotham Ingestion Package
"""
from .document_loader import DeclassifiedDocumentLoader
from .entity_extractor import OntologicalEntityExtractor

__all__ = ["DeclassifiedDocumentLoader", "OntologicalEntityExtractor"]
