"""
Sovereign Gotham - CAPCO Intelligence Portion Marking Parser
Parses national security banners and portion markings: (TS//SI-TK//NF), (S//REL TO USA, FVEY), (U)
Adheres to the Controlled Access Program Coordination Office (CAPCO) and ISOO standards.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from ontology.models import SecurityClassification


class ParsedPortionMarking(BaseModel):
    """Structured representation of a parsed IC classification portion marking."""
    raw_marking: str
    classification: SecurityClassification
    compartments: list[str] = Field(default_factory=list)
    dissemination_controls: list[str] = Field(default_factory=list)
    is_noforn: bool = False
    is_fvey_releasable: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class CAPCOMarkingEngine:
    """
    Parses and validates US Intelligence Community (IC) banner and portion markings.
    """

    LEVEL_MAP: dict[str, SecurityClassification] = {
        "U": SecurityClassification.UNCLASSIFIED,
        "UNCLASSIFIED": SecurityClassification.UNCLASSIFIED,
        "C": SecurityClassification.CONFIDENTIAL,
        "CONFIDENTIAL": SecurityClassification.CONFIDENTIAL,
        "S": SecurityClassification.SECRET,
        "SECRET": SecurityClassification.SECRET,
        "TS": SecurityClassification.TOP_SECRET,
        "TOP SECRET": SecurityClassification.TOP_SECRET,
        "TOP_SECRET": SecurityClassification.TOP_SECRET,
        "RESTRICTED": SecurityClassification.RESTRICTED,
        "DECLASSIFIED": SecurityClassification.DECLASSIFIED,
    }

    # Matches markings like (U), (S), (TS//SI-TK//NF), (S//REL TO USA, FVEY), (TS//HCS-P/SI/TK//ORCON/NOFORN)
    PORTION_REGEX = re.compile(
        r"\(([U|C|S|TS|TOP\s*SECRET|SECRET|CONFIDENTIAL|UNCLASSIFIED]+)"
        r"(?:\s*//\s*([^/()]+))?"
        r"(?:\s*//\s*([^/()]+))?\)",
        re.IGNORECASE,
    )

    # Banner regex at document head (e.g. TOP SECRET // SI // NOFORN)
    BANNER_REGEX = re.compile(
        r"^(TOP[\s_-]?SECRET|SECRET|CONFIDENTIAL|UNCLASSIFIED)"
        r"(?:\s*//\s*([A-Z0-9_\-\s/]+))?"
        r"(?:\s*//\s*([A-Z0-9_\-\s,/]+))?",
        re.IGNORECASE | re.MULTILINE,
    )

    @classmethod
    def parse_portion(cls, text: str) -> ParsedPortionMarking | None:
        """Extracts the first portion marking found in a line or paragraph."""
        match = cls.PORTION_REGEX.search(text)
        if not match:
            return None

        # Extract all parts split by //
        raw_inner = match.group(0).strip("()")
        parts = [p.strip() for p in raw_inner.split("//")]
        
        level_raw = parts[0].strip().upper() if parts else "UNCLASSIFIED"
        classification = cls.LEVEL_MAP.get(level_raw, SecurityClassification.UNCLASSIFIED)

        compartments: list[str] = []
        dissem: list[str] = []

        for p in parts[1:]:
            p_upper = p.upper()
            # Check if this part represents dissemination controls
            if any(ctrl in p_upper for ctrl in ["REL TO", "NOFORN", "NF", "ORCON", "PROPIN", "FVEY", "EYES ONLY"]):
                for d in re.split(r"[,/]", p):
                    clean_d = d.strip().upper()
                    if clean_d:
                        dissem.append(clean_d)
            else:
                # Compartments (SI, TK, HCS, etc.)
                for c in re.split(r"[-/]", p):
                    clean_c = c.strip().upper()
                    if clean_c:
                        compartments.append(clean_c)

        is_noforn = any("NF" in d or "NOFORN" in d for d in dissem) or "NOFORN" in raw_inner.upper() or "//NF" in raw_inner.upper()
        is_fvey = any("FVEY" in d for d in dissem) or "FVEY" in raw_inner.upper()

        return ParsedPortionMarking(
            raw_marking=match.group(0),
            classification=classification,
            compartments=compartments,
            dissemination_controls=dissem,
            is_noforn=is_noforn,
            is_fvey_releasable=is_fvey,
        )

    @classmethod
    def parse_banner(cls, text: str) -> ParsedPortionMarking | None:
        """Parses document-level classification banner (e.g. at header or footer)."""
        match = cls.BANNER_REGEX.search(text.strip())
        if not match:
            return None

        level_raw = match.group(1).strip().upper().replace("-", " ").replace("_", " ")
        classification = cls.LEVEL_MAP.get(level_raw, SecurityClassification.UNCLASSIFIED)

        compartments_raw = match.group(2) or ""
        dissem_raw = match.group(3) or ""

        compartments = [c.strip().upper() for c in re.split(r"[-/]", compartments_raw) if c.strip()]
        dissem = [d.strip().upper() for d in re.split(r"//|,", dissem_raw) if d.strip()]

        is_noforn = any("NF" in d or "NOFORN" in d for d in dissem)
        is_fvey = any("FVEY" in d for d in dissem)

        return ParsedPortionMarking(
            raw_marking=match.group(0),
            classification=classification,
            compartments=compartments,
            dissemination_controls=dissem,
            is_noforn=is_noforn,
            is_fvey_releasable=is_fvey,
        )
