"""
Sovereign Gotham - CIA CREST & HistoryLab Ingestion Module
Supports streaming millions of declassified documents from Hugging Face FOIArchive
as well as targeted direct queries against CIA FOIA Electronic Reading Room.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from ontology.models import SecurityClassification

logger = logging.getLogger("SovereignGotham.CIA")


class DeclassifiedRecord(BaseModel):
    """Normalized declassified intelligence record."""
    doc_id: str
    title: str
    source: str = "CIA"
    authored_date: str | None = None
    classification: SecurityClassification = SecurityClassification.DECLASSIFIED
    body: str
    summary: str = ""
    page_count: int = 1
    provenance_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CIACrestConnector:
    """
    Connects to open datasets and CIA CREST endpoints.
    - Direct CIA FOIA Reading Room search
    - Streaming from Columbia University HistoryLab (foiarchive)
    """

    CREST_SEARCH_URL = "https://www.cia.gov/readingroom/search/site"
    HUGGINGFACE_STREAM_URL = "https://datasets-server.huggingface.co/rows?dataset=HistoryLab%2Ffoiarchive&config=default&split=train"

    def __init__(self, user_agent: str = "SovereignGotham-IntelligenceEngine/1.0 (AirGapped-Research)"):
        self.headers = {"User-Agent": user_agent}

    def search_reading_room(self, keyword: str, page: int = 0, timeout: float = 12.0) -> list[dict[str, Any]]:
        """
        Executes a targeted search against the CIA FOIA Electronic Reading Room.
        Returns a list of search result hits with document URLs.
        """
        url = f"{self.CREST_SEARCH_URL}/{keyword}"
        params = {"page": page}

        try:
            with httpx.Client(timeout=timeout, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url, params=params)
                if resp.status_code != 200:
                    logger.warning(f"CIA CREST search returned HTTP {resp.status_code}")
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                results: list[dict[str, Any]] = []

                # Parse search listing items
                for item in soup.select("ol.search-results li, div.views-row"):
                    title_elem = item.select_one("h3 a, a")
                    snippet_elem = item.select_one("div.search-snippet-info, div.views-field-body")
                    if title_elem and title_elem.get_text(strip=True):
                        href = title_elem.get("href", "")
                        full_url = href if href.startswith("http") else f"https://www.cia.gov{href}"
                        results.append({
                            "title": title_elem.get_text(strip=True),
                            "url": full_url,
                            "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                        })

                return results
        except Exception as e:
            logger.error(f"Error connecting to CIA CREST: {e}")
            return []

    def stream_historylab_archive(
        self,
        max_records: int = 50,
        offset: int = 0,
        timeout: float = 20.0,
    ) -> Generator[DeclassifiedRecord, None, None]:
        """
        Streams pre-cleaned declassified documents from Columbia University's HistoryLab FOIArchive.
        Includes CIA CREST, PDBs, and diplomatic communications.
        """
        limit_per_batch = min(max_records, 50)
        yielded = 0
        current_offset = offset

        try:
            with httpx.Client(timeout=timeout, headers=self.headers) as client:
                while yielded < max_records:
                    fetch_len = min(limit_per_batch, max_records - yielded)
                    api_url = f"{self.HUGGINGFACE_STREAM_URL}&offset={current_offset}&length={fetch_len}"
                    resp = client.get(api_url)

                    if resp.status_code != 200:
                        logger.warning(f"HistoryLab dataset API returned HTTP {resp.status_code}")
                        break

                    data = resp.json()
                    rows = data.get("rows", [])
                    if not rows:
                        break

                    for item in rows:
                        row = item.get("row", {})
                        body_text = row.get("body") or ""
                        doc_id = str(row.get("doc_id") or f"HL-DOC-{current_offset}")

                        # Map classification string to SecurityClassification enum
                        raw_class = str(row.get("classification") or "DECLASSIFIED").upper()
                        classification = SecurityClassification.DECLASSIFIED
                        if "TOP" in raw_class:
                            classification = SecurityClassification.TOP_SECRET
                        elif "SECRET" in raw_class:
                            classification = SecurityClassification.SECRET
                        elif "CONFIDENTIAL" in raw_class:
                            classification = SecurityClassification.CONFIDENTIAL
                        elif "UNCLASSIFIED" in raw_class:
                            classification = SecurityClassification.UNCLASSIFIED

                        record = DeclassifiedRecord(
                            doc_id=doc_id,
                            title=row.get("title") or "Untitled CIA Document",
                            source=row.get("source") or "CIA-CREST",
                            authored_date=row.get("authored"),
                            classification=classification,
                            body=body_text,
                            summary=body_text[:300] + "..." if len(body_text) > 300 else body_text,
                            page_count=int(row.get("pg_cnt") or 1),
                            metadata={
                                "char_cnt": row.get("char_cnt"),
                                "word_cnt": row.get("word_cnt"),
                            },
                        )

                        yield record
                        yielded += 1
                        if yielded >= max_records:
                            break

                    current_offset += len(rows)
        except Exception as e:
            logger.error(f"Error streaming from HistoryLab: {e}")
            return
