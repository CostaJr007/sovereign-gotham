"""
Sovereign Gotham - Unsloth Fast Language Model Fine-Tuning Pipeline
Optimized for AMD Radeon RX 7600 XT (16 GB VRAM) on Windows.
Runs 4-bit QLoRA with Unsloth native kernels, eliminating RAM saturation and maximizing GPU compute.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

try:
    _project_root = str(Path(__file__).resolve().parent.parent)
except NameError:
    _project_root = str(Path(".").resolve())

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

logger = logging.getLogger("SovereignGotham.UnslothTrainer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def parse_args():
    parser = argparse.ArgumentParser(description="Unsloth Fine-tuning for DeepSeek-R1-Distill-Qwen-7B")
    parser.add_argument(
        "--model_id",
        type=str,
        default="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        help="HuggingFace model ID",
    )
    parser.add_argument(
        "--dataset_path",
        type=str,
        default="training_data/sovereign_deepseek_r1_agent.jsonl",
        help="Path to training dataset JSONL",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="D:/sovereign_models/deepseek_r1_sovereign_agent" if Path("D:/").exists() else "./models/deepseek_r1_sovereign_agent",
        help="Output directory for fine-tuned LoRA adapters",
    )
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Per-device batch size")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--max_seq_length", type=int, default=2048, help="Max sequence length")
    parser.add_argument("--lora_r", type=int, default=64, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=128, help="LoRA alpha")
    return parser.parse_args()


def load_jsonl_dataset(file_path: str | Path) -> list[dict[str, Any]]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            l = line.strip()
            if l:
                records.append(json.loads(l))
    logger.info(f"Loaded {len(records)} samples from {path}")
    return records


def format_sharegpt_to_text(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    formatted = []
    for r in records:
        convs = r.get("conversations", [])
        sys_msg = ""
        user_msg = ""
        gpt_msg = ""
        for c in convs:
            role = c.get("from")
            val = c.get("value", "")
            if role == "system":
                sys_msg = val
            elif role in ("human", "user"):
                user_msg = val
            elif role in ("gpt", "assistant"):
                gpt_msg = val

        full_text = (
            f"<|im_start|>system\n{sys_msg}<|im_end|>\n"
            f"<|im_start|>user\n{user_msg}<|im_end|>\n"
            f"<|im_start|>assistant\n{gpt_msg}<|im_end|>"
        )
        formatted.append({"text": full_text})
    return formatted


def train():
    args = parse_args()
    logger.info("==========================================================================")
    logger.info("  SOVEREIGN GOTHAM // UNSLOTH AMD RADEON RX 7600 XT ACCELERATED PIPELINE")
    logger.info("==========================================================================")

    status_file = Path("D:/sovereign_models/training_status.json") if Path("D:/").exists() else Path("./models/training_status.json")
    status_file.parent.mkdir(parents=True, exist_ok=True)

    initial_status = {
        "status": "CARREGANDO_GPU",
        "progress_pct": 0.0,
        "current_step": 0,
        "total_steps": 1000,
        "epoch": 0.0,
        "total_epochs": args.epochs,
        "loss": None,
        "loss_history": [],
        "elapsed_seconds": 0,
        "eta_seconds": 0,
        "vram_target": "14.0 GB",
        "gpu_name": "AMD Radeon RX 7600 XT (16 GB GDDR6)",
        "model_id": args.model_id,
        "dataset_samples": 0,
    }
    status_file.write_text(json.dumps(initial_status, indent=2), encoding="utf-8")

    import torch
    from datasets import Dataset
    from transformers import TrainerCallback, TrainingArguments
    from trl import SFTTrainer
    from unsloth import FastLanguageModel

    # 1. Load Dataset
    raw_records = load_jsonl_dataset(args.dataset_path)
    train_data = format_sharegpt_to_text(raw_records)
    hf_dataset = Dataset.from_list(train_data)
    initial_status["dataset_samples"] = len(train_data)
    status_file.write_text(json.dumps(initial_status, indent=2), encoding="utf-8")

    # 2. Load 4-bit Quantized Model directly onto AMD GPU
    logger.info(f"Loading {args.model_id} with Unsloth 4-bit GPU acceleration...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model_id,
        max_seq_length=args.max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )

    # 3. Apply High-Intelligence LoRA Adapters (Rank 64)
    logger.info("Configuring Unsloth optimized LoRA adapters (Rank 64)...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=args.lora_alpha,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    # 4. Progress Callback for Live Web Monitor on Port 8888
    class UnslothMonitorCallback(TrainerCallback):
        def __init__(self, s_file: Path, total_epochs: int):
            self.s_file = s_file
            self.total_epochs = total_epochs
            self.start_time = time.time()
            self.loss_history = []

        def on_log(self, tr_args, state, control, logs=None, **kwargs):
            if not logs:
                return
            elapsed = int(time.time() - self.start_time)
            cur_step = state.global_step
            max_s = state.max_steps if state.max_steps > 0 else 1
            pct = round((cur_step / max_s) * 100, 2)
            rate = elapsed / max(cur_step, 1)
            remaining = max(max_s - cur_step, 0)
            eta = int(remaining * rate)

            loss = logs.get("loss")
            if loss is not None:
                self.loss_history.append({"step": cur_step, "loss": round(float(loss), 4)})

            status = {
                "status": "TREINANDO_GPU",
                "progress_pct": min(pct, 100.0),
                "current_step": cur_step,
                "total_steps": max_s,
                "epoch": round(state.epoch or 0, 2),
                "total_epochs": self.total_epochs,
                "loss": float(loss) if loss is not None else (self.loss_history[-1]["loss"] if self.loss_history else None),
                "loss_history": self.loss_history[-30:],
                "elapsed_seconds": elapsed,
                "eta_seconds": eta,
                "vram_target": "14.0 GB",
                "gpu_name": "AMD Radeon RX 7600 XT (16 GB)",
                "model_id": args.model_id,
                "dataset_samples": len(train_data),
            }
            try:
                self.s_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
            except Exception:
                pass

        def on_train_end(self, tr_args, state, control, **kwargs):
            elapsed = int(time.time() - self.start_time)
            status = {
                "status": "CONCLUÍDO",
                "progress_pct": 100.0,
                "current_step": state.global_step,
                "total_steps": state.global_step,
                "epoch": float(self.total_epochs),
                "total_epochs": self.total_epochs,
                "loss": self.loss_history[-1]["loss"] if self.loss_history else None,
                "loss_history": self.loss_history[-30:],
                "elapsed_seconds": elapsed,
                "eta_seconds": 0,
                "vram_target": "14.0 GB",
                "gpu_name": "AMD Radeon RX 7600 XT (16 GB)",
                "model_id": args.model_id,
                "dataset_samples": len(train_data),
            }
            try:
                self.s_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
            except Exception:
                pass

    # 5. Trainer Setup
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        warmup_steps=10,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        fp16=not torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False,
        bf16=torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False,
        logging_steps=5,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=hf_dataset,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=training_args,
        callbacks=[UnslothMonitorCallback(status_file, args.epochs)],
    )

    logger.info("[*] Starting Unsloth GPU accelerated training...")
    trainer_stats = trainer.train()

    # 6. Save Model to Drive D:
    final_path = Path(args.output_dir) / "final_adapter"
    model.save_pretrained(str(final_path))
    tokenizer.save_pretrained(str(final_path))
    logger.info(f"[✓] Unsloth model successfully trained and saved to: {final_path}")


if __name__ == "__main__":
    train()
