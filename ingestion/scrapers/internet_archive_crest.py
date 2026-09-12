"""
Sovereign Gotham - Internet Archive CIA CREST Batch Harvester
Connects to the official CIA Collection on Internet Archive (930,000+ declassified documents).
Harvests documents with pre-extracted ABBYY OCR text and original metadata via open HTTP.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    _project_root = str(Path(__file__).resolve().parent.parent.parent)
except NameError:
    _project_root = str(Path(".").resolve())

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import hashlib
import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

from ontology.models import SecurityClassification

logger = logging.getLogger("SovereignGotham.IACrest")


class HarvestedCIADocument(BaseModel):
    """Normalized declassified document harvested from the CIA collection."""
    doc_id: str
    title: str
    date: str | None = None
    raw_content: str
    sha256_hash: str
    archive_url: str
    pdf_url: str
    ocr_url: str
    classification: SecurityClassification = SecurityClassification.DECLASSIFIED
    metadata: dict[str, Any] = Field(default_factory=dict)


class InternetArchiveCIABatchHarvester:
    """
    Harvests batches of real declassified CIA documents from Internet Archive.
    Zero API keys, 100% open, with clean pre-extracted OCR text.
    """

    SEARCH_API = "https://archive.org/advancedsearch.php"
    DOWNLOAD_BASE = "https://archive.org/download"

    def __init__(self, output_dir: str | Path | None = None):
        if output_dir is None:
            self.output_dir = Path("D:/sovereign_gotham_data/crest_batch") if Path("D:/").exists() else Path("sample_data/crest_harvested")
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {"User-Agent": "SovereignGotham-IntelligenceResearch/2.0"}

    def search_cia_collection(
        self,
        query: str = "identifier:(CIA-RDP*)",
        rows: int = 10,
        page: int = 1,
        timeout: float = 15.0,
    ) -> list[dict[str, Any]]:
        """Searches the Internet Archive CIA collection for declassified records."""
        params = {
            "q": query,
            "fl[]": ["identifier", "title", "date", "year", "description"],
            "rows": rows,
            "page": page,
            "output": "json",
        }

        try:
            with httpx.Client(timeout=timeout, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(self.SEARCH_API, params=params)
                if resp.status_code != 200:
                    logger.warning(f"Archive.org search returned HTTP {resp.status_code}")
                    return []

                data = resp.json()
                return data.get("response", {}).get("docs", [])
        except Exception as e:
            logger.error(f"Error searching Internet Archive: {e}")
            return []

    def harvest_batch(
        self,
        count: int = 50,
        query: str = "identifier:(CIA-RDP*)",
        page: int = 1,
        download_pdfs: bool = False,
        max_workers: int = 16,
    ) -> list[HarvestedCIADocument]:
        """
        Downloads a batch of declassified CIA documents concurrently across multiple pages,
        saving clean OCR text to disk. Continues until `count` documents are harvested.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        harvested: list[HarvestedCIADocument] = []
        page_idx = page
        shared_client = httpx.Client(
            timeout=30.0,
            headers=self.headers,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=32, max_connections=64),
        )

        def _fetch_single_doc(item: dict[str, Any]) -> HarvestedCIADocument | None:
            ident = item.get("identifier")
            if not ident:
                return None

            title = item.get("title") or ident
            doc_date = item.get("date") or item.get("year") or "1975-01-01"

            ocr_url = f"{self.DOWNLOAD_BASE}/{ident}/{ident}_djvu.txt"
            pdf_url = f"{self.DOWNLOAD_BASE}/{ident}/{ident}.pdf"

            try:
                ocr_resp = shared_client.get(ocr_url)
                if ocr_resp.status_code != 200:
                    return None

                text_content = ocr_resp.text.strip()
                if not text_content:
                    return None

                sha256_hash = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
                local_text_file = self.output_dir / f"{ident}.txt"
                local_text_file.write_text(text_content, encoding="utf-8")

                if download_pdfs:
                    pdf_resp = shared_client.get(pdf_url)
                    if pdf_resp.status_code == 200:
                        local_pdf = self.output_dir / f"{ident}.pdf"
                        local_pdf.write_bytes(pdf_resp.content)

                orig_marking = "UNCLASSIFIED"
                text_upper = text_content.upper()
                if "TOP SECRET" in text_upper:
                    orig_marking = "HISTORIC_TOP_SECRET"
                elif "SECRET" in text_upper:
                    orig_marking = "HISTORIC_SECRET"
                elif "CONFIDENTIAL" in text_upper:
                    orig_marking = "HISTORIC_CONFIDENTIAL"

                record = HarvestedCIADocument(
                    doc_id=ident,
                    title=title,
                    date=str(doc_date)[:10],
                    raw_content=text_content,
                    sha256_hash=sha256_hash,
                    archive_url=f"https://archive.org/details/{ident}",
                    pdf_url=pdf_url,
                    ocr_url=ocr_url,
                    classification=SecurityClassification.DECLASSIFIED,
                    metadata={
                        "local_path": str(local_text_file),
                        "bytes": len(text_content),
                        "historic_marking": orig_marking,
                        "source": "CIA_CREST_ARCHIVE_ORG",
                    },
                )
                logger.info(f"Harvested: {ident} - {title[:40]} ({len(text_content)} chars)")
                return record
            except Exception as e:
                logger.error(f"Error harvesting document {ident}: {e}")
                return None

        try:
            while len(harvested) < count and page_idx < 100:
                needed = count - len(harvested)
                fetch_rows = min(max(needed * 2, 50), 500)
                docs_metadata = self.search_cia_collection(query=query, rows=fetch_rows, page=page_idx)
                if not docs_metadata:
                    break

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_doc = {executor.submit(_fetch_single_doc, item): item for item in docs_metadata}
                    for future in as_completed(future_to_doc):
                        res = future.result()
                        if res is not None:
                            harvested.append(res)
                            if len(harvested) >= count:
                                break

                page_idx += 1
        finally:
            shared_client.close()

        return harvested
