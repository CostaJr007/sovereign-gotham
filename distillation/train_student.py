"""
Sovereign Gotham - Student Distillation Trainer (DirectML / AMD Radeon RX 7600 XT)
Trains the student SLM (DeepSeek-R1-Distill-Qwen) on curated teacher reasoning traces
using hardware-accelerated DirectX 12 compute.
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
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    PROJECT_ROOT = Path(".").resolve()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
import torch_directml
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

from distillation.config import default_distill_config

logger = logging.getLogger("SovereignGotham.DistillTrainer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def parse_args():
    parser = argparse.ArgumentParser(description="Sovereign Gotham Student Distillation Trainer")
    parser.add_argument("--dataset", type=str, default=str(default_distill_config.curated_dataset_path))
    parser.add_argument("--output_dir", type=str, default=str(default_distill_config.student_output_dir))
    parser.add_argument("--base_model", type=str, default=default_distill_config.student_model_id)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--grad_accum", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max_seq_length", type=int, default=512)
    parser.add_argument("--steps", type=int, default=0, help="Override max steps (0 for full dataset)")
    return parser.parse_args()


def load_dataset_samples(dataset_path: Path, tokenizer, max_seq_length: int) -> list[torch.Tensor]:
    logger.info(f"Loading curated distillation samples from {dataset_path}...")
    tokenized_items: list[torch.Tensor] = []
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            data = json.loads(line_str)
            convs = data.get("conversations", [])
            
            # Format into DeepSeek ChatML
            formatted_text = ""
            for c in convs:
                role = c["from"]
                val = c["value"]
                if role == "system":
                    formatted_text += f"<|im_start|>system\n{val}<|im_end|>\n"
                elif role == "human":
                    formatted_text += f"<|im_start|>user\n{val}<|im_end|>\n"
                elif role == "gpt":
                    formatted_text += f"<|im_start|>assistant\n{val}<|im_end|>\n"

            enc = tokenizer(
                formatted_text,
                truncation=True,
                max_length=max_seq_length,
                return_tensors="pt",
            )
            tokenized_items.append(enc["input_ids"][0])

    logger.info(f"Loaded and tokenized {len(tokenized_items)} distillation samples.")
    return tokenized_items


def save_distilled_adapter(model, tokenizer, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Serializing distilled student weights to {output_dir}...")
    
    from peft import get_peft_model_state_dict
    lora_w = get_peft_model_state_dict(model)
    cpu_lora = {k: v.detach().cpu() for k, v in lora_w.items()}
    
    model.save_pretrained(str(output_dir), state_dict=cpu_lora)
    tokenizer.save_pretrained(str(output_dir))
    logger.info(f"[✓] Distilled Student Adapter Successfully Saved to: {output_dir}")


def train_student():
    args = parse_args()
    logger.info("==========================================================================")
    logger.info("   SOVEREIGN GOTHAM // DIRECTML STUDENT DISTILLATION TRAINER")
    logger.info("==========================================================================")

    # 1. Device Setup (AMD Radeon RX 7600 XT)
    count = torch_directml.device_count()
    target_idx = 1 if count > 1 else 0
    for i in range(count):
        name = torch_directml.device_name(i)
        if "7600" in name or "RX" in name or "XT" in name:
            target_idx = i
            break
    device = torch_directml.device(target_idx)
    gpu_name = torch_directml.device_name(target_idx)
    logger.info(f"[+] DirectML Dedicated GPU Device {target_idx}: {gpu_name}")

    # Status tracking file for live dashboard on port 8888
    status_file = Path("D:/sovereign_models/training_status.json")
    status_file.parent.mkdir(parents=True, exist_ok=True)

    # 2. Tokenizer & Base Student Model
    logger.info(f"[*] Loading student model: {args.base_model}...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float32,
        trust_remote_code=True,
    ).to(device)

    # Gradient Checkpointing for VRAM stability
    base_model.gradient_checkpointing_enable()

    # 3. LoRA Configuration
    lora_cfg = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(base_model, lora_cfg)
    model.print_trainable_parameters()

    # 4. Dataset Loading
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.error(f"Curated dataset not found at {dataset_path}. Run distillation/pipeline.py first!")
        sys.exit(1)

    samples = load_dataset_samples(dataset_path, tokenizer, args.max_seq_length)
    if not samples:
        logger.error("No samples found in dataset!")
        sys.exit(1)

    # 5. Training Loop
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps_per_epoch = max(len(samples) // (args.batch_size * args.grad_accum), 1)
    total_steps = steps_per_epoch * args.epochs
    if args.steps > 0:
        total_steps = min(total_steps, args.steps)

    logger.info(f"Starting Distillation: {total_steps} gradient steps ({args.epochs} epochs) | LR: {args.lr}")
    model.train()
    step = 0
    start_time = time.time()
    accum_loss = 0.0
    loss_history: list[dict[str, Any]] = []

    # Update initial status
    status = {
        "status": "TREINANDO_DESTILACAO",
        "progress_pct": 0.0,
        "current_step": 0,
        "total_steps": total_steps,
        "epoch": 0.0,
        "total_epochs": args.epochs,
        "loss": 0.0,
        "loss_history": [],
        "elapsed_seconds": 0,
        "eta_seconds": 0,
        "vram_target": "14.0 GB",
        "gpu_name": f"{gpu_name} (16 GB GDDR6)",
        "model_id": args.base_model,
        "dataset_samples": len(samples),
    }
    status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")

    for epoch in range(args.epochs):
        optimizer.zero_grad()
        for idx, item in enumerate(samples):
            input_ids = item.unsqueeze(0).to(device)
            labels = input_ids.clone()

            outputs = model(input_ids=input_ids, labels=labels)
            loss = outputs.loss / args.grad_accum
            loss.backward()
            accum_loss += loss.item() * args.grad_accum

            if (idx + 1) % args.grad_accum == 0 or (idx + 1) == len(samples):
                optimizer.step()
                optimizer.zero_grad()
                step += 1

                elapsed = time.time() - start_time
                avg_loss = accum_loss / max(idx + 1, 1)
                speed = round(step / max(elapsed, 1), 2)
                eta = round((total_steps - step) / max(speed, 0.01), 1)
                curr_loss = round(loss.item() * args.grad_accum, 4)

                loss_history.append({"step": step, "loss": curr_loss})
                if len(loss_history) > 30:
                    loss_history.pop(0)

                progress = round((step / total_steps) * 100, 1)
                logger.info(f"Epoch {epoch+1}/{args.epochs} | Step {step}/{total_steps} ({progress}%) | Loss: {curr_loss:.4f} (Avg: {avg_loss:.4f}) | ETA: {eta:.0f}s")

                status.update({
                    "progress_pct": progress,
                    "current_step": step,
                    "epoch": round(epoch + (idx + 1) / len(samples), 2),
                    "loss": curr_loss,
                    "loss_history": loss_history,
                    "elapsed_seconds": int(elapsed),
                    "eta_seconds": int(eta),
                })
                status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")

                if args.steps > 0 and step >= args.steps:
                    break

        if args.steps > 0 and step >= args.steps:
            break

    # 6. Save Distilled Student Adapter
    output_path = Path(args.output_dir)
    save_distilled_adapter(model, tokenizer, output_path)
    
    status.update({
        "status": "DESTILACAO_CONCLUIDA",
        "progress_pct": 100.0,
        "current_step": total_steps,
        "eta_seconds": 0,
        "loss": curr_loss,
    })
    status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
    logger.info(f"[✓] Distillation Training Complete in {time.time() - start_time:.1f}s!")


if __name__ == "__main__":
    train_student()
