"""
Sovereign Gotham - Intelligence Entity Resolution Engine
Resolves target identities, aliases, and CIA/DoD cryptonyms using phonetic and fuzzy string metrics.
Deduplicates and unifies entity nodes across fragmented declassified sources.
"""

from __future__ import annotations

import difflib

from pydantic import BaseModel, Field


class EntityProfile(BaseModel):
    """Unified identity profile for a target, agent, or operational asset."""
    canonical_id: str
    canonical_name: str
    aliases: set[str] = Field(default_factory=set)
    cryptonyms: set[str] = Field(default_factory=set)
    affiliations: set[str] = Field(default_factory=set)
    threat_level: str = "MEDIUM"


class IntelligenceEntityResolver:
    """
    Deduplicates and unifies entity nodes across fragmented declassified sources.
    Handles CIA cryptonym decodings, FBI alias registers, and transliteration variations.
    """

    # Curated registry of historic declassified CIA cryptonyms
    KNOWN_CRYPTONYMS: dict[str, str] = {
        "AMTHUG": "Fidel Castro Ruz",
        "AMQUAFF": "Cuban Intelligence Extraction Network",
        "ZRRIFLE": "CIA Staff D Executive Action Capability",
        "MKULTRA": "CIA Behavioral Modification & Mind Control Program",
        "AELADLE": "Anatoliy Golitsyn",
        "CKTAW": "Soviet Military Wiretap Operation",
        "GTPROLOGUE": "Alexander Zaporozhsky",
        "CYPHER_9": "Karl Koecher",
    }

    def __init__(self, similarity_threshold: float = 0.82):
        self.threshold = similarity_threshold
        self.registry: dict[str, EntityProfile] = {}

    def register_canonical(
        self,
        canonical_id: str,
        name: str,
        cryptonyms: list[str] | None = None,
        aliases: list[str] | None = None,
        threat_level: str = "MEDIUM",
    ) -> EntityProfile:
        """Adds or updates a canonical entity profile."""
        clean_name = name.strip()
        alias_set = {clean_name.upper()}
        if aliases:
            alias_set.update(a.strip().upper() for a in aliases)

        crypto_set = set()
        if cryptonyms:
            crypto_set.update(c.strip().upper() for c in cryptonyms)

        profile = EntityProfile(
            canonical_id=canonical_id,
            canonical_name=clean_name,
            aliases=alias_set,
            cryptonyms=crypto_set,
            threat_level=threat_level,
        )
        self.registry[canonical_id] = profile
        return profile

    def resolve(self, candidate_name: str) -> str | None:
        """
        Returns canonical_id if match is found via cryptonym, alias, or fuzzy string distance.
        """
        cand_clean = candidate_name.strip().upper()
        if not cand_clean:
            return None

        # 1. Direct Cryptonym Lookup
        if cand_clean in self.KNOWN_CRYPTONYMS:
            resolved_real_name = self.KNOWN_CRYPTONYMS[cand_clean].upper()
            for cid, profile in self.registry.items():
                if profile.canonical_name.upper() == resolved_real_name or cand_clean in profile.cryptonyms:
                    return cid

        # 2. Exact Match against Canonical Names, Aliases, or Cryptonyms
        for cid, profile in self.registry.items():
            if (
                cand_clean == profile.canonical_name.upper()
                or cand_clean in profile.aliases
                or cand_clean in profile.cryptonyms
            ):
                return cid

        # 3. Fuzzy String Metric (SequenceMatcher / Jaro-Winkler approximation)
        best_match_id = None
        highest_ratio = 0.0

        for cid, profile in self.registry.items():
            pool = [profile.canonical_name] + list(profile.aliases)
            for alias in pool:
                ratio = difflib.SequenceMatcher(None, cand_clean, alias.upper()).ratio()
                if ratio > highest_ratio and ratio >= self.threshold:
                    highest_ratio = ratio
                    best_match_id = cid

        return best_match_id
