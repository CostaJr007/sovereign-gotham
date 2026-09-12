"""
Sovereign Gotham - Calibrated Dataset Builder (1024-Token Certified)
Condenses and formats authentic agency methodologies and multi-agency reasoning traces
to guarantee 100% completion within the 1024-token DirectML GPU training window.
Eliminates all archive references; focuses purely on project methodology & OLA ontology.
"""

import json
import re
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from pathlib import Path
from transformers import AutoTokenizer

_CURRENT_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
PROJECT_ROOT = _CURRENT_DIR.parent if (_CURRENT_DIR.parent / "pyproject.toml").exists() else _CURRENT_DIR

tok = AutoTokenizer.from_pretrained("D:/sovereign_models/sovereign_gotham_universal_1.5b")

SYSTEM_DIRECTIVE = (
    "You are Sovereign Gotham Universal Intelligence, governed by Palantir's Ontological Framework "
    "(Objects, Links, Actions - OLA) and the integrated tradecraft of the US Defense & Security Community:\n"
    "1. NSA: Signal vs Noise Triage, Cold Telemetry & Decoupled Pipeline Allocation\n"
    "2. FBI: Forensic Causal Mapping, Follow-The-Money & RICO Incentive Networks\n"
    "3. CIA: Richards Heuer's Analysis of Competing Hypotheses (ACH) & Bias Mitigation\n"
    "4. DoD / US Army: Boyd OODA Loop, Mission Command (Auftragstaktik) & Phased Courses of Action (COA)\n\n"
    "Dissect any operational, business, or technical dilemma through all 4 agencies in <thought>...</thought> "
    "and output an auditable Palantir Action Blueprint in JSON format."
)


def trim_sentences(text: str, max_words: int = 50) -> str:
    """Trims text to approximately max_words ending at a complete sentence."""
    words = text.strip().split()
    if len(words) <= max_words:
        return text.strip()
    truncated = " ".join(words[:max_words])
    if "." in truncated:
        return truncated.rsplit(".", 1)[0] + "."
    return truncated + "."


def process_sample(record: dict) -> dict | None:
    convs = record.get("conversations", [])
    if len(convs) < 3:
        return None

    user_val = convs[1].get("value", "")
    resp_val = convs[2].get("value", "")

    # Only process Portuguese project challenges
    if "Analise o seguinte" not in user_val and "Diretiva de Missão" not in user_val:
        return None

    if "<thought>" not in resp_val or "```json" not in resp_val:
        return None

    thought_match = re.search(r"<thought>(.*?)(?:</thought>|```json)", resp_val, re.DOTALL)
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", resp_val, re.DOTALL)

    if not thought_match or not json_match:
        return None

    raw_thought = thought_match.group(1).strip()
    raw_json_str = json_match.group(1).strip()

    try:
        blueprint = json.loads(raw_json_str)
    except Exception:
        return None

    # Compact JSON to 2 essential objects and 2 links to leave space for dense thought
    if "palantir_objects" in blueprint and len(blueprint["palantir_objects"]) > 2:
        blueprint["palantir_objects"] = blueprint["palantir_objects"][:2]
    if "palantir_links" in blueprint and len(blueprint["palantir_links"]) > 2:
        blueprint["palantir_links"] = blueprint["palantir_links"][:2]

    # Clean action execution text
    actions = blueprint.get("palantir_action_execution", {})
    if isinstance(actions, dict):
        for k in ["phase_1_t24h", "phase_2_t7d", "phase_3_t30d", "abort_criteria"]:
            if k in actions and isinstance(actions[k], str):
                actions[k] = trim_sentences(actions[k], max_words=30)
        if "rules_of_engagement" in actions and isinstance(actions["rules_of_engagement"], list):
            actions["rules_of_engagement"] = [trim_sentences(r, max_words=20) for r in actions["rules_of_engagement"][:2]]

    # Parse thought paragraphs
    sections = re.split(r"\n(?=\d+\.|\#\#\#)", raw_thought)
    nsa_text, fbi_text, cia_text, dod_text = "", "", "", ""

    for s in sections:
        s_clean = s.strip()
        s_low = s_clean.lower()
        if ("nsa" in s_low or "triagem" in s_low) and not nsa_text:
            # Strip header if present
            content = re.sub(r"^(\d+\.|\#\#\#\s*\d*\.?)\s*[^\n]+\n?", "", s_clean).strip()
            nsa_text = content or s_clean
        elif ("fbi" in s_low or "forense" in s_low or "incentivo" in s_low) and not fbi_text:
            content = re.sub(r"^(\d+\.|\#\#\#\s*\d*\.?)\s*[^\n]+\n?", "", s_clean).strip()
            fbi_text = content or s_clean
        elif ("cia" in s_low or "ach" in s_low or "hipótese" in s_low or "decepção" in s_low) and not cia_text:
            content = re.sub(r"^(\d+\.|\#\#\#\s*\d*\.?)\s*[^\n]+\n?", "", s_clean).strip()
            cia_text = content or s_clean
        elif ("dod" in s_low or "exército" in s_low or "army" in s_low or "ooda" in s_low or "escalão" in s_low) and not dod_text:
            content = re.sub(r"^(\d+\.|\#\#\#\s*\d*\.?)\s*[^\n]+\n?", "", s_clean).strip()
            dod_text = content or s_clean

    nsa_p = trim_sentences(nsa_text or "Isolamento de telemetria objetiva e identificação de anomalias estatísticas com desacoplamento de fluxo operacional.", max_words=45)
    fbi_p = trim_sentences(fbi_text or "Rastreamento causal de incentivos assimétricos, mapeamento de conflitos de interesse e imposição de preclusão procedimental.", max_words=45)
    cia_p = trim_sentences(cia_text or "Avaliação pela Matriz ACH de Richards Heuer confrontando premissas operacionais com evidências diagnósticas refutatórias.", max_words=45)
    dod_p = trim_sentences(dod_text or "Ciclo OODA e comando de missão escalonado com regras de engajamento invioláveis e critérios quantitativos de aborto.", max_words=45)

    thought_block = (
        f"<thought>\n"
        f"1. Triagem de Sinais e Telemetria (NSA):\n{nsa_p}\n\n"
        f"2. Mapeamento Forense e Incentivos (FBI):\n{fbi_p}\n\n"
        f"3. Hipóteses Concorrentes e Decepção (CIA):\n{cia_p}\n\n"
        f"4. Ciclo OODA e Ações Faseadas (DoD/Exército):\n{dod_p}\n"
        f"</thought>"
    )

    json_block = f"```json\n{json.dumps(blueprint, indent=2, ensure_ascii=False)}\n```"
    final_assistant = f"{thought_block}\n\n{json_block}"

    # Trim user_val if overly verbose
    clean_user = user_val
    if "[CONTEXTO ONTOLÓGICO PALANTIR" in user_val:
        parts = user_val.split("[CONTEXTO ONTOLÓGICO PALANTIR")
        dilemma_part = parts[0].strip()
        context_part = "[CONTEXTO ONTOLÓGICO PALANTIR" + parts[1]
        # Keep dilemma to ~80 words
        lines = dilemma_part.split("\n")
        header = lines[0]
        prob_body = "\n".join(lines[1:])
        prob_trimmed = trim_sentences(prob_body, max_words=80)
        clean_user = f"{header}\n{prob_trimmed}\n\n{context_part}"

    full_formatted = (
        f"<|im_start|>system\n{SYSTEM_DIRECTIVE}<|im_end|>\n"
        f"<|im_start|>user\n{clean_user}<|im_end|>\n"
        f"<|im_start|>assistant\n{final_assistant}<|im_end|>"
    )

    total_tokens = len(tok.encode(full_formatted))
    if total_tokens > 1020:
        # If still slightly above, trim thought slightly more
        nsa_p = trim_sentences(nsa_p, max_words=35)
        fbi_p = trim_sentences(fbi_p, max_words=35)
        cia_p = trim_sentences(cia_p, max_words=35)
        dod_p = trim_sentences(dod_p, max_words=35)
        thought_block = (
            f"<thought>\n"
            f"1. Triagem de Sinais e Telemetria (NSA):\n{nsa_p}\n\n"
            f"2. Mapeamento Forense e Incentivos (FBI):\n{fbi_p}\n\n"
            f"3. Hipóteses Concorrentes e Decepção (CIA):\n{cia_p}\n\n"
            f"4. Ciclo OODA e Ações Faseadas (DoD/Exército):\n{dod_p}\n"
            f"</thought>"
        )
        final_assistant = f"{thought_block}\n\n{json_block}"
        full_formatted = (
            f"<|im_start|>system\n{SYSTEM_DIRECTIVE}<|im_end|>\n"
            f"<|im_start|>user\n{clean_user}<|im_end|>\n"
            f"<|im_start|>assistant\n{final_assistant}<|im_end|>"
        )
        total_tokens = len(tok.encode(full_formatted))

    if total_tokens > 1024:
        return None

    return {
        "conversations": [
            {"from": "system", "value": SYSTEM_DIRECTIVE},
            {"from": "human", "value": clean_user},
            {"from": "gpt", "value": final_assistant},
        ],
        "token_count": total_tokens,
    }


def main():
    src_file = PROJECT_ROOT / "training_data" / "sovereign_master_distilled.jsonl"
    dst_file = PROJECT_ROOT / "training_data" / "sovereign_calibrated_1024.jsonl"

    if not src_file.exists():
        print(f"[-] Source file not found: {src_file}")
        sys.exit(1)

    print(f"[*] Processing {src_file} -> {dst_file} ...")
    valid_records = []
    token_lengths = []

    with open(src_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                cal = process_sample(rec)
                if cal:
                    valid_records.append({"conversations": cal["conversations"]})
                    token_lengths.append(cal["token_count"])
            except Exception:
                pass

    print(f"[✓] Generated {len(valid_records)} calibrated samples!")
    if token_lengths:
        print(f"    * Min Tokens: {min(token_lengths)}")
        print(f"    * Avg Tokens: {sum(token_lengths)/len(token_lengths):.1f}")
        print(f"    * Max Tokens: {max(token_lengths)} (Under 1024 Limit!)")

    with open(dst_file, "w", encoding="utf-8") as f:
        for r in valid_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[✓] Saved calibrated dataset to: {dst_file}")


if __name__ == "__main__":
    main()
