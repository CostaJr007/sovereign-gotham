"""
Sovereign Gotham - Live Reasoning Streamer & Monitor
Follows D:/sovereign_distillation/curated_dataset/distilled_sovereign_r1.jsonl
and streams newly generated teacher/student reasoning traces in real-time.
"""

import json
import sys
import time
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DATASET_PATH = Path("D:/sovereign_distillation/curated_dataset/distilled_sovereign_r1.jsonl")


def stream_reasoning():
    print("==========================================================================")
    print("   SOVEREIGN GOTHAM // LIVE DISTILLATION REASONING STREAM")
    print("==========================================================================")
    print(f"[*] Monitoring: {DATASET_PATH}")
    print("[*] Waiting for newly distilled intelligence traces... (Ctrl+C to stop)\n")

    last_pos = 0
    if DATASET_PATH.exists():
        last_pos = DATASET_PATH.stat().st_size

    try:
        while True:
            if not DATASET_PATH.exists():
                time.sleep(1)
                continue

            current_size = DATASET_PATH.stat().st_size
            if current_size > last_pos:
                with open(DATASET_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(last_pos)
                    new_lines = f.readlines()
                    last_pos = f.tell()

                for line in new_lines:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        data = json.loads(line_str)
                        convs = data.get("conversations", [])
                        human_msg = convs[1]["value"] if len(convs) > 1 else ""
                        assistant_msg = convs[2]["value"] if len(convs) > 2 else ""

                        # Extract doc title or query
                        first_line = human_msg.splitlines()[0] if human_msg else "NO_PROMPT"

                        print("\n" + "=" * 74)
                        print(f"📡 [NOVA ANÁLISE DESTILADA]: {first_line[:70]}...")
                        print("=" * 74)
                        print(assistant_msg)
                        print("-" * 74 + "\n")
                    except Exception:
                        pass
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Monitor finalizado.")


if __name__ == "__main__":
    stream_reasoning()
