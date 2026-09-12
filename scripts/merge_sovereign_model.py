"""
Sovereign Gotham - LoRA Weight Fusion (Merge & Unload)
Combines the fine-tuned PEFT LoRA adapter (trained on 3,124 declassified intelligence samples)
with the base DeepSeek-R1-Distill-Qwen-1.5B model to generate an autonomous, standalone model.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args():
    parser = argparse.ArgumentParser(description="Sovereign Gotham - Merge LoRA Adapter into Base Model")
    parser.add_argument(
        "--base_model",
        type=str,
        default="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
        help="HuggingFace base model ID or local directory",
    )
    parser.add_argument(
        "--adapter_dir",
        type=str,
        default="D:/sovereign_distillation/student_checkpoints/distilled_student_adapter",
        help="Path to trained PEFT LoRA adapter",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="D:/sovereign_models/sovereign_gotham_merged_1.5b",
        help="Destination directory for the unified standalone model",
    )
    return parser.parse_args()


def merge_and_save(base_model_id: str, adapter_dir: str, output_dir: str):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    adapter_path = Path(adapter_dir)
    output_path = Path(output_dir)

    if not adapter_path.exists():
        raise FileNotFoundError(f"Adapter directory not found at: {adapter_path}")

    output_path.mkdir(parents=True, exist_ok=True)

    print("==========================================================================")
    print("   SOVEREIGN GOTHAM // MODEL WEIGHT FUSION ENGINE")
    print("==========================================================================")
    print(f"[*] Base Model:       {base_model_id}")
    print(f"[*] LoRA Adapter:     {adapter_path}")
    print(f"[*] Target Directory: {output_path}")
    print("--------------------------------------------------------------------------")

    start_time = time.time()

    # 1. Load Tokenizer
    print("[1/5] Loading tokenizer from adapter path...")
    tokenizer = AutoTokenizer.from_pretrained(str(adapter_path), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 2. Load Base Model in float32 for clean arithmetic merge
    print("[2/5] Loading base model into RAM...")
    t0 = time.time()
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=torch.float32,
        device_map="cpu",
        trust_remote_code=True,
    )
    print(f"      Base model loaded in {time.time() - t0:.2f}s")

    # 3. Attach LoRA Adapter
    print("[3/5] Attaching LoRA weights from adapter...")
    t0 = time.time()
    peft_model = PeftModel.from_pretrained(base_model, str(adapter_path))
    print(f"      LoRA attached in {time.time() - t0:.2f}s")

    # 4. Perform Merge and Unload
    print("[4/5] Executing weight fusion (merge_and_unload)...")
    t0 = time.time()
    merged_model = peft_model.merge_and_unload()
    # Cast to float16 for standard, efficient footprint (~3.1 GB)
    merged_model = merged_model.to(torch.float16)
    print(f"      Weights fused and converted to float16 in {time.time() - t0:.2f}s")

    # 5. Save unified standalone weights and tokenizer
    print(f"[5/5] Saving standalone model to {output_path}...")
    t0 = time.time()
    merged_model.save_pretrained(
        str(output_path),
        safe_serialization=True,
        max_shard_size="4GB",
    )
    tokenizer.save_pretrained(str(output_path))
    print(f"      Saved successfully in {time.time() - t0:.2f}s")

    # Generate metadata report
    elapsed_total = time.time() - start_time
    metadata = {
        "model_name": "Sovereign Gotham DeepSeek-R1 Distill 1.5B (Unified)",
        "base_model": base_model_id,
        "adapter_source": str(adapter_path),
        "merged_at": datetime.now(timezone.utc).isoformat(),
        "precision": "float16",
        "serialization": "safetensors",
        "training_dataset": "3,124 declassified intelligence reports (CIA, DoD, NSA, Army)",
        "fusion_duration_seconds": round(elapsed_total, 2),
    }

    metadata_file = output_path / "sovereign_merge_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("--------------------------------------------------------------------------")
    print(f"[✓] Fusion completed successfully in {elapsed_total:.2f}s.")
    print(f"[✓] Standalone model ready at: {output_path}")
    print("==========================================================================")


if __name__ == "__main__":
    args = parse_args()
    merge_and_save(args.base_model, args.adapter_dir, args.output_dir)
