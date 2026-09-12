"""
Sovereign Gotham - Ingestion Document Loader
Extracts text, calculates air-gapped cryptographic provenance, and normalizes intelligence headers.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from ontology.models import SecurityClassification


class DeclassifiedDocumentLoader:
    """Loads and standardizes declassified documents (PDF / TXT)."""

    CLASSIFICATION_PATTERNS = {
        SecurityClassification.TOP_SECRET: r"\b(TOP[\s_-]?SECRET)\b",
        SecurityClassification.SECRET: r"\b(SECRET)\b",
        SecurityClassification.CONFIDENTIAL: r"\b(CONFIDENTIAL)\b",
        SecurityClassification.RESTRICTED: r"\b(RESTRICTED)\b",
        SecurityClassification.UNCLASSIFIED: r"\b(UNCLASSIFIED)\b",
        SecurityClassification.DECLASSIFIED: r"\b(DECLASSIFIED|SANITIZED COPY)\b",
    }

    AGENCY_PATTERNS = {
        "CIA": r"\b(CENTRAL INTELLIGENCE AGENCY|CIA|CREST)\b",
        "FBI": r"\b(FEDERAL BUREAU OF INVESTIGATION|FBI)\b",
        "DOD": r"\b(DEPARTMENT OF DEFENSE|DOD|US ARMY|AIR FORCE|NAVY)\b",
        "DIA": r"\b(DEFENSE INTELLIGENCE AGENCY|DIA)\b",
    }

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Cryptographic hash for chain-of-custody and sovereign provenance."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def load_file(cls, file_path: str | Path) -> dict[str, Any]:
        """Extract text and metadata from file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        provenance_hash = cls.calculate_sha256(path)
        raw_text = ""

        if path.suffix.lower() == ".pdf":
            reader = PdfReader(str(path))
            pages_text = []
            for i, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                pages_text.append(txt)
            raw_text = "\n\n".join(pages_text)
        else:
            raw_text = path.read_text(encoding="utf-8", errors="replace")

        metadata = cls._extract_metadata(raw_text, path.name)
        metadata["provenance_hash"] = provenance_hash
        metadata["raw_content"] = raw_text
        metadata["file_path"] = str(path.resolve())

        return metadata

    @classmethod
    def _extract_metadata(cls, text: str, filename: str) -> dict[str, Any]:
        """Heuristic and regex parsing of intelligence headers."""
        # 1. Source Agency
        source = "UNKNOWN_AGENCY"
        for agency, pattern in cls.AGENCY_PATTERNS.items():
            if re.search(pattern, text[:1500], re.IGNORECASE):
                source = agency
                break

        # 2. Document ID
        doc_id_match = re.search(r"DOCUMENT\s*ID\s*:\s*([A-Z0-9\-_]+)", text, re.IGNORECASE)
        doc_id = doc_id_match.group(1).strip() if doc_id_match else f"DOC-{Path(filename).stem.upper()}"

        # 3. Subject / Title
        subj_match = re.search(r"SUBJECT\s*:\s*(.+?)(?:\n|\r)", text, re.IGNORECASE)
        title = subj_match.group(1).strip() if subj_match else Path(filename).stem.replace("_", " ").title()

        # 4. Declassification Date
        date_match = re.search(r"DECLASSIFICATION\s*DATE\s*:\s*(\d{4}[-/]\d{2}[-/]\d{2})", text, re.IGNORECASE)
        if not date_match:
            date_match = re.search(r"\b(\d{4}[-/]\d{2}[-/]\d{2})\b", text[:1000])
        doc_date = date_match.group(1).replace("/", "-") if date_match else "1985-01-01"

        # 5. Security Classification
        classification = SecurityClassification.DECLASSIFIED
        for sec_cls, pattern in cls.CLASSIFICATION_PATTERNS.items():
            if re.search(pattern, text[:1500], re.IGNORECASE):
                classification = sec_cls
                break

        # 6. Executive Summary extraction (first 300 chars or mission objective)
        summary = ""
        obj_match = re.search(r"(?:MISSION OBJECTIVE|MANDATE|SUMMARY)\s*:\s*(.+?)(?:\n\n|\n[0-9]\.|\Z)", text, re.IGNORECASE | re.DOTALL)
        if obj_match:
            summary = obj_match.group(1).strip().replace("\n", " ")
        else:
            summary = text.strip()[:400] + "..."

        return {
            "id": doc_id,
            "source": source,
            "title": title,
            "document_date": doc_date,
            "classification_original": classification,
            "summary": summary,
        }
