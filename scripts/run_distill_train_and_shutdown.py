"""
Sovereign Gotham - Autonomous Distillation, Training, & PC Shutdown Orchestrator
Automates the full pipeline:
  1. Distills CIA/DoD intelligence reports up to the target sample count (e.g. 250).
  2. Executes student SLM fine-tuning on the AMD Radeon RX 7600 XT via DirectML.
  3. Evaluates cognitive reasoning depth (<thought> tags & ROE compliance).
  4. Shuts down the PC safely with a 120-second abort window.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
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

logger = logging.getLogger("SovereignGotham.AutoShutdown")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_dataset_count(dataset_path: Path) -> int:
    """Returns the current number of valid lines/samples in the master dataset."""
    if not dataset_path.exists():
        return 0
    try:
        return len([line for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()])
    except Exception as e:
        logger.warning(f"Could not read dataset: {e}")
        return 0


def kill_existing_distillation_processes():
    """Terminates any background pipeline.py process so training can take the GPU."""
    try:
        # On Windows, find and kill python processes running pipeline.py
        cmd = 'wmic process where "CommandLine like \'%distillation/pipeline.py%\' and not CommandLine like \'%wmic%\'" get ProcessId'
        out = subprocess.check_output(cmd, shell=True, text=True, errors="ignore")
        pids = [line.strip() for line in out.splitlines() if line.strip().isdigit()]
        for pid in pids:
            if int(pid) != os.getpid():
                logger.info(f"Terminating background distillation process PID: {pid}...")
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
    except Exception as e:
        logger.debug(f"Process cleanup notice: {e}")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Distillation, Training, & PC Shutdown Orchestrator")
    parser.add_argument("--target", type=int, default=250, help="Target total samples in master dataset (default: 250)")
    parser.add_argument("--epochs", type=int, default=4, help="Student training epochs (default: 4)")
    parser.add_argument("--grad_accum", type=int, default=2, help="Gradient accumulation steps (default: 2)")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate (default: 2e-4)")
    parser.add_argument("--shutdown_delay", type=int, default=120, help="Shutdown warning countdown in seconds (default: 120)")
    parser.add_argument("--no_shutdown", action="store_true", help="Do not shut down PC after completion (for testing)")
    args = parser.parse_args()

    config = default_distill_config
    dataset_path = config.curated_dataset_path
    telemetry_dir = config.storage_root / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    summary_file = telemetry_dir / "overnight_execution_summary.json"

    logger.info("==========================================================================")
    logger.info("   SOVEREIGN GOTHAM // AUTONOMOUS ORCHESTRATOR & AUTO-SHUTDOWN")
    logger.info("==========================================================================")
    logger.info(f"Target Master Dataset: {args.target} samples")
    logger.info(f"Student Training Epochs: {args.epochs}")
    logger.info(f"Hardware Target: {config.gpu_name} (DirectML)")
    logger.info(f"Auto-Shutdown: {'DISABLED (--no_shutdown)' if args.no_shutdown else f'ENABLED ({args.shutdown_delay}s delay)'}")

    # ---------------------------------------------------------
    # STEP 1: MONITOR OR RUN DISTILLATION UP TO TARGET
    # ---------------------------------------------------------
    current_count = get_dataset_count(dataset_path)
    logger.info(f"Current Master Dataset Samples: {current_count} / {args.target}")

    start_orchestration = time.time()

    if current_count < args.target:
        logger.info(f"[*] Attaching to distillation stream. Waiting for {args.target - current_count} more samples...")

        while current_count < args.target:
            time.sleep(10)
            current_count = get_dataset_count(dataset_path)
            rem = max(0, args.target - current_count)
            logger.info(f"[Distillation Progress] Master Dataset: {current_count}/{args.target} samples (Remaining: {rem})")

        logger.info(f"[✓] Target of {args.target} samples successfully achieved!")

    # Stop any background distillation process cleanly before training
    logger.info("[*] Halting distillation stream to dedicate 100% GPU VRAM to DirectML training...")
    kill_existing_distillation_processes()
    time.sleep(3)

    # ---------------------------------------------------------
    # STEP 2: TRAIN STUDENT MODEL ON AMD RADEON RX 7600 XT
    # ---------------------------------------------------------
    logger.info("==========================================================================")
    logger.info("   PHASE 2: DIRECTML STUDENT TRAINING (AMD RADEON RX 7600 XT)")
    logger.info("==========================================================================")
    train_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "distillation" / "train_student.py"),
        "--epochs", str(args.epochs),
        "--grad_accum", str(args.grad_accum),
        "--lr", str(args.lr),
    ]

    t_train_start = time.time()
    train_proc = subprocess.run(train_cmd, cwd=str(PROJECT_ROOT))
    t_train_duration = time.time() - t_train_start

    if train_proc.returncode != 0:
        logger.error(f"[X] Training failed with return code {train_proc.returncode}. Aborting shutdown for inspection.")
        return

    logger.info(f"[✓] Student model training successfully completed in {t_train_duration:.1f}s!")

    # ---------------------------------------------------------
    # STEP 3: EVALUATION & BENCHMARK
    # ---------------------------------------------------------
    logger.info("==========================================================================")
    logger.info("   PHASE 3: COGNITIVE BENCHMARK & ADAPTER EVALUATION")
    logger.info("==========================================================================")
    eval_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "distillation" / "evaluate_student.py"),
    ]
    subprocess.run(eval_cmd, cwd=str(PROJECT_ROOT))

    # Record final summary
    total_duration = time.time() - start_orchestration
    summary_data = {
        "status": "COMPLETED",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target_samples": args.target,
        "final_dataset_samples": get_dataset_count(dataset_path),
        "training_epochs": args.epochs,
        "training_duration_seconds": round(t_train_duration, 1),
        "total_orchestration_duration_minutes": round(total_duration / 60, 2),
        "hardware": config.gpu_name,
        "output_adapter": str(config.student_output_dir),
    }
    summary_file.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
    logger.info(f"[✓] Execution summary written to: {summary_file}")

    # ---------------------------------------------------------
    # STEP 4: SYSTEM SHUTDOWN
    # ---------------------------------------------------------
    logger.info("==========================================================================")
    logger.info("   PIPELINE FINISHED SUCCESSFULLY! PREPARING SHUTDOWN")
    logger.info("==========================================================================")

    if args.no_shutdown:
        logger.info("[!] Flag --no_shutdown active. System will remain powered on.")
        return

    msg = (
        f"Sovereign Gotham: Distilacao e Treino Concluidos ({args.target} amostras)! "
        f"Desligando o computador em {args.shutdown_delay} segundos. "
        f"Para cancelar, execute no terminal: shutdown /a"
    )
    logger.warning(f"\n[!] SHUTTING DOWN SYSTEM IN {args.shutdown_delay} SECONDS!")
    logger.warning("[!] To CANCEL shutdown at any time, run: shutdown /a in PowerShell/CMD\n")

    shutdown_cmd = [
        "shutdown",
        "/s",
        "/t", str(args.shutdown_delay),
        "/c", msg,
    ]
    subprocess.run(shutdown_cmd)


if __name__ == "__main__":
    main()
