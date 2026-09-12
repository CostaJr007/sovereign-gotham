"""
Sovereign Gotham - DSpark Distillation Curator & Filter
Audits raw teacher reasoning samples against strict I/O contracts,
CAPCO classification rules, and anti-hallucination standards.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel

try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    PROJECT_ROOT = Path(".").resolve()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from distillation.config import DistillationConfig, default_distill_config
from distillation.teacher_engine import RawDistillSample

logger = logging.getLogger("SovereignGotham.DistillCurator")


class CuratedDistillSample(BaseModel):
    """Audited and approved sample for student training in ShareGPT format."""
    system_prompt: str
    user_prompt: str
    assistant_response: str
    audit_score: float = 1.0
    curator_log: str = "PASSED_ALL_GATES"

    def to_sharegpt(self) -> dict[str, Any]:
        return {
            "conversations": [
                {"from": "system", "value": self.system_prompt},
                {"from": "human", "value": self.user_prompt},
                {"from": "gpt", "value": self.assistant_response},
            ]
        }


class DistillationCuratorFilter:
    """
    Applies the DSpark Dual-Engine Curator filters to teacher distillation samples.
    Rejects malformed, shallow, or hallucinated traces.
    """

    SYSTEM_PROMPT = (
        "You are Sovereign Gotham, an autonomous intelligence analysis engine. "
        "Analyze the operational situation, extract entities, evaluate counter-intelligence risks, "
        "and produce rigorous reasoning within <thought>...</thought> tags before issuing your final directive."
    )

    def __init__(self, config: DistillationConfig | None = None):
        self.config = config or default_distill_config

    def audit_sample(self, raw: RawDistillSample) -> tuple[bool, str]:
        """
        Audits a raw teacher sample across 5 quality gates.
        Returns (is_approved, reason).
        """
        # Gate 1: Check Thought Length & Depth
        thought = raw.teacher_thought.strip()
        if len(thought) < self.config.min_reasoning_length:
            return False, f"REJECTED: Reasoning trace too short ({len(thought)} < {self.config.min_reasoning_length})"

        # Gate 2: Check Step-by-Step Structure using robust multiline regex
        step_count = len(re.findall(r"^\s*\d+[\.\)]", thought, flags=re.MULTILINE))
        if step_count < self.config.min_thought_steps:
            return False, f"REJECTED: Insufficient reasoning steps ({step_count} < {self.config.min_thought_steps})"

        # Gate 3: Check Output Schema & JSON Validability
        out = raw.teacher_output
        if not isinstance(out, dict) or not out:
            return False, "REJECTED: Output payload is not a valid dictionary"

        required_keys = ["document_id", "threat_rating", "course_of_action", "confidence_score"]
        missing = [k for k in required_keys if k not in out]
        if missing:
            return False, f"REJECTED: Missing required output keys: {missing}"

        # Gate 4: ROE & Compliance Check
        status = str(out.get("compliance_status", ""))
        if "VIOLATION" in status or "BREACH" in status:
            return False, f"REJECTED: Sample contains unresolved ROE breach ({status})"

        # Gate 5: Confidence Score Threshold with graceful type-safe coercion
        raw_conf = out.get("confidence_score", 0.0)
        try:
            conf_val = float(raw_conf)
        except (ValueError, TypeError):
            return False, f"REJECTED: Non-numeric confidence score ({raw_conf})"

        if conf_val < 0.70:
            return False, f"REJECTED: Confidence score below threshold ({conf_val} < 0.70)"

        return True, "PASSED"

    def curate_and_export(
        self,
        raw_samples: list[RawDistillSample],
        output_file: Path | None = None,
        append: bool = True,
    ) -> tuple[int, int]:
        """
        Curates a list of raw teacher samples and exports the approved ones to JSONL.
        Returns (approved_count, rejected_count).
        """
        dest_file = Path(output_file) if output_file else self.config.curated_dataset_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        approved: list[CuratedDistillSample] = []
        rejected_count = 0

        for s in raw_samples:
            ok, reason = self.audit_sample(s)
            if not ok:
                rejected_count += 1
                logger.debug(f"Curator rejected sample {s.source_id}: {reason}")
                continue

            # Build Formatted Assistant Response
            context_str = json.dumps(s.context, indent=2, ensure_ascii=False)
            user_msg = f"{s.directive}\n\n[ONTOLOGICAL INTELLIGENCE CONTEXT]\n{context_str}"
            assistant_msg = (
                f"<thought>\n{s.teacher_thought}\n</thought>\n\n"
                f"```json\n{json.dumps(s.teacher_output, indent=2, ensure_ascii=False)}\n```"
            )

            try:
                score = float(s.teacher_output.get("confidence_score", 0.95))
            except (ValueError, TypeError):
                score = 0.95

            approved.append(CuratedDistillSample(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_msg,
                assistant_response=assistant_msg,
                audit_score=score,
                curator_log="AUDITED_AND_APPROVED_BY_DSPARK_CURATOR",
            ))

        # Write or append to JSONL
        mode = "a" if (append and dest_file.exists()) else "w"
        with open(dest_file, mode, encoding="utf-8") as f:
            f.writelines(json.dumps(item.to_sharegpt(), ensure_ascii=False) + "\n" for item in approved)

        logger.info(f"[✓] Curated {len(approved)} distillation samples (Rejected {rejected_count}) -> {dest_file} (mode: {mode})")
        return len(approved), rejected_count
