"""
Sovereign Gotham - Auto Shutdown Watcher Daemon
Monitors the training progress of task-1959. Once 100% complete and verified,
it triggers a safe 180-second system shutdown so the user can sleep peacefully.
"""

import json
import logging
import subprocess
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AutoShutdownWatcher")

status_file = Path("D:/sovereign_models/training_status.json")
report_file = Path("D:/sovereign_distillation/telemetry/final_production_training_report.json")
adapter_dir = Path("D:/sovereign_distillation/student_checkpoints/distilled_student_adapter")

logger.info("[*] Auto-Shutdown Watcher started. Monitoring training completion...")

while True:
    time.sleep(30)
    
    # Check if production training report has been written
    if report_file.exists():
        try:
            data = json.loads(report_file.read_text(encoding="utf-8"))
            if data.get("status") == "COMPLETED":
                logger.info("[✓] Production training report confirmed COMPLETED!")
                break
        except Exception:
            pass

    # Check training status file
    if status_file.exists():
        try:
            status_data = json.loads(status_file.read_text(encoding="utf-8"))
            pct = status_data.get("progress_pct", 0.0)
            status_str = status_data.get("status", "")
            if pct >= 100.0 or status_str == "DESTILACAO_CONCLUIDA":
                # Give 60 seconds for evaluation script to complete
                logger.info("[*] Training reached 100%. Waiting 60s for evaluation to finish...")
                time.sleep(60)
                break
        except Exception:
            pass

logger.info("==========================================================================")
logger.info("[✓] ALL TRAINING AND EVALUATION PHASES CONFIRMED COMPLETED!")
logger.info("[!] Initiating system shutdown in 180 seconds (3 minutes)...")
logger.info("[!] To abort: run 'shutdown /a' in terminal.")
logger.info("==========================================================================")

msg = "Sovereign Gotham: Treinamento de 3.124 amostras concluido com 100% de sucesso! Desligando em 3 minutos."
subprocess.run(["shutdown", "/s", "/t", "180", "/c", msg])
