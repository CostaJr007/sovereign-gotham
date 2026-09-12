"""
Sovereign Gotham - Gemini Organic Cognitive Distillation Engine (CIA + DoD Dual-Core)
Teacher Engine: Gemini (via AGY CLI)
Student Target: DeepSeek-R1-Distill (DirectML on AMD Radeon RX 7600 XT)

Grounds Gemini in:
1. Palantir Dynamic Ontology (Objects, Links, Actions - OLA)
2. Authentic CIA (Analysis of Competing Hypotheses, Estimative Intelligence)
3. Authentic DoD / US Army (Boyd OODA Loop, Mission Command / Auftragstaktik)
4. 12 High-Stakes Operational Problem Domains (100% Native English)

Generates bespoke, unscripted, human-grade strategic reasoning and valid Palantir Action Blueprints.
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import random
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

logger = logging.getLogger("SovereignGotham.GeminiOrganicDistiller")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

PALANTIR_CIA_DOD_SYSTEM_PROMPT = (
    "You are Sovereign Gotham Universal Intelligence, an operational intelligence and decision engine "
    "governed by Palantir's Dynamic Ontological Framework (Objects, Links, Actions - OLA) "
    "and the integrated dual-core tradecraft of the US National Security Apparatus:\n\n"
    "1. CIA (Directorate of Analysis // Epistemological Diagnostic Core):\n"
    "   - Richards J. Heuer Jr.'s Analysis of Competing Hypotheses (ACH).\n"
    "   - Cognitive bias suppression, deception detection, and diagnostic evidence weighting.\n"
    "   - Systematic hypothesis elimination: evaluating H1 (Benign Noise / Statistical Drift), "
    "H2 (Systemic Glitch / Engineering Failure), and H3 (Adversarial Intrusion / Coordinated Fraud / Malice).\n"
    "   - Falsification scoring: prioritizing disconfirming evidence over confirmation seeking.\n\n"
    "2. DoD / US Army (Mission Command // Kinetic Operational Maneuver Core):\n"
    "   - Col. John Boyd's OODA Loop (Observe -> Orient -> Decide -> Act) out-cycling operational friction.\n"
    "   - Mission Command (Auftragstaktik): decentralized tactical execution anchored in clear Commander's Intent.\n"
    "   - Phased Courses of Action (COA): Phase 1 (T+24h Immediate Containment), Phase 2 (T+7d Root-Cause Neutralization), "
    "and Phase 3 (T+30d Institutional Hardening & Redundancy).\n"
    "   - Inviolable Rules of Engagement (ROE) and Deterministic Abort / Stop-Loss Criteria.\n\n"
    "For every operational crisis, technical incident, or strategic dilemma, produce an exhaustive, deep analytical breakdown "
    "inside <thought>...</thought> through both CIA and DoD doctrines, then issue an auditable Palantir Action Blueprint "
    "formatted as valid JSON adhering to the Dynamic Ontology (OLA)."
)

DOMAINS_SPEC = [
    {
        "domain": "ENTERPRISE_CAPITAL_ALLOCATION",
        "desc": "B2B SaaS cash flow burn spikes, predatory vendor cartels, shell entity structuring, founder dilution deadlocks, cloud spend arbitrage, and contract kickbacks."
    },
    {
        "domain": "CRITICAL_INFRASTRUCTURE_CYBER",
        "desc": "High-voltage SCADA/RTU Modbus anomalies, water treatment chemical dosing overrides, zero-day build server compromises, and nuclear coolant loop sensor drift."
    },
    {
        "domain": "DEFENSE_AEROSPACE_SUPPLY_CHAIN",
        "desc": "Rad-hardened ASIC cleanroom contamination, forged titanium submarine mill certificates, hypersonic thermal sensor blackouts, and stranding of precision turbofan cores."
    },
    {
        "domain": "EPIDEMIOLOGICAL_CRITICAL_LOGISTICS",
        "desc": "Pediatric oncology drug supply diversions, sub-zero cold-chain maritime excursions, counterfeit peptide infiltration, and hospital trauma center inventory data corruption."
    },
    {
        "domain": "FINANCIAL_CRIMES_AML_CFT",
        "desc": "Cross-border smurfing through regional banking APIs, ransomware mixer USDT off-ramps, trade-based container over-invoicing, and offshore discretionary sanctions evasion trusts."
    },
    {
        "domain": "HIGH_FREQUENCY_SYSTEMS_ENGINEERING",
        "desc": "Equities matching engine p99 latency degradation, multi-cloud Raft consensus split-brain partitions, algorithmic market maker runaway liquidations, and kernel eBPF memory exhaustion."
    },
    {
        "domain": "AUTONOMOUS_FLEET_TELEMETRY",
        "desc": "Long-haul autonomous freight GPS spoofing, subsea acoustic link dropouts during sonar sweeps, eVTOL motor CAN-bus bus-offs, and warehouse optical LiDAR marker chemical degradation."
    },
    {
        "domain": "STRATEGIC_COUNTERINTELLIGENCE",
        "desc": "Dilution refrigerator quantum computing exfiltration, foreign microwave spread-spectrum intercept arrays, clean-room physical memory smuggling, and APT zero-click spear-phishing."
    },
    {
        "domain": "CRITICAL_MARITIME_LOGISTICS",
        "desc": "Dark fleet sanctions-busting crude transfers, port vessel traffic service phantom radar spoofing, automated crane terminal ransomware, and deepwater bulk carrier ballast water sabotage."
    },
    {
        "domain": "ENERGY_GRID_RESILIENCE",
        "desc": "Simultaneous physical acoustic attacks on 500kV transformer radiators, gas compressor DCS valve overrides, hydroelectric turbine resonance manipulation, and offshore HVDC converter disconnects."
    },
    {
        "domain": "TELECOMMUNICATIONS_INFRASTRUCTURE",
        "desc": "Subsea fiber repeater acoustic acoustic interference, 5G user plane function (UPF) denial-of-service, BGP route hijacking of sovereign traffic, and automated 911 trunk saturation."
    },
    {
        "domain": "EXECUTIVE_DECISION_UNDER_UNCERTAINTY",
        "desc": "Covert hostile foreign acquisition of Tier-2 defense suppliers, CRISPR genomic sequencing extortion under 48h deadline, conflicting breach attribution reports, and datacenter cooling plant triage."
    }
]


def load_methodology_catalog(path: str = "storage/extracted_agency_methodologies.json") -> dict[str, list[dict[str, Any]]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Methodology catalog not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "CIA": [m for m in data if m.get("agency") == "CIA"],
        "DOD": [m for m in data if "ARMY" in m.get("agency", "") or m.get("agency") == "DOD"]
    }


class GeminiOrganicDistiller:
    def __init__(
        self,
        output_file: str = "training_data/palantir_cia_dod_organic_english.jsonl",
        max_workers: int = 4,
    ):
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        methods = load_methodology_catalog()
        self.cia_methods = methods["CIA"]
        self.dod_methods = methods["DOD"]
        self.max_workers = max_workers
        self.lock = threading.Lock()

        self.total_generated = 0
        if self.output_file.exists():
            with open(self.output_file, "r", encoding="utf-8") as f:
                self.total_generated = sum(1 for line in f if line.strip())
            logger.info(f"[*] Found existing organic dataset with {self.total_generated} samples.")

    def generate_single_sample(self, domain_spec: dict[str, Any]) -> dict[str, Any] | None:
        """Invokes Gemini via AGY CLI to generate one complete bespoke organic CIA+DoD sample."""
        cia_m = random.choice(self.cia_methods)
        dod_m = random.choice(self.dod_methods)
        domain_name = domain_spec["domain"]
        domain_desc = domain_spec["desc"]

        prompt = (
            "You are the Sovereign Gotham Chief Intelligence Ontologist and Master Intelligence Teacher.\n"
            "Produce an authentic, gritty, and rigorous operational training sample in 100% Native English.\n\n"
            "MANDATORY ARCHITECTURAL CONTEXT:\n"
            "1. PALANTIR DYNAMIC ONTOLOGY (Objects, Links, Actions - OLA):\n"
            "   - Objects: First-class typed entities with operational state and properties.\n"
            "   - Links: Semantic directional relations.\n"
            "   - Kinetic Actions: Governed operations with strict Rules of Engagement (ROE), phased execution (T+24h, T+7d, T+30d), and quantitative abort criteria.\n"
            "2. CIA DIAGNOSTIC TRADECRAFT (Directorate of Analysis):\n"
            f"   - Methodology: {cia_m['method_name']}\n"
            f"   - Principles: {', '.join(cia_m.get('core_principles', [])[:2])}\n"
            f"   - Inviolable Rule: {cia_m.get('inviolable_rules', ['Prioritize disconfirmation over confirmation'])[0]}\n"
            "   - Must explicitly formulate H1 (Benign Noise / Baseline Drift), H2 (Systemic Glitch / Engineering Error), H3 (Adversarial Malfeasance / Coordinated Fraud / Attack).\n"
            "3. DoD / US ARMY OPERATIONAL DOCTRINE (Mission Command):\n"
            f"   - Methodology: {dod_m['method_name']}\n"
            f"   - Principles: {', '.join(dod_m.get('core_principles', [])[:2])}\n"
            f"   - Inviolable Rule: {dod_m.get('inviolable_rules', ['Decentralized tactical execution must remain strictly within Commander Intent'])[0]}\n"
            "   - Must apply John Boyd's OODA Loop, Commander's Intent (Auftragstaktik), and Phased Courses of Action (COA).\n\n"
            f"Domain: {domain_name}\n"
            f"Scenario Guidance: {domain_desc}\n\n"
            "Return STRICTLY a valid JSON object wrapped in ```json ... ``` with this exact structure:\n"
            "{\n"
            '  "problem_statement": "A detailed, realistic, highly specific 2-3 sentence operational dilemma with concrete numbers, names, and stakes.",\n'
            '  "thought": "Deep organic multi-paragraph chain of thought starting with 1. [CIA // ESTIMATIVE INTELLIGENCE, HEUER\'S ACH & DIAGNOSTIC FALSIFICATION] and then 2. [DoD / US ARMY // MISSION COMMAND, BOYD OODA LOOP & KINETIC ACTION BLUEPRINT].",\n'
            '  "palantir_action_blueprint": {\n'
            '    "mission_id": "GOTHAM-PALANTIR-XXXXXX",\n'
            f'    "problem_domain": "{domain_name}",\n'
            '    "cia_assessment": {"dominant_hypothesis": "...", "confidence_score": 0.94, "disproven_hypotheses": ["H1", "H2"]},\n'
            '    "dod_mission_command": {"commanders_intent": "...", "ooda_cadence": "FAST_BURST"},\n'
            '    "palantir_objects": [{"object_type": "...", "properties": {...}}],\n'
            '    "palantir_links": [{"source": "...", "predicate": "...", "target": "..."}],\n'
            '    "palantir_action_execution": {\n'
            '      "phase_1_t24h_immediate_containment": "...",\n'
            '      "phase_2_t7d_tactical_neutralization": "...",\n'
            '      "phase_3_t30d_strategic_consolidation": "...",\n'
            '      "rules_of_engagement": ["..."],\n'
            '      "abort_criteria": "..."\n'
            '    }\n'
            '  }\n'
            "}"
        )

        try:
            res = subprocess.run(
                ["agy", "-p", prompt],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=120,
            )

            if res.returncode == 0 and res.stdout:
                json_match = re.search(r"```json(.*?)```", res.stdout, re.DOTALL)
                raw_text = json_match.group(1).strip() if json_match else res.stdout.strip()
                if "{" in raw_text and "}" in raw_text:
                    raw_text = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
                    data = json.loads(raw_text)

                    prob = data.get("problem_statement", "")
                    thought = data.get("thought", "")
                    blueprint = data.get("palantir_action_blueprint", {})

                    if prob and thought and blueprint:
                        thought_clean = thought.strip()
                        if not thought_clean.startswith("<thought>"):
                            thought_clean = f"<thought>\n{thought_clean}\n</thought>"

                        rag_context = {
                            "mission_id": blueprint.get("mission_id", f"GOTHAM-PALANTIR-{random.randint(100000, 999999)}"),
                            "operational_domain": domain_name,
                            "classification": "UNCLASSIFIED//FOR OFFICIAL USE ONLY",
                            "grounded_agency_doctrines": {
                                "CIA_DIAGNOSTIC_CORE": {
                                    "method_name": cia_m["method_name"],
                                    "principles": cia_m.get("core_principles", [])[:2],
                                    "inviolable_rules": cia_m.get("inviolable_rules", [])[:2]
                                },
                                "DOD_OPERATIONAL_COMMAND": {
                                    "method_name": dod_m["method_name"],
                                    "principles": dod_m.get("core_principles", [])[:2],
                                    "inviolable_rules": dod_m.get("inviolable_rules", [])[:2]
                                }
                            }
                        }

                        user_prompt = (
                            f"Palantir Gotham Operational Directive [{domain_name}]:\n"
                            f"Analyze the following operational dilemma:\n\"{prob}\"\n\n"
                            f"[PALANTIR ONTOLOGICAL CONTEXT - AUTHENTIC CIA + DOD DOCTRINAL GROUND TRUTH]\n"
                            f"{json.dumps(rag_context, indent=2, ensure_ascii=False)}"
                        )

                        assistant_reply = f"{thought_clean}\n\n```json\n{json.dumps(blueprint, indent=2, ensure_ascii=False)}\n```"

                        return {
                            "conversations": [
                                {"from": "system", "value": PALANTIR_CIA_DOD_SYSTEM_PROMPT},
                                {"from": "human", "value": user_prompt},
                                {"from": "gpt", "value": assistant_reply},
                            ]
                        }
        except Exception as e:
            logger.warning(f"Error generating sample: {e}")
        return None

    def save_sample(self, sample: dict[str, Any]) -> int:
        """Appends one sample to the dataset in a thread-safe manner."""
        with self.lock:
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            self.total_generated += 1
            return self.total_generated

    def run_distillation_campaign(self, target_samples: int = 100):
        """Runs the multi-worker organic distillation campaign."""
        logger.info("==========================================================================")
        logger.info("   SOVEREIGN GOTHAM // GEMINI ORGANIC COGNITIVE DISTILLER (CIA + DOD)")
        logger.info("==========================================================================")
        logger.info(f"[*] Target Samples: {target_samples}")
        logger.info(f"[*] Available CIA Methodologies: {len(self.cia_methods)}")
        logger.info(f"[*] Available DoD Methodologies: {len(self.dod_methods)}")
        logger.info(f"[*] Destination: {self.output_file}")
        logger.info(f"[*] Parallel Workers: {self.max_workers}")

        needed = max(0, target_samples - self.total_generated)
        if needed == 0:
            logger.info(f"[✓] Already have {self.total_generated} samples. Done.")
            return

        logger.info(f"[*] Launching {needed} organic distillation tasks across {self.max_workers} worker threads...")

        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for _ in range(needed):
                domain = random.choice(DOMAINS_SPEC)
                futures.append(executor.submit(self.generate_single_sample, domain))

            for f in concurrent.futures.as_completed(futures):
                completed += 1
                try:
                    sample = f.result()
                    if sample:
                        cur_total = self.save_sample(sample)
                        prob_line = sample["conversations"][1]["value"].split("\n")[2][:70]
                        logger.info(f"[{completed}/{needed}] [✓] Organic Sample Added! (Total: {cur_total}/{target_samples}) -> {prob_line}...")
                    else:
                        logger.warning(f"[{completed}/{needed}] [-] Generation returned None, retrying...")
                except Exception as exc:
                    logger.warning(f"[{completed}/{needed}] [!] Worker exception: {exc}")

        logger.info(f"\n[✓] GEMINI CIA+DOD ORGANIC DISTILLATION COMPLETE! Total samples: {self.total_generated}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gemini Organic Distillation (CIA + DoD)")
    parser.add_argument("--samples", type=int, default=100, help="Number of organic samples to distill")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent worker threads")
    args = parser.parse_args()

    distiller = GeminiOrganicDistiller(max_workers=args.workers)
    distiller.run_distillation_campaign(target_samples=args.samples)
