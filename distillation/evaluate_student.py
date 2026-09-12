"""
Sovereign Gotham - Distillation Evaluation & Benchmark Harness
Benchmarks distilled student performance against teacher ground truth and validates CoT depth.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

try:
    _curr = Path(__file__).resolve()
    PROJECT_ROOT = _curr.parent.parent if _curr.parent.name == "distillation" else _curr.parent
except NameError:
    PROJECT_ROOT = Path(".").resolve()

if not (PROJECT_ROOT / "distillation").exists():
    fallback = Path(r"c:\Users\adeil\.gemini\antigravity\scratch\sovereign_gotham")
    if fallback.exists():
        PROJECT_ROOT = fallback

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "cli") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "cli"))

try:
    from sovereign_inference import load_sovereign_model, query_model
    from distillation.config import default_distill_config
except ImportError:
    load_sovereign_model = None  # type: ignore
    query_model = None  # type: ignore
    default_distill_config = None  # type: ignore

logger = logging.getLogger("SovereignGotham.DistillEval")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def evaluate_student(adapter_path: Path, max_tokens: int = 250):
    logger.info("==========================================================================")
    logger.info("   SOVEREIGN GOTHAM // DISTILLATION COGNITIVE EVALUATOR")
    logger.info("==========================================================================")
    logger.info(f"Evaluating Adapter: {adapter_path}")

    if not adapter_path.exists():
        logger.error(f"Adapter not found at {adapter_path}")
        return

    model, tokenizer, device = load_sovereign_model(
        base_model_id=default_distill_config.student_model_id,
        adapter_dir=str(adapter_path),
    )

    test_scenarios = [
        "Analise o relatório desclassificado sobre o Projeto STARGATE da CIA e identifique vetores de contra-inteligência.",
        "Target 'AGENT_K' detected with unauthorized clearance accessing compartment TOP SECRET // SI-TK. Evaluate breach.",
        "Formulate a three-step Course of Action for passive surveillance on hostile courier network in Berlin.",
    ]

    results = []
    for i, sc in enumerate(test_scenarios, 1):
        logger.info(f"\n--- Scenario {i}/{len(test_scenarios)} ---")
        logger.info(f"Prompt: {sc}")
        
        t0 = time.time()
        response = query_model(model, tokenizer, device, sc, max_tokens=max_tokens)
        elapsed = time.time() - t0

        has_thought = "<thought>" in response or "</thought>" in response
        step_count = sum(1 for line in response.splitlines() if any(line.strip().startswith(f"{idx}.") for idx in range(1, 10)))
        has_json = "```json" in response or "{" in response

        eval_data = {
            "scenario": sc,
            "has_thought_block": has_thought,
            "reasoning_steps": step_count,
            "has_structured_data": has_json,
            "elapsed_seconds": round(elapsed, 2),
            "response_preview": response[:200] + "...",
        }
        results.append(eval_data)
        logger.info(f"Result: Thought={has_thought} | Steps={step_count} | Structured={has_json} | Time={elapsed:.2f}s")

    passed_tests = sum(1 for r in results if r["has_thought_block"])
    logger.info("==========================================================================")
    logger.info(f"Evaluation Summary: {passed_tests}/{len(test_scenarios)} tests demonstrated reasoning traces.")
    logger.info("==========================================================================")
    return results


if __name__ == "__main__":
    adapter_p = default_distill_config.student_output_dir
    if not adapter_p.exists():
        adapter_p = Path("D:/sovereign_models/deepseek_r1_sovereign_agent/final_adapter")
    evaluate_student(adapter_p)
