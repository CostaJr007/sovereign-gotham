"""
Sovereign Gotham - DSpark Dual-Engine Training & Curation Pipeline
Applies the Creator-Curator methodology at the AI training level.
Generates DPO (Direct Preference Optimization) preference pairs where:
  - Chosen: Audited and verified by the Curator (compliant with ROE, ground truth, and clearance).
  - Rejected: Flagged by the Curator for containing adversarial edge-case flaws, hallucinations, or ROE breaches.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    Agent_Role,
    Operation,
    Target_Entity,
)

logger = logging.getLogger("SovereignGotham.DSparkCuration")


class DPOPreferenceSample(BaseModel):
    """Pair of verified vs rejected tactical reasoning for DPO alignment."""
    system_prompt: str
    prompt: str
    chosen: str = Field(..., description="Curator-approved response (adheres to ROE, I/O contracts, and CoT)")
    rejected: str = Field(..., description="Curator-rejected response (contains ROE breach or tactical flaw)")
    curator_notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "system": self.system_prompt,
            "prompt": self.prompt,
            "chosen": self.chosen,
            "rejected": self.rejected,
            "curator_notes": self.curator_notes,
        }


class DSparkTrainingCurator:
    """
    Implements the DSpark Dual-Engine verification loop for dataset synthesis.
    Audits candidate samples against Ontological Ground Truth and Rules of Engagement.
    """

    def __init__(self, graph: GothamKnowledgeGraph):
        self.graph = graph

    def curate_dpo_dataset(self, output_path: str | Path) -> int:
        """
        Generates pairs of (Chosen, Rejected) responses across tactical intelligence scenarios.
        Teaches the DeepSeek-R1 model what NOT to do (preventing unauthorized kinetic actions).
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        samples: list[DPOPreferenceSample] = []
        operations = [obj for obj in self.graph.entities.values() if isinstance(obj, Operation)]
        targets = [obj for obj in self.graph.entities.values() if isinstance(obj, Target_Entity)]
        roles = [obj for obj in self.graph.entities.values() if isinstance(obj, Agent_Role)]

        system_prompt = (
            "You are the Sovereign Gotham Chief Intelligence Analyst (DeepSeek-R1 Core). "
            "You reason systematically and critically inside <thought>...</thought> tags, "
            "evaluating motives, counter-intelligence risks, and Rules of Engagement (ROE). "
            "Always ground your final verdict in the provided Ontological Context and emit structured JSON."
        )

        for op in operations:
            for target in targets:
                for role in roles:
                    # Scenario: Request to conduct unauthorized breach without PID or clearance
                    prompt = (
                        f"Operational Scenario: Target {target.name} ({target.threat_level}) is moving through a sensitive "
                        f"sector. Agent Role '{role.designation}' (Clearance: {role.clearance_level}) requests authorization "
                        f"to initiate immediate kinetic raid."
                    )

                    # CHOSEN (DSpark Curator Approved): Reflexive thought, checks clearance, rejects reckless assault
                    chosen = (
                        "<thought>\n"
                        f"1. Evaluating command request from {role.designation} with clearance {role.clearance_level}.\n"
                        f"2. Inspecting target {target.name}: Threat level is {target.threat_level}.\n"
                        "3. Checking Rules of Engagement: Immediate kinetic raid in sensitive sector requires verified "
                        "Positive Identification (PID) and Chief of Station / National Command authority.\n"
                        f"4. Clearance evaluation: {role.clearance_level} lacks statutory power for unilateral strike sanction.\n"
                        "5. Curator Invariant Check: Action prohibited under SROE guidelines. Halting breach; recommending passive surveillance.\n"
                        "</thought>\n"
                        "```json\n"
                        "{\n"
                        '  "directive": "DENY_KINETIC_BREACH",\n'
                        '  "compliance_status": "BLOCKED_ROE",\n'
                        '  "authorized_alternative": "DEPLOY_PASSIVE_OBSERVATION",\n'
                        '  "rationale": "Insufficient command authority and lack of confirmed PID. Kinetic strike would cause diplomatic crisis."\n'
                        "}\n"
                        "```"
                    )

                    # REJECTED (Curator Flawed / Hallucination): Approves kinetic strike without authorization
                    rejected = (
                        "<thought>\n"
                        f"Target {target.name} is dangerous. We should attack immediately to eliminate the threat.\n"
                        "</thought>\n"
                        "```json\n"
                        "{\n"
                        '  "directive": "EXECUTE_IMMEDIATE_RAID",\n'
                        '  "compliance_status": "PERMITTED",\n'
                        '  "rationale": "Target presents clear danger."\n'
                        "}\n"
                        "```"
                    )

                    curator_notes = (
                        "Rejected candidate commits serious ROE violation: approves kinetic raid without command authority "
                        "validation, ignores lack of Positive Identification, and bypasses CAPCO clearance gates."
                    )

                    samples.append(DPOPreferenceSample(
                        system_prompt=system_prompt,
                        prompt=prompt,
                        chosen=chosen,
                        rejected=rejected,
                        curator_notes=curator_notes,
                    ))

        # Write DPO JSONL
        with open(out_file, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(s.to_dict(), ensure_ascii=False) + "\n" for s in samples)

        logger.info(f"Generated {len(samples)} DSpark DPO preference pairs at {out_file}")
        return len(samples)
