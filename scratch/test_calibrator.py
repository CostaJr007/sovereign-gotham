import json
import re
import sys
from pathlib import Path
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("D:/sovereign_models/sovereign_gotham_universal_1.5b")

def calibrate_sample(sample_data):
    convs = sample_data["conversations"]
    sys_val = convs[0]["value"]
    user_val = convs[1]["value"]
    resp_val = convs[2]["value"]
    
    # Check if thought and json exist
    if "<thought>" not in resp_val or "</thought>" not in resp_val or "```json" not in resp_val:
        return None
        
    thought_match = re.search(r"<thought>(.*?)</thought>", resp_val, re.DOTALL)
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", resp_val, re.DOTALL)
    if not thought_match or not json_match:
        return None
        
    raw_thought = thought_match.group(1).strip()
    raw_json_str = json_match.group(1).strip()
    
    try:
        blueprint = json.loads(raw_json_str)
    except Exception:
        return None
        
    # Condense blueprint to essentials if needed
    if "palantir_objects" in blueprint and len(blueprint["palantir_objects"]) > 3:
        blueprint["palantir_objects"] = blueprint["palantir_objects"][:3]
    if "palantir_links" in blueprint and len(blueprint["palantir_links"]) > 3:
        blueprint["palantir_links"] = blueprint["palantir_links"][:3]
        
    # Split thought into agency sections
    paragraphs = [p.strip() for p in raw_thought.split("\n\n") if p.strip()]
    
    # Extract agency blocks (NSA, FBI, CIA, DOD)
    nsa_text = ""
    fbi_text = ""
    cia_text = ""
    dod_text = ""
    
    for p in paragraphs:
        p_low = p.lower()
        if ("nsa" in p_low or "triagem" in p_low) and not nsa_text:
            nsa_text = p
        elif ("fbi" in p_low or "forense" in p_low or "incentivo" in p_low) and not fbi_text:
            fbi_text = p
        elif ("cia" in p_low or "ach" in p_low or "hipótese" in p_low or "decepção" in p_low) and not cia_text:
            cia_text = p
        elif ("dod" in p_low or "exército" in p_low or "army" in p_low or "ooda" in p_low or "escalão" in p_low) and not dod_text:
            dod_text = p
            
    # Helper to condense paragraph to 2-3 key sentences
    def trim_paragraph(text, max_words=55):
        words = text.split()
        if len(words) <= max_words:
            return text
        # Keep first max_words and end on full stop
        truncated = " ".join(words[:max_words])
        if "." in truncated:
            truncated = truncated.rsplit(".", 1)[0] + "."
        else:
            truncated += "..."
        return truncated

    # Reconstruct thought
    nsa_clean = trim_paragraph(nsa_text or "1. Triagem de Sinais (NSA): Análise de telemetria isolando anomalias estatísticas e desacoplando subsistemas críticos.")
    fbi_clean = trim_paragraph(fbi_text or "2. Mapeamento Forense e Incentivos (FBI): Rastreamento de cadeias causais, identificação de conflitos e aplicação de preclusão procedimental.")
    cia_clean = trim_paragraph(cia_text or "3. Hipóteses Concorrentes e Decepção (CIA): Matriz ACH confrontando hipóteses diagnósticas e neutralizando vieses cognitivos de confirmação.")
    dod_clean = trim_paragraph(dod_text or "4. Ciclo OODA e Ações Faseadas (DoD/Exército): Execução escalonada com regras de engajamento restritas e critérios quantitativos de aborto.")
    
    # Ensure headings
    if not nsa_clean.startswith("1."): nsa_clean = "1. Triagem de Sinais e Telemetria (NSA):\n" + nsa_clean
    if not fbi_clean.startswith("2."): fbi_clean = "2. Mapeamento Forense e Incentivos (FBI):\n" + fbi_clean
    if not cia_clean.startswith("3."): cia_clean = "3. Hipóteses Concorrentes e Decepção (CIA):\n" + cia_clean
    if not dod_clean.startswith("4."): dod_clean = "4. Ciclo OODA e Ações Faseadas (DoD/Exército):\n" + dod_clean
    
    condensed_thought = f"<thought>\n{nsa_clean}\n\n{fbi_clean}\n\n{cia_clean}\n\n{dod_clean}\n</thought>"
    condensed_json = json.dumps(blueprint, indent=2, ensure_ascii=False)
    final_assistant = f"{condensed_thought}\n\n```json\n{condensed_json}\n```"
    
    # Measure full token length
    full_text = (
        f"<|im_start|>system\n{sys_val}<|im_end|>\n"
        f"<|im_start|>user\n{user_val}<|im_end|>\n"
        f"<|im_start|>assistant\n{final_assistant}<|im_end|>"
    )
    tokens = len(tok.encode(full_text))
    return {
        "conversations": [
            {"from": "system", "value": sys_val},
            {"from": "human", "value": user_val},
            {"from": "gpt", "value": final_assistant}
        ],
        "total_tokens": tokens
    }

# Test on first 3 PT samples
with open("training_data/sovereign_master_distilled.jsonl", "r", encoding="utf-8") as f:
    tested = 0
    for line in f:
        d = json.loads(line)
        if "Analise o seguinte" in d["conversations"][1]["value"]:
            cal = calibrate_sample(d)
            if cal:
                print(f"Sample {tested}: Total Tokens = {cal['total_tokens']}")
                print("Tail of response:")
                print(cal["conversations"][2]["value"][-200:])
                print("---")
                tested += 1
                if tested >= 3:
                    break
