"""
Sovereign Gotham - Multi-Agency Sovereign Intelligence Harvester
Harvests declassified intelligence text collections across agencies:
  - CIA: CIA CREST Collection (930,000+ records)
  - NSA: NSA Cryptolog Journal & Cryptologic History Series (SIGINT/Cyber/TEMPEST)
  - DoD / Joint Forces: Declassified Military Doctrines & Field Manuals
Saves clean OCR text to Drive D: with cryptographic SHA-256 custody hashes.
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger("SovereignGotham.MultiAgencyHarvester")


class MultiAgencyHarvestedRecord(BaseModel):
    """Normalized declassified intelligence record tagged by agency domain."""
    doc_id: str
    agency: str = Field(..., description="CIA, NSA, FBI, or DOD")
    title: str
    date: str | None = None
    raw_content: str
    sha256_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MultiAgencyIntelligenceHarvester:
    """
    High-throughput concurrent harvester connecting to official declassified
    intelligence collections on the Internet Archive for CIA, NSA, and DoD.
    """

    SEARCH_API = "https://archive.org/advancedsearch.php"
    DOWNLOAD_BASE = "https://archive.org/download"

    AGENCY_QUERIES = {
        "CIA": "identifier:(CIA-RDP*)",
        "NSA": "collection:nsacryptolog",
        "DOD": "collection:nationalsecurityarchive AND title:(military OR defense OR nuclear)",
        "ARMY": "title:(Field Manual Army) AND mediatype:(texts)",
        "NAVY": "title:(Naval OR Navy) AND mediatype:(texts)",
        "FBI": "subject:(FBI) AND mediatype:(texts)",
    }

    def __init__(self, output_dir: str | Path | None = None):
        if output_dir is None:
            self.output_dir = Path("D:/sovereign_gotham_data") if Path("D:/").exists() else Path("./data/sovereign_gotham_data")
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {"User-Agent": "SovereignGotham-DefenseResearch/2.0"}

    def harvest_agency(
        self,
        agency: str = "NSA",
        count: int = 20,
        page: int = 1,
        max_workers: int = 16,
    ) -> list[MultiAgencyHarvestedRecord]:
        """Harvests records specifically for a designated intelligence agency."""
        agency_upper = agency.upper()
        query = self.AGENCY_QUERIES.get(agency_upper, self.AGENCY_QUERIES["CIA"])
        agency_dir = self.output_dir / agency_upper.lower()
        agency_dir.mkdir(parents=True, exist_ok=True)

        params = {
            "q": query,
            "fl[]": ["identifier", "title", "date", "year"],
            "rows": max(count * 2, 40),
            "page": page,
            "output": "json",
        }

        try:
            with httpx.Client(timeout=20.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(self.SEARCH_API, params=params)
                if resp.status_code != 200:
                    logger.warning(f"Archive search failed for {agency}: HTTP {resp.status_code}")
                    return []
                items = resp.json().get("response", {}).get("docs", [])
        except Exception as e:
            logger.error(f"Search failed for {agency}: {e}")
            return []

        harvested: list[MultiAgencyHarvestedRecord] = []
        shared_client = httpx.Client(timeout=30.0, headers=self.headers, follow_redirects=True)

        def _fetch_record(item: dict[str, Any]) -> MultiAgencyHarvestedRecord | None:
            ident = item.get("identifier")
            if not ident:
                return None

            title = item.get("title") or ident
            doc_date = str(item.get("date") or item.get("year") or "1980-01-01")[:10]
            ocr_url = f"{self.DOWNLOAD_BASE}/{ident}/{ident}_djvu.txt"

            try:
                ocr_resp = shared_client.get(ocr_url)
                if ocr_resp.status_code != 200:
                    return None

                text = ocr_resp.text.strip()
                if len(text) < 300:
                    return None

                sha256_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                local_file = agency_dir / f"{ident}.txt"
                local_file.write_text(text, encoding="utf-8")

                rec = MultiAgencyHarvestedRecord(
                    doc_id=ident,
                    agency=agency_upper,
                    title=title,
                    date=doc_date,
                    raw_content=text,
                    sha256_hash=sha256_hash,
                    metadata={
                        "chars": len(text),
                        "source_url": ocr_url,
                        "agency": agency_upper,
                        "local_path": str(local_file),
                    },
                )
                logger.info(f"[{agency_upper}] Harvested: {ident} - {title[:35]} ({len(text)} chars)")
                return rec
            except Exception as e:
                logger.error(f"Failed to fetch {ident}: {e}")
                return None

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_fetch_record, it) for it in items]
                for f in as_completed(futures):
                    res = f.result()
                    if res is not None:
                        harvested.append(res)
                        if len(harvested) >= count:
                            break
        finally:
            shared_client.close()

        return harvested

    def harvest_all_agencies(
        self,
        cia_count: int = 50,
        nsa_count: int = 25,
        dod_count: int = 25,
    ) -> dict[str, list[MultiAgencyHarvestedRecord]]:
        """Harvests a balanced multi-agency intelligence corpus."""
        results = {}
        if cia_count > 0:
            results["CIA"] = self.harvest_agency("CIA", count=cia_count)
        if nsa_count > 0:
            results["NSA"] = self.harvest_agency("NSA", count=nsa_count)
        if dod_count > 0:
            results["DOD"] = self.harvest_agency("DOD", count=dod_count)
        return results
