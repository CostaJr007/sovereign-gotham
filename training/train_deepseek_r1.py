"""
Sovereign Gotham - DeepSeek-R1-Distill-Qwen-7B QLoRA Fine-Tuning Pipeline
Trains the Unified Sovereign Intelligence Agent on local GPU (AMD Radeon RX 7600 XT 16GB / DirectML / ROCm / CUDA).
Integrates with HuggingFace TRL/Transformers, PEFT (QLoRA), DataCollatorForSeq2Seq, and live real-time progress callbacks.
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

logger = logging.getLogger("SovereignGotham.Trainer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune DeepSeek-R1-Distill-Qwen-7B for Sovereign Gotham")
    parser.add_argument(
        "--model_id",
        type=str,
        default="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        help="HuggingFace model ID or local path to base model weights",
    )
    parser.add_argument(
        "--dataset_path",
        type=str,
        default="training_data/sovereign_deepseek_r1_agent.jsonl",
        help="Path to consolidated instruction dataset JSONL",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="D:/sovereign_models/deepseek_r1_sovereign_agent" if Path("D:/").exists() else "./models/deepseek_r1_sovereign_agent",
        help="Output directory for fine-tuned LoRA adapters and model checkpoints",
    )
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--vram_target", type=str, default="14gb", choices=["8gb", "10gb", "14gb"], help="VRAM target allocation profile")
    parser.add_argument("--batch_size", type=int, default=4, help="Per-device batch size (set to 4 for 14GB target)")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--max_seq_length", type=int, default=4096, help="Maximum sequence length (4096 for deep context)")
    parser.add_argument("--lora_r", type=int, default=64, help="LoRA rank (64 for maximum intelligence)")
    parser.add_argument("--lora_alpha", type=int, default=128, help="LoRA scaling factor")
    parser.add_argument("--lora_dropout", type=float, default=0.05, help="LoRA dropout rate")
    return parser.parse_args()


def load_jsonl_dataset(file_path: str | Path) -> list[dict[str, Any]]:
    """Loads ShareGPT formatted training lines from JSONL."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}. Run 'python cli.py generate-datasets' first.")

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                records.append(json.loads(line_str))

    logger.info(f"Loaded {len(records)} training samples from {path}")
    return records


def format_conversations_for_training(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    """
    Transforms ShareGPT multi-turn conversations into unified prompt-response text
    adhering strictly to DeepSeek-R1's prompt template:
    <|im_start|>system\n{sys}<|im_end|>\n<|im_start|>user\n{usr}<|im_end|>\n<|im_start|>assistant\n{asst}<|im_end|>
    """
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


def get_status_file(output_dir: str) -> Path:
    out = Path(output_dir)
    parent = out.parent if out.parent.exists() else Path("D:/sovereign_models") if Path("D:/").exists() else Path("./models")
    parent.mkdir(parents=True, exist_ok=True)
    return parent / "training_status.json"


def train():
    args = parse_args()
    logger.info("==========================================================================")
    logger.info("     SOVEREIGN GOTHAM // DEEPSEEK-R1-DISTILL-QWEN-7B FINE-TUNING")
    logger.info("==========================================================================")
    logger.info(f"Target Model: {args.model_id}")
    logger.info(f"Dataset Path: {args.dataset_path}")
    logger.info(f"Output Directory: {args.output_dir}")
    logger.info(f"Hyperparameters: Epochs={args.epochs}, BatchSize={args.batch_size}, GradAccum={args.grad_accum}, LoRA_R={args.lora_r}")

    status_file = get_status_file(args.output_dir)

    # Initial status
    initial_status = {
        "status": "CARREGANDO_MODELO",
        "progress_pct": 0.0,
        "current_step": 0,
        "total_steps": 1000,
        "epoch": 0.0,
        "total_epochs": args.epochs,
        "loss": None,
        "loss_history": [],
        "elapsed_seconds": 0,
        "eta_seconds": 0,
        "vram_target": f"{args.vram_target.upper()}",
        "gpu_name": "AMD Radeon RX 7600 XT (16 GB)",
        "model_id": args.model_id,
        "dataset_samples": 0,
    }
    status_file.write_text(json.dumps(initial_status, indent=2), encoding="utf-8")

    # Check dependencies
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            DataCollatorForSeq2Seq,
            TrainerCallback,
        )
    except ImportError as e:
        logger.error(f"Missing required training dependencies: {e}")
        sys.exit(1)

    # Detect AMD GPU DirectML / CUDA accelerator
    dml_device = None
    try:
        import torch_directml
        if torch_directml.is_available():
            dml_device = torch_directml.device()
            logger.info(f"[+] AMD Radeon GPU DirectML acceleration active: {dml_device}")
    except Exception:
        pass

    # 1. Load and format dataset
    raw_records = load_jsonl_dataset(args.dataset_path)
    train_data = format_conversations_for_training(raw_records)
    hf_dataset = Dataset.from_list(train_data)
    initial_status["dataset_samples"] = len(train_data)
    status_file.write_text(json.dumps(initial_status, indent=2), encoding="utf-8")

    # 2. Tokenizer
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 3. Quantization Configuration
    bnb_config = None
    try:
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        logger.info("Configured 4-bit BitsAndBytes NF4 quantization.")
    except Exception as e:
        logger.info(f"BitsAndBytes not available ({e}); using float16 precision.")

    # 4. Load Base Model
    logger.info(f"Loading base model {args.model_id} (authenticated via Hugging Face token)...")
    device_map = "auto" if torch.cuda.is_available() else None
    torch_dtype = torch.float16 if (torch.cuda.is_available() or dml_device is not None) else torch.float32

    model_kwargs = {
        "trust_remote_code": True,
        "dtype": torch_dtype,
    }
    if bnb_config:
        model_kwargs["quantization_config"] = bnb_config
    if device_map:
        model_kwargs["device_map"] = device_map

    model = AutoModelForCausalLM.from_pretrained(args.model_id, **model_kwargs)

    if dml_device is not None:
        try:
            logger.info("Moving model weights to AMD Radeon DirectML GPU device...")
            model = model.to(dml_device)
        except Exception as ex:
            logger.warning(f"DirectML device transfer notice: {ex}")

    try:
        from peft import prepare_model_for_kbit_training
        if bnb_config:
            model = prepare_model_for_kbit_training(model)
    except Exception:
        pass

    # 5. LoRA Configuration (Rank 64 for 14GB VRAM High-Performance)
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=target_modules,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 6. Real-Time Training Progress Callback
    class LiveProgressCallback(TrainerCallback):
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
                "status": "TREINANDO",
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

    # 7. Training Execution with Dynamic Padding Data Collator
    try:
        from transformers import Trainer, TrainingArguments

        training_args = TrainingArguments(
            output_dir=args.output_dir,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=args.grad_accum,
            learning_rate=args.lr,
            logging_steps=5,
            save_strategy="epoch",
            fp16=torch.cuda.is_available(),
            dataloader_pin_memory=False,
            dataloader_num_workers=0,
            warmup_steps=10,
            lr_scheduler_type="cosine",
            report_to="none",
        )

        def tokenize_fn(batch):
            tokenized = tokenizer(batch["text"], truncation=True, max_length=args.max_seq_length)
            tokenized["labels"] = [list(ids) for ids in tokenized["input_ids"]]
            return tokenized

        tokenized_dataset = hf_dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

        # Dynamic padding collator to handle variable sequence lengths seamlessly
        data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, pad_to_multiple_of=8, padding=True)

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
            callbacks=[LiveProgressCallback(status_file, args.epochs)],
        )

        logger.info("Starting fine-tuning with live monitoring...")
        trainer.train()

        # Save fine-tuned adapter
        final_save_path = Path(args.output_dir) / "final_adapter"
        trainer.model.save_pretrained(final_save_path)
        tokenizer.save_pretrained(final_save_path)
        logger.info(f"[✓] Sovereign Intelligence Agent successfully trained and saved to: {final_save_path}")

    except Exception as ex:
        logger.error(f"Training loop failed: {ex}")
        raise ex


if __name__ == "__main__":
    train()
