"""
Sovereign Gotham - DoD Doctrine & NSA Declassified Ingestion Module
Connects to NSA Declassified Reading Room, JCS Joint Electronic Library, and FAS IRP.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

from ontology.models import ClearanceLevel, Procedure, ProcedureCategory

logger = logging.getLogger("SovereignGotham.DoD_NSA")


class NSARecordMetadata(BaseModel):
    title: str
    topic: str
    release_year: str | None = None
    pdf_url: str
    source: str = "NSA"


class NSADeclassifiedScraper:
    """
    Crawls historical declassified records from the NSA FOIA Declassified Reading Room.
    Topics include Venona, Cryptologic Spectrum, Gulf of Tonkin, and European Axis SIGINT.
    """

    BASE_URL = "https://www.nsa.gov/Helpful-Links/NSA-FOIA/Declassified-Records"

    TOPICS = [
        "venona-project",
        "cryptologic-history",
        "gulf-of-tonkin",
        "european-axis-sigint",
    ]

    def __init__(self):
        self.headers = {"User-Agent": "SovereignGotham-IntelligencePlatform/1.0"}

    def fetch_topic_records(self, topic: str = "venona-project", timeout: float = 15.0) -> list[NSARecordMetadata]:
        """Scrapes links to declassified intelligence PDFs for a specific topic."""
        url = f"{self.BASE_URL}/{topic}/"
        records: list[NSARecordMetadata] = []

        try:
            with httpx.Client(headers=self.headers, timeout=timeout, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"NSA declassified topic {topic} returned HTTP {resp.status_code}")
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.select("table a[href$='.pdf'], div.content a[href$='.pdf']"):
                    href = a.get("href", "")
                    title = a.get_text(strip=True) or "NSA Declassified Report"
                    if href:
                        pdf_url = href if href.startswith("http") else f"https://www.nsa.gov{href}"
                        records.append(
                            NSARecordMetadata(
                                title=title,
                                topic=topic,
                                pdf_url=pdf_url,
                            )
                        )
            return records
        except Exception as e:
            logger.error(f"Error fetching NSA records for {topic}: {e}")
            return []


class DoDDoctrineConnector:
    """
    Catalogs and structures Military Joint Doctrines (JCS) and Field Manuals (FM).
    Specifically:
      - JP 2-0 (Joint Intelligence)
      - JP 3-60 (Joint Targeting Cycle - D3A)
      - JP 3-0 (Joint Operations)
      - FM 2-0 (Intelligence Operations)
    """

    CORE_DOCTRINES: dict[str, dict[str, Any]] = {
        "JP-2-0": {
            "name": "Joint Intelligence (JP 2-0)",
            "category": ProcedureCategory.SURVEILLANCE,
            "required_clearance": ClearanceLevel.SECRET,
            "steps": [
                "Planning and Direction: Identify intelligence requirements and collection priorities",
                "Collection: Task organic and national assets (SIGINT, HUMINT, GEOINT, OSINT)",
                "Processing and Exploitation: Decrypt, translate, and convert raw data into usable information",
                "Analysis and Production: Integrate and synthesize multi-source intelligence into estimates",
                "Dissemination and Integration: Deliver intelligence to operational decision-makers",
                "Evaluation and Feedback: Assess effectiveness and calibrate subsequent taskings",
            ],
            "restrictions": [
                "Prohibition of domestic collection without statutory authorization (EO 12333)",
                "Strict protection of sources, methods, and cryptographic material",
            ],
            "roe_guidelines": "Intelligence operations must remain within combatant command boundaries and legal authorities.",
        },
        "JP-3-60": {
            "name": "Joint Targeting Cycle - D3A Framework (JP 3-60)",
            "category": ProcedureCategory.COVERT_ACTION,
            "required_clearance": ClearanceLevel.TOP_SECRET,
            "steps": [
                "Decide: Determine target priorities, desired effects, and weapon-target pairing",
                "Detect: Acquire target location with required precision (Sensor-to-Shooter)",
                "Deliver: Execute kinetic, cyber, or electronic tasking within RoE authorization",
                "Assess: Combat assessment and battle damage assessment (BDA) to verify effect",
            ],
            "restrictions": [
                "Prohibition of strikes exceeding authorized collateral damage thresholds (CDEM)",
                "Mandatory Positive Identification (PID) prior to engagement",
                "Prohibition of targeting cultural, religious, or non-combatant protected infrastructure",
            ],
            "roe_guidelines": "Zero engagement without verified Positive Identification (PID) and Standing Rules of Engagement (SROE) adherence.",
        },
        "FM-2-0-HUMINT": {
            "name": "Human Intelligence Collector Operations (FM 2-0 / TC 2-22.3)",
            "category": ProcedureCategory.HUMINT,
            "required_clearance": ClearanceLevel.SECRET,
            "steps": [
                "Target Profiling: Assess psychological traits, vulnerabilities, and ideological motivations",
                "Contact and Rapport Building: Establish clandestine communication and credibility",
                "Elicitation: Gather critical information through non-coercive conversational techniques",
                "Debriefing and Cross-Verification: Validate source reporting against collateral SIGINT/IMINT",
                "Termination or Cold Storage: Safeguard source identity and extract or deactivate cleanly",
            ],
            "restrictions": [
                "Strict prohibition against coercive, degrading, or unlawful interrogation techniques",
                "Source identity must be protected with cryptonyms and compartmented handling",
            ],
            "roe_guidelines": "Comply strictly with the Geneva Conventions, Army Field Manual 2-22.3, and legal review.",
        },
    }

    @classmethod
    def get_standard_procedure(cls, doctrine_code: str) -> Procedure | None:
        """Instantiates a canonical Procedure from vetted military doctrine."""
        data = cls.CORE_DOCTRINES.get(doctrine_code.upper())
        if not data:
            return None

        return Procedure(
            id=f"PROC-DOCTRINE-{doctrine_code.upper()}",
            name=data["name"],
            category=data["category"],
            steps=data["steps"],
            restrictions=data["restrictions"],
            required_clearance=data["required_clearance"],
            roe_guidelines=data["roe_guidelines"],
            metadata={"doctrine_code": doctrine_code, "authority": "DoD / JCS"},
        )

    @classmethod
    def list_all_procedures(cls) -> list[Procedure]:
        """Returns all built-in military intelligence doctrines."""
        procs = []
        for code in cls.CORE_DOCTRINES:
            p = cls.get_standard_procedure(code)
            if p:
                procs.append(p)
        return procs
