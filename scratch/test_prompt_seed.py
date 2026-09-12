import sys
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_dir = "D:/sovereign_models/sovereign_gotham_universal_1.5b"
tokenizer = AutoTokenizer.from_pretrained(model_dir)

import torch_directml
device = torch_directml.device(1)

model = AutoModelForCausalLM.from_pretrained(
    model_dir,
    torch_dtype=torch.float32,
).to(device)
model.eval()

directive = """<|im_start|>system
You are Sovereign Gotham Universal Intelligence, governed by Palantir's Ontological Framework (Objects, Links, Actions - OLA) and the integrated tradecraft of the US Defense & Security Community:
1. NSA: Signal vs Noise Triage, Cold Telemetry & Decoupled Pipeline Allocation
2. FBI: Forensic Causal Mapping, Follow-The-Money & RICO Incentive Networks
3. CIA: Richards Heuer's Analysis of Competing Hypotheses (ACH) & Bias Mitigation
4. DoD / US Army: Boyd OODA Loop, Mission Command (Auftragstaktik) & Phased Courses of Action (COA)

Dissect any operational, business, or technical dilemma through all 4 agencies in <thought>...</thought> and output an auditable Palantir Action Blueprint in JSON format.<|im_end|>
<|im_start|>user
Diretiva de Missão Palantir Gotham [CORPORATE_STRATEGY]:
Analise o seguinte desafio operacional:
'Startup B2B sofreu queda de 45% no fluxo de caixa livre enquanto consumo de API subiu 300%'

[CONTEXTO ONTOLÓGICO PALANTIR - METODOLOGIAS REAIS DAS AGÊNCIAS]
{
  "domain": "CORPORATE_STRATEGY",
  "agency_doctrines": {
    "nsa": "Cookbook Demystification & Operational Capability Democratization Protocol",
    "fbi": "Asymmetric Dual-Track Forensic Inquest (Procedural Estoppel Vectoring)",
    "cia": "Cross-Echelon Divergence and Narrative Cadence Profiling",
    "dod_army": "Bounded Entitlement Gateway & Provenance-Enforced Channel Governance"
  }
}<|im_end|>
<|im_start|>assistant
<thought>
1. Triagem de Sinais e Telemetria (NSA):"""

inputs = tokenizer(directive, return_tensors="pt")
inputs = {k: v.to(device) for k, v in inputs.items()}

print("[*] Running generation test...")
outputs = model.generate(
    **inputs,
    max_new_tokens=400,
    do_sample=True,
    temperature=0.6,
    top_p=0.95,
    repetition_penalty=1.15,
)
text = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print("\n--- GENERATED CONTINUATION ---")
print("1. Triagem de Sinais e Telemetria (NSA):" + text)
