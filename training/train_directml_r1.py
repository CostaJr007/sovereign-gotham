"""
Sovereign Gotham - Native DirectML GPU Training Pipeline for AMD Radeon RX 7600 XT
Binds tensors directly to the dedicated AMD Radeon RX 7600 XT (16 GB GDDR6) via DirectX 12 Compute.
Renders real-time training progress to D:/sovereign_models/training_status.json and port 8888.
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

logger = logging.getLogger("SovereignGotham.DirectMLTrainer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def parse_args():
    parser = argparse.ArgumentParser(description="DirectML GPU Training for Sovereign Gotham")
    parser.add_argument("--model_id", type=str, default="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B")
    parser.add_argument("--dataset_path", type=str, default="training_data/palantir_cia_dod_organic_english.jsonl")
    parser.add_argument("--output_dir", type=str, default="D:/sovereign_models/sovereign_master_lora")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--grad_accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=6e-5)
    parser.add_argument("--max_seq_length", type=int, default=4096)
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--max_steps", type=int, default=35, help="Max optimization steps (-1 for full dataset)")
    return parser.parse_args()


def load_dataset(file_path: str | Path):
    path = Path(file_path)
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))
    return records


def format_conversations(records: list[dict[str, Any]]) -> list[tuple[str, str]]:
    pairs = []
    for r in records:
        convs = r.get("conversations", [])
        sys_msg, user_msg, gpt_msg = "", "", ""
        for c in convs:
            role = c.get("from")
            val = c.get("value", "")
            if role == "system":
                sys_msg = val
            elif role in ("human", "user"):
                user_msg = val
            elif role in ("gpt", "assistant"):
                gpt_msg = val

        prompt = (
            f"<|im_start|>system\n{sys_msg}<|im_end|>\n"
            f"<|im_start|>user\n{user_msg}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        full_text = f"{prompt}{gpt_msg}<|im_end|>"
        pairs.append((prompt, full_text))
    return pairs


def train():
    args = parse_args()
    logger.info("==========================================================================")
    logger.info("   SOVEREIGN GOTHAM // DIRECTML AMD RADEON RX 7600 XT NATIVE GPU CORE")
    logger.info("==========================================================================")

    import torch
    import torch_directml
    from peft import LoraConfig, get_peft_model
    from torch.utils.data import DataLoader
    from torch.utils.data import Dataset as TorchDataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, DataCollatorForSeq2Seq

    # 1. Detect and Bind to Dedicated AMD Radeon GPU (Device 1: RX 7600 XT)
    count = torch_directml.device_count()
    target_idx = 0
    for i in range(count):
        name = torch_directml.device_name(i)
        if "7600" in name or "RX" in name or "XT" in name:
            target_idx = i
            break
    if target_idx == 0 and count > 1:
        target_idx = count - 1

    device = torch_directml.device(target_idx)
    gpu_name = torch_directml.device_name(target_idx)
    logger.info(f"[+] Bound to Dedicated Accelerator: {gpu_name} (Device {target_idx})")

    # Status tracking file
    status_dir = Path(args.output_dir).parent if Path(args.output_dir).parent.exists() else Path(".")
    status_file = status_dir / "training_status.json"
    status = {
        "status": "CARREGANDO",
        "progress_pct": 0.0,
        "current_step": 0,
        "total_steps": 0,
        "epoch": 0,
        "total_epochs": args.epochs,
        "loss": 0.0,
        "loss_history": [],
        "elapsed_seconds": 0,
        "eta_seconds": 0,
        "vram_target": "14.0 GB",
        "gpu_name": gpu_name,
        "model_id": args.model_id,
        "dataset_samples": 0
    }

    # 2. Tokenizer & Dataset
    logger.info(f"Loading tokenizer for {args.model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    logger.info(f"Loading distilled dataset from {args.dataset_path}...")
    raw_data = load_dataset(args.dataset_path)
    status["dataset_samples"] = len(raw_data)
    formatted_texts = format_conversations(raw_data)
    logger.info(f"Loaded {len(formatted_texts)} formatted conversations for training.")

    class TextDataset(TorchDataset):
        def __init__(self, pairs: list[tuple[str, str]], tok, max_len: int = 4096):
            self.examples = []
            for prompt, full in pairs:
                p_enc = tok(prompt, add_special_tokens=False)
                prompt_len = len(p_enc["input_ids"])
                f_enc = tok(full, truncation=True, max_length=max_len)
                input_ids = f_enc["input_ids"]
                mask_len = min(prompt_len, len(input_ids))
                labels = [-100] * mask_len + input_ids[mask_len:]
                self.examples.append({
                    "input_ids": input_ids,
                    "labels": labels
                })

        def __len__(self):
            return len(self.examples)

        def __getitem__(self, idx):
            return self.examples[idx]

    train_ds = TextDataset(formatted_texts, tokenizer, args.max_seq_length)
    collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, pad_to_multiple_of=8, padding=True)
    loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collator)

    # 3. Load Model in Float16 and Move Directly to RX 7600 XT VRAM
    logger.info(f"Loading {args.model_id} in float16 into AMD Radeon RX 7600 XT VRAM...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )
    logger.info(f"Transferring weights to DirectML GPU device: {device} ...")
    model = model.to(device)
    model.gradient_checkpointing_enable()

    # 4. LoRA Adapters (Targeted Q, K, V, O Projections for High-Speed RX 7600 XT Stability)
    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 5. Optimizer (Targeting only trainable LoRA parameters to conserve VRAM)
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable_params, lr=args.lr)

    total_steps = (len(loader) // args.grad_accum) * args.epochs
    if args.max_steps > 0:
        total_steps = min(total_steps, args.max_steps)
    status["total_steps"] = total_steps
    status["status"] = "TREINANDO_GPU"
    status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")

    logger.info(f"[*] Starting DirectML GPU Training ({args.max_seq_length} Sequence Window): Total Batches={len(loader)}, Total Steps={total_steps}")
    start_time = time.time()
    global_step = 0
    loss_history = []

    model.train()
    optimizer.zero_grad()

    base_m = model.base_model.model if hasattr(model.base_model, 'model') else model.model

    for epoch in range(args.epochs):
        epoch_loss = 0.0
        for step, batch in enumerate(loader):
            batch.pop("attention_mask", None)
            batch = {k: v.to(device) for k, v in batch.items()}
            input_ids = batch["input_ids"]
            labels = batch["labels"]

            # Chunked LM-Head loss to guarantee 2048 sequence length on DirectML without DirectX 12 buffer overflow
            hidden_states = base_m.model(input_ids=input_ids).last_hidden_state
            shift_h = hidden_states[:, :-1, :]
            shift_l = labels[:, 1:]

            sample_loss = 0.0
            total_tokens = 0
            for i in range(0, shift_h.size(1), 512):
                hc = shift_h[:, i:i+512, :]
                lc = shift_l[:, i:i+512]
                valid_mask = (lc != -100)
                num_valid = int(valid_mask.sum().item())
                if num_valid > 0:
                    lc_logits = base_m.lm_head(hc)
                    closs = torch.nn.functional.cross_entropy(
                        lc_logits.view(-1, lc_logits.size(-1)),
                        lc.view(-1),
                        reduction="sum",
                        ignore_index=-100
                    )
                    sample_loss = sample_loss + closs
                    total_tokens += num_valid

            loss = (sample_loss / max(total_tokens, 1)) / args.grad_accum
            loss.backward()

            norm_loss = float(sample_loss.item() / max(total_tokens, 1))
            epoch_loss += norm_loss

            if (step + 1) % args.grad_accum == 0 or (step + 1) == len(loader):
                optimizer.step()
                optimizer.zero_grad()
                global_step += 1

                elapsed = int(time.time() - start_time)
                rate = elapsed / max(global_step, 1)
                remaining = max(total_steps - global_step, 0)
                eta = int(remaining * rate)
                pct = round((global_step / total_steps) * 100, 2)

                current_loss = round(norm_loss, 4)
                loss_history.append({"step": global_step, "loss": current_loss})

                logger.info(f"Epoch {epoch+1}/{args.epochs} | Step {global_step}/{total_steps} ({pct}%) | Loss: {current_loss} | ETA: {eta}s")

                status.update({
                    "progress_pct": pct,
                    "current_step": global_step,
                    "epoch": round(epoch + (step / len(loader)), 2),
                    "loss": current_loss,
                    "loss_history": loss_history[-30:],
                    "elapsed_seconds": elapsed,
                    "eta_seconds": eta,
                })
                try:
                    status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
                except Exception:
                    pass

                # Periodic checkpoint save
                if global_step % 100 == 0:
                    ckpt_dir = Path(args.output_dir) / f"checkpoint-{global_step}"
                    try:
                        from peft import get_peft_model_state_dict
                        lora_w = get_peft_model_state_dict(model)
                        cpu_lora = {k: v.cpu() for k, v in lora_w.items()}
                        ckpt_dir.mkdir(parents=True, exist_ok=True)
                        model.save_pretrained(str(ckpt_dir), state_dict=cpu_lora)
                        tokenizer.save_pretrained(str(ckpt_dir))
                        logger.info(f"[✓] Periodic checkpoint saved to: {ckpt_dir}")
                    except Exception as e:
                        logger.warning(f"Failed to save periodic checkpoint: {e}")

                if args.max_steps > 0 and global_step >= args.max_steps:
                    logger.info(f"[*] Reached target max_steps ({args.max_steps}). Finishing training loop.")
                    break

        if args.max_steps > 0 and global_step >= args.max_steps:
            break

    # Save final model adapter to Drive D:
    final_dir = Path(args.output_dir) / "final_adapter"
    final_dir.mkdir(parents=True, exist_ok=True)
    from peft import get_peft_model_state_dict
    lora_w = get_peft_model_state_dict(model)
    cpu_lora = {k: v.cpu() for k, v in lora_w.items()}
    model.save_pretrained(str(final_dir), state_dict=cpu_lora)
    tokenizer.save_pretrained(str(final_dir))

    # Consolidate into unified standalone model for instant inference
    unified_dir = Path("D:/sovereign_models/sovereign_gotham_universal_1.5b")
    logger.info(f"[*] Merging fine-tuned LoRA into unified standalone model at: {unified_dir} ...")
    try:
        cpu_model = model.to("cpu")
        merged_model = cpu_model.merge_and_unload()
        merged_model.save_pretrained(str(unified_dir), safe_serialization=True)
        tokenizer.save_pretrained(str(unified_dir))
        logger.info(f"[✓] Consolidated unified model saved successfully at: {unified_dir}")
    except Exception as e:
        logger.warning(f"Merge and unload note: {e}")

    status["status"] = "CONCLUÍDO"
    status["progress_pct"] = 100.0
    status["eta_seconds"] = 0
    status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")

    logger.info(f"[✓] DirectML GPU Fine-tuning Complete! Saved to: {final_dir}")


if __name__ == "__main__":
    train()
