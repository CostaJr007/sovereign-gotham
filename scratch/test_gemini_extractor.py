"""
Sovereign Gotham - Test Real Document Extraction via Gemini (AGY CLI)
Reads an authentic NSA Cryptolog document and asks Gemini to extract the operational methodology.
"""

import json
import subprocess
import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

def test_extraction():
    nsa_file = Path("D:/sovereign_gotham_data/nsa/cryptolog_03.txt")
    if not nsa_file.exists():
        print("NSA file not found.")
        return

    content = nsa_file.read_text(encoding="utf-8", errors="ignore")[:2500]

    prompt = (
        "You are Sovereign Gotham Chief Ontologist.\n"
        "Analyze this authentic declassified NSA technical document excerpt:\n"
        "----------------------------------------\n"
        f"{content}\n"
        "----------------------------------------\n"
        "Your task:\n"
        "1. Extract the operational PROBLEM-SOLVING METHODOLOGY / WORKFLOW embedded in this text (not historical trivia, but the actual technical method of signal analysis, traffic analysis, or problem decomposition).\n"
        "2. Formulate a real-world corporate or technical problem where this exact NSA method solves the problem.\n"
        "3. Output a structured JSON containing:\n"
        "   - agency: 'NSA'\n"
        "   - method_name: 'Name of the extracted methodology'\n"
        "   - core_algorithm_steps: [Step 1, Step 2, Step 3]\n"
        "   - real_world_application: 'Description of application to modern business/tech'\n"
        "Output valid JSON inside a ```json ... ``` block."
    )

    print("[*] Calling Gemini (AGY CLI) to extract methodology from real NSA document...")
    res = subprocess.run(
        ["agy", "--model", "gemini-3.8-flash-high", "-p", prompt],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    print("\n--- GEMINI EXTRACTION OUTPUT ---")
    print(res.stdout)

if __name__ == "__main__":
    test_extraction()
