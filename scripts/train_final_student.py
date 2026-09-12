"""
Sovereign Gotham - Production Student Model Fine-Tuning & Evaluation Runner
Trains the DeepSeek-R1-Distill-Qwen-1.5B student model on the 3,124 curated distillation samples
using hardware-accelerated DirectML (DirectX 12) on the AMD Radeon RX 7600 XT (16 GB GDDR6).
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

try:
    _curr = Path(__file__).resolve()
    PROJECT_ROOT = _curr.parent.parent if _curr.parent.name == "scripts" else _curr.parent
except NameError:
    PROJECT_ROOT = Path(".").resolve()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from distillation.config import default_distill_config

logger = logging.getLogger("SovereignGotham.ProductionTrainer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Sovereign Gotham Production Training & Refine Runner")
    parser.add_argument("--epochs", type=int, default=2, help="Number of training epochs (default: 2)")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps (default: 4)")
    parser.add_argument("--lr", type=float, default=1.8e-4, help="Learning rate (default: 1.8e-4)")
    parser.add_argument("--shutdown", action="store_true", help="Shut down PC after training and evaluation completes")
    args = parser.parse_args()

    config = default_distill_config
    dataset_path = config.curated_dataset_path
    output_dir = config.student_output_dir
    telemetry_dir = config.storage_root / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    report_file = telemetry_dir / "final_production_training_report.json"

    logger.info("==========================================================================")
    logger.info("   SOVEREIGN GOTHAM // PRODUCTION DIRECTML TRAINING & REFINEMENT")
    logger.info("==========================================================================")
    logger.info(f"Target Dataset: {dataset_path}")
    logger.info(f"Hardware: {config.gpu_name} (DirectML Device 1)")
    logger.info(f"Hyperparameters: Epochs={args.epochs} | GradAccum={args.grad_accum} | LR={args.lr}")
    logger.info(f"Output Adapter: {output_dir}")
    logger.info(f"Auto-Shutdown: {'ENABLED' if args.shutdown else 'DISABLED'}")

    if not dataset_path.exists():
        logger.error(f"Dataset file not found: {dataset_path}")
        sys.exit(1)

    sample_count = len([l for l in dataset_path.read_text(encoding="utf-8").splitlines() if l.strip()])
    logger.info(f"Total Verified Training Samples: {sample_count}")

    # 1. RUN TRAINING
    train_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "distillation" / "train_student.py"),
        "--dataset", str(dataset_path),
        "--output_dir", str(output_dir),
        "--epochs", str(args.epochs),
        "--grad_accum", str(args.grad_accum),
        "--lr", str(args.lr),
    ]

    t_start = time.time()
    logger.info("[*] Launching DirectML training loop on AMD Radeon RX 7600 XT...")
    proc = subprocess.run(train_cmd, cwd=str(PROJECT_ROOT))
    train_duration = time.time() - t_start

    if proc.returncode != 0:
        logger.error(f"[X] Training process failed with code {proc.returncode}")
        sys.exit(proc.returncode)

    logger.info(f"[✓] Training phase completed successfully in {train_duration:.1f}s ({train_duration/60:.1f} min)!")

    # 2. RUN COGNITIVE EVALUATION & BENCHMARK
    logger.info("==========================================================================")
    logger.info("   PHASE 2: COGNITIVE BENCHMARK & REASONING VERIFICATION")
    logger.info("==========================================================================")
    eval_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "distillation" / "evaluate_student.py"),
    ]
    subprocess.run(eval_cmd, cwd=str(PROJECT_ROOT))

    # 3. SAVE PRODUCTION REPORT
    report_data = {
        "status": "COMPLETED",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_samples": sample_count,
        "epochs": args.epochs,
        "grad_accum": args.grad_accum,
        "lr": args.lr,
        "training_duration_seconds": round(train_duration, 1),
        "training_duration_minutes": round(train_duration / 60, 2),
        "hardware": config.gpu_name,
        "adapter_location": str(output_dir),
    }
    report_file.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    logger.info(f"[✓] Production training report saved to: {report_file}")

    if args.shutdown:
        logger.warning("\n[!] Auto-shutdown requested. System will shut down in 120 seconds.")
        logger.warning("[!] To cancel, run: shutdown /a in terminal.\n")
        subprocess.run(["shutdown", "/s", "/t", "120", "/c", "Sovereign Gotham: Treinamento e Refino Concluidos! Desligando em 2 minutos."])


if __name__ == "__main__":
    main()
