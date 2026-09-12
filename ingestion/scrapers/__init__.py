"""
Sovereign Gotham - Intelligence Scrapers & Connectors Package
"""

from .cia_ingest import CIACrestConnector, DeclassifiedRecord
from .dod_nsa_ingest import (
    DoDDoctrineConnector,
    NSADeclassifiedScraper,
    NSARecordMetadata,
)
from .fbi_ingest import FBIDocumentMetadata, FBIVaultScraper, FBIWantedAPIClient
from .internet_archive_crest import (
    HarvestedCIADocument,
    InternetArchiveCIABatchHarvester,
)

__all__ = [
    "CIACrestConnector",
    "DeclassifiedRecord",
    "DoDDoctrineConnector",
    "FBIDocumentMetadata",
    "FBIVaultScraper",
    "FBIWantedAPIClient",
    "HarvestedCIADocument",
    "InternetArchiveCIABatchHarvester",
    "NSADeclassifiedScraper",
    "NSARecordMetadata",
]
