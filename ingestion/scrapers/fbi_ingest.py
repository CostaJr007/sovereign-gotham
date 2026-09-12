"""
Sovereign Gotham - FBI Vault & FBI Wanted API Ingestion Module
Crawls declassified files from vault.fbi.gov and consumes official FBI Wanted REST API.
"""

from __future__ import annotations

import logging
import time

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from ontology.models import Target_Entity, TargetType, ThreatLevel

logger = logging.getLogger("SovereignGotham.FBI")


class FBIDocumentMetadata(BaseModel):
    """Metadata for a declassified file in the FBI Vault."""
    title: str
    category: str
    portal_url: str
    pdf_parts: list[str] = Field(default_factory=list)


class FBIVaultScraper:
    """
    Scrapes declassified document directories and PDFs from vault.fbi.gov.
    Includes courteous rate limiting and user-agent identification.
    """

    BASE_URL = "https://vault.fbi.gov"
    KNOWN_CATEGORIES = [
        "counterintelligence",
        "espionage",
        "foreign-counterintelligence",
        "gangs-extremist-groups",
        "unexplained-phenomenon-ufo",
        "famous-people",
    ]

    def __init__(self, rate_limit_sec: float = 1.0):
        self.rate_limit_sec = rate_limit_sec
        self.headers = {"User-Agent": "SovereignGotham-IntelligencePlatform/1.0"}

    def harvest_category_documents(
        self,
        category: str = "counterintelligence",
        max_docs: int = 5,
        timeout: float = 15.0,
    ) -> list[FBIDocumentMetadata]:
        """
        Crawls a specific category in the FBI Vault and extracts document records with PDF download links.
        """
        target_url = f"{self.BASE_URL}/{category}"
        records: list[FBIDocumentMetadata] = []

        try:
            with httpx.Client(headers=self.headers, timeout=timeout, follow_redirects=True) as client:
                resp = client.get(target_url)
                if resp.status_code != 200:
                    logger.warning(f"FBI Vault category {category} returned HTTP {resp.status_code}")
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.select("table.listing a, div.documentByLine a, ul.searchResults a")

                for a_tag in links[:max_docs]:
                    title = a_tag.get_text(strip=True)
                    href = a_tag.get("href", "")
                    if not href or "section-" in href:
                        continue

                    full_url = href if href.startswith("http") else f"{self.BASE_URL}/{href.lstrip('/')}"

                    time.sleep(self.rate_limit_sec)
                    pdf_urls = self._extract_pdf_download_links(client, full_url)

                    records.append(
                        FBIDocumentMetadata(
                            title=title or "Untitled FBI Document",
                            category=category,
                            portal_url=full_url,
                            pdf_parts=pdf_urls,
                        )
                    )

            return records
        except Exception as e:
            logger.error(f"Error harvesting FBI Vault category {category}: {e}")
            return []

    def _extract_pdf_download_links(self, client: httpx.Client, doc_page_url: str) -> list[str]:
        """Extracts direct PDF download endpoints (at_download/file) from a document page."""
        try:
            resp = client.get(doc_page_url)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            pdf_urls: list[str] = []
            for a in soup.select("a[href*='at_download/file'], a[href$='.pdf']"):
                href = a.get("href", "")
                if href:
                    full_pdf = href if href.startswith("http") else f"{self.BASE_URL}/{href.lstrip('/')}"
                    pdf_urls.append(full_pdf)
            return pdf_urls
        except Exception:
            return []


class FBIWantedAPIClient:
    """
    Harvests target personas and threat vectors from the official FBI Wanted REST API.
    Endpoint: https://api.fbi.gov/wanted/v1/list
    """

    API_ENDPOINT = "https://api.fbi.gov/wanted/v1/list"

    @classmethod
    def fetch_targets(cls, page: int = 1, timeout: float = 12.0) -> list[Target_Entity]:
        """
        Fetches official wanted/threat profiles from FBI API and converts them
        into canonical Sovereign Gotham Target_Entity objects.
        """
        targets: list[Target_Entity] = []

        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                resp = client.get(cls.API_ENDPOINT, params={"page": page})
                if resp.status_code != 200:
                    logger.warning(f"FBI Wanted API returned HTTP {resp.status_code}")
                    return []

                data = resp.json()
                items = data.get("items", [])

                for item in items:
                    uid = item.get("uid") or f"FBI-{item.get('id', 'UNK')}"
                    title = item.get("title") or "UNKNOWN SUBJECT"
                    aliases = item.get("aliases") or []
                    description = item.get("description") or item.get("warning_message") or ""
                    subjects = item.get("subjects") or []

                    # Determine threat level based on warning text
                    desc_upper = description.upper()
                    if "ARMED AND DANGEROUS" in desc_upper or "TERROR" in desc_upper:
                        threat = ThreatLevel.CRITICAL
                    elif "ESCAPED" in desc_upper or "CYBER" in desc_upper:
                        threat = ThreatLevel.HIGH
                    else:
                        threat = ThreatLevel.MEDIUM

                    target = Target_Entity(
                        id=f"TARGET-FBI-{uid}",
                        name=title,
                        type=TargetType.INDIVIDUAL,
                        threat_level=threat,
                        affiliations=subjects,
                        location=item.get("place_of_birth") or item.get("nationality"),
                        metadata={
                            "aliases": aliases,
                            "fbi_url": item.get("url"),
                            "reward_text": item.get("reward_text"),
                            "scars_and_marks": item.get("scars_and_marks"),
                            "source": "FBI_WANTED_API",
                        },
                    )
                    targets.append(target)

            return targets
        except Exception as e:
            logger.error(f"Error calling FBI Wanted API: {e}")
            return []
