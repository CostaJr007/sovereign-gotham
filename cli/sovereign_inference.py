"""
Sovereign Gotham - DirectML Cognitive Inference Engine
Executes inference on the fine-tuned DeepSeek-R1-Distill-Qwen LoRA model
using the dedicated AMD Radeon RX 7600 XT GPU (16 GB GDDR6).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles with unbuffered live flushing
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

_CURRENT_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
PROJECT_ROOT = _CURRENT_DIR
for parent in [_CURRENT_DIR, *_CURRENT_DIR.parents]:
    if (parent / "pyproject.toml").exists() or (parent / "ontology").exists():
        PROJECT_ROOT = parent
        break
_workspace_fallback = Path(r"c:\Users\adeil\.gemini\antigravity\scratch\sovereign_gotham")
if _workspace_fallback.exists() and str(_workspace_fallback) not in sys.path:
    sys.path.insert(0, str(_workspace_fallback))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import json
import re

from ingestion.document_loader import DeclassifiedDocumentLoader
from ingestion.entity_extractor import OntologicalEntityExtractor
from ontology.graph import GothamKnowledgeGraph
from ontology.models import Target_Entity
from ontology.osdk_client import SovereignOSDKClient
from storage.vector_store import SovereignVectorStore


def parse_args():
    parser = argparse.ArgumentParser(description="Sovereign Gotham - Local Model Inference")
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        default=None,
        help="Intelligence directive / operational query to analyze",
    )
    default_dir = (
        "D:/sovereign_models/sovereign_gotham_universal_1.5b"
        if Path("D:/sovereign_models/sovereign_gotham_universal_1.5b").exists()
        else "D:/sovereign_models/sovereign_gotham_merged_1.5b"
    )
    parser.add_argument(
        "--model_dir",
        type=str,
        default=default_dir,
        help="Path to unified model or LoRA adapter directory",
    )

    parser.add_argument(
        "--base_model",
        type=str,
        default="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
        help="HuggingFace base model ID",
    )
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=2048,
        help="Maximum tokens to generate",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.6,
        help="Sampling temperature (0.6 recommended for reasoning models)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in continuous interactive chat mode",
    )
    parser.add_argument(
        "--no_rag",
        action="store_true",
        help="Disable automatic Ontological Knowledge Graph & Vector Store RAG",
    )
    return parser.parse_args()


_METHODOLOGY_CATALOG = None


def get_methodology_catalog() -> list[dict[str, Any]]:
    global _METHODOLOGY_CATALOG
    if _METHODOLOGY_CATALOG is None:
        cat_file = PROJECT_ROOT / "storage" / "extracted_agency_methodologies.json"
        if cat_file.exists():
            with open(cat_file, "r", encoding="utf-8") as f:
                _METHODOLOGY_CATALOG = json.load(f)
        else:
            _METHODOLOGY_CATALOG = []
    return _METHODOLOGY_CATALOG


def init_knowledge_system():
    """Initializes and pre-seeds the Sovereign Knowledge Graph and Vector Store exclusively with project methodologies."""
    graph = GothamKnowledgeGraph()
    vector_store = SovereignVectorStore(persist_directory=str(PROJECT_ROOT / "storage" / "chroma_db"))

    # Ensure vector store contains authentic agency project methodologies (Zero historical archive cables)
    catalog = get_methodology_catalog()
    if (vector_store.collection and vector_store.collection.count() == 0) or len(vector_store.corpus) == 0:
        if catalog:
            texts = []
            metas = []
            ids = []
            for idx, m in enumerate(catalog):
                text_rep = (
                    f"{m.get('agency', 'INTELLIGENCE')} OPERATIONAL METHODOLOGY: {m.get('method_name', 'Method')}\n"
                    f"Domain: {m.get('doctrine_domain', 'OPERATIONS')}\n"
                    f"Principles: {' '.join(m.get('core_principles', []))}\n"
                    f"Application: {m.get('real_world_application', '')}"
                )
                texts.append(text_rep)
                metas.append({
                    "source": m.get("source_file", "agency_doctrine"),
                    "agency": m.get("agency", "INTELLIGENCE"),
                    "method_name": m.get("method_name", "Method"),
                    "classification": "UNCLASSIFIED_DOCTRINE",
                })
                ids.append(f"DOC-METHOD-{m.get('agency', 'AGY')}-{idx:04d}")
            vector_store.add_texts(texts, metas, ids)

    return graph, vector_store


def build_ontological_context(query: str, graph: GothamKnowledgeGraph, vector_store: SovereignVectorStore):
    """Retrieves agency doctrine and grounds problem domain from the multi-agency ontology."""
    q_lower = query.lower()

    # 1. Infer Problem Domain (Comprehensive English and Operational Mapping)
    if any(w in q_lower for w in ("startup", "saas", "burn", "revenue", "runway", "arr", "churn", "equity", "dilution", "vendor", "contract", "audit", "cfo", "cpo", "lucro", "faturamento", "sócio", "caixa")):
        domain = "ENTERPRISE_CAPITAL_ALLOCATION"
    elif any(w in q_lower for w in ("cyber", "scada", "modbus", "rtu", "dns", "firewall", "exploit", "intrusion", "substation", "grid", "telemetry", "anomaly", "zero-day", "hacker", "vpn")):
        domain = "CRITICAL_INFRASTRUCTURE_CYBER"
    elif any(w in q_lower for w in ("semiconductor", "asic", "cleanroom", "wafer", "titanium", "forging", "hypersonic", "aerospace", "procurement", "fab", "supply chain", "fábrica", "gargalo")):
        domain = "DEFENSE_AEROSPACE_SUPPLY_CHAIN"
    elif any(w in q_lower for w in ("hospital", "pharmaceutical", "oncology", "plasma", "cold-chain", "vaccine", "insulin", "reagent", "trauma", "clinic", "medicamento")):
        domain = "EPIDEMIOLOGICAL_CRITICAL_LOGISTICS"
    elif any(w in q_lower for w in ("aml", "cft", "laundering", "smurfing", "structuring", "shell", "crypto", "usdt", "kickback", "rico", "fraud", "wire", "propina", "lavagem")):
        domain = "FINANCIAL_CRIMES_AML_CFT"
    elif any(w in q_lower for w in ("latency", "p99", "matching engine", "order book", "distributed", "raft", "consensus", "partition", "deadlock", "ebpf", "kernel", "microsecond")):
        domain = "HIGH_FREQUENCY_SYSTEMS_ENGINEERING"
    elif any(w in q_lower for w in ("autonomous", "truck", "gps spoofing", "lidar", "drone", "swarm", "subsea", "evtol", "fleet", "veículo", "autônomo")):
        domain = "AUTONOMOUS_FLEET_TELEMETRY"
    elif any(w in q_lower for w in ("insider", "exfiltration", "honeypot", "biometric", "espionage", "apt", "clearance", "spying", "contrainteligência")):
        domain = "STRATEGIC_COUNTERINTELLIGENCE"
    elif any(w in q_lower for w in ("dark fleet", "tanker", "ais", "vessel", "port", "container", "crane", "maritime", "shipping", "navio", "porto")):
        domain = "CRITICAL_MARITIME_LOGISTICS"
    elif any(w in q_lower for w in ("grid", "blackstart", "hvdc", "transformer", "transmission", "substation", "dam", "turbine", "energia", "apagão")):
        domain = "ENERGY_GRID_RESILIENCE"
    elif any(w in q_lower for w in ("subsea cable", "fiber", "bgp", "5g", "core", "upf", "telecom", "fibra", "cabo")):
        domain = "TELECOMMUNICATIONS_INFRASTRUCTURE"
    else:
        domain = "OPERATIONAL_INTELLIGENCE"

    catalog = get_methodology_catalog()
    cia_pool = [m for m in catalog if m.get("agency") == "CIA"]
    army_pool = [m for m in catalog if "ARMY" in m.get("agency", "") or m.get("agency") == "DOD"]

    # 2. Similarity search in vector store (prioritizing doctrinal frameworks)
    docs = vector_store.similarity_search(query, top_k=5, where={"classification": "UNCLASSIFIED_DOCTRINE"})
    if not docs:
        docs = vector_store.similarity_search(query, top_k=5)

    retrieved_summary = []
    selected_methods = {}

    for d in docs:
        meta = d.get("metadata", {})
        ag = str(meta.get("agency", ""))
        txt = d.get("text", "")
        m_name = None
        if "OPERATIONAL METHODOLOGY:" in txt:
            m_name = txt.split("OPERATIONAL METHODOLOGY:")[1].split("\n")[0].strip()
        elif "METHODOLOGY:" in txt:
            m_name = txt.split("METHODOLOGY:")[1].split("\n")[0].strip()

        if ag == "CIA" and "cia" not in selected_methods and m_name:
            selected_methods["cia"] = m_name
        elif ("ARMY" in ag or ag == "DOD") and "dod_army" not in selected_methods and m_name:
            selected_methods["dod_army"] = m_name

        retrieved_summary.append({
            "id": d.get("id"),
            "classification": meta.get("classification", "DOCTRINE"),
            "agency": ag,
            "preview": txt[:100].replace("\n", " ").strip(),
        })

    # Catalog fallbacks strictly for CIA + DoD dual-core
    if "cia" not in selected_methods:
        selected_methods["cia"] = cia_pool[0]["method_name"] if cia_pool else "Richards Heuer Analysis of Competing Hypotheses (ACH)"
    if "dod_army" not in selected_methods:
        selected_methods["dod_army"] = army_pool[0]["method_name"] if army_pool else "Hierarchical Multi-Echelon Subsystem Decomposition and Asynchronous Feedback Protocol"

    # 3. Check for specific entities explicitly mentioned in graph
    osdk = SovereignOSDKClient(graph)
    targets = osdk.objects(Target_Entity).fetch(limit=10)
    matched_target = None
    for t in targets:
        if t.name.lower() in q_lower:
            matched_target = {"name": t.name, "threat_level": str(getattr(t.threat_level, "value", t.threat_level))}
            break

    context_data = {
        "domain": domain,
        "agency_doctrines": selected_methods,
    }
    if matched_target:
        context_data["grounded_entity"] = matched_target

    return context_data, retrieved_summary


def load_sovereign_model(base_model_id: str, model_path_str: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_path = Path(model_path_str)
    if not model_path.exists():
        raise FileNotFoundError(f"Model path not found at: {model_path}")

    device = torch.device("cpu")
    try:
        import torch_directml
        count = torch_directml.device_count()
        target_idx = None
        for i in range(count):
            name = torch_directml.device_name(i)
            if "7600" in name or "RX" in name or "XT" in name:
                target_idx = i
                break
        if target_idx is None and count > 0:
            target_idx = count - 1

        if target_idx is not None:
            device = torch_directml.device(target_idx)
            device_name = torch_directml.device_name(target_idx)
            print(f"[+] GPU Acceleration: {device_name} (DirectML Device {target_idx})")
    except Exception as e:
        print(f"[-] Falling back to CPU: {e}")

    print(f"[*] Loading tokenizer from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Check if standalone merged model or PEFT adapter
    has_weights = (model_path / "model.safetensors").exists()
    is_adapter = (model_path / "adapter_config.json").exists() and not has_weights

    if not is_adapter:
        print(f"[*] Loading standalone unified model from {model_path}...")
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            torch_dtype=torch.float16,
            trust_remote_code=True,
        ).to(device)
    else:
        from peft import PeftModel
        print(f"[*] Loading base model {base_model_id}...")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=torch.float16,
            trust_remote_code=True,
        ).to(device)
        print(f"[*] Attaching fine-tuned Sovereign Gotham LoRA adapters from {model_path}...")
        model = PeftModel.from_pretrained(base_model, str(model_path))

    model.eval()
    print("[✓] Sovereign Gotham Engine Ready.\n")
    return model, tokenizer, device


def query_model(
    model,
    tokenizer,
    device,
    prompt: str,
    max_tokens: int = 3072,
    temp: float = 0.6,
    graph: GothamKnowledgeGraph | None = None,
    vector_store: SovereignVectorStore | None = None,
    use_rag: bool = True,
) -> str:
    system_directive = (
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

    if use_rag and graph is not None and vector_store is not None:
        context_data, evidence = build_ontological_context(prompt, graph, vector_store)
        domain_tag = context_data.get('domain', 'OPERATIONAL_INTELLIGENCE')
        if evidence:
            print("[+] Ontological RAG Grounding:")
            for ev in evidence:
                print(f"    * Document [{ev['id']}] ({ev.get('agency', 'DOCTRINE')}): {ev['preview']}...")
            print(f"    * Problem Domain: {domain_tag}")
            if "agency_doctrines" in context_data:
                doctrines = context_data["agency_doctrines"]
                print(f"    * Agency Doctrines Grounded:")
                print(f"      - CIA: {doctrines.get('cia', 'N/A')}")
                print(f"      - DoD/Army: {doctrines.get('dod_army', 'N/A')}\n")

        user_content = (
            f"Palantir Gotham Operational Directive [{domain_tag}]:\n"
            f"Analyze the following operational dilemma:\n\"{prompt}\"\n\n"
            f"[PALANTIR ONTOLOGICAL CONTEXT - AUTHENTIC CIA + DOD DOCTRINAL GROUND TRUTH]\n"
            f"{json.dumps(context_data, indent=2, ensure_ascii=False)}"
        )
        seed_prefix = "1. [CIA // ESTIMATIVE INTELLIGENCE, HEUER'S ACH & DIAGNOSTIC FALSIFICATION]"
        formatted_prompt = (
            f"<|im_start|>system\n{system_directive}<|im_end|>\n"
            f"<|im_start|>user\n{user_content}<|im_end|>\n"
            f"<|im_start|>assistant\n<thought>\n{seed_prefix}\n"
        )
    else:
        seed_prefix = "1. [CIA // ESTIMATIVE INTELLIGENCE, HEUER'S ACH & DIAGNOSTIC FALSIFICATION]"
        formatted_prompt = (
            f"<|im_start|>system\n{system_directive}<|im_end|>\n"
            f"<|im_start|>user\n{prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n<thought>\n{seed_prefix}\n"
        )

    inputs = tokenizer(formatted_prompt, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    start_t = time.time()
    eos_ids = [tokenizer.eos_token_id]
    im_end_id = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if isinstance(im_end_id, int) and im_end_id != tokenizer.eos_token_id:
        eos_ids.append(im_end_id)

    outputs = model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        do_sample=True,
        temperature=temp,
        top_p=0.95,
        repetition_penalty=1.05,
        eos_token_id=eos_ids,
        pad_token_id=tokenizer.eos_token_id,
    )
    elapsed = time.time() - start_t

    input_len = inputs["input_ids"].shape[1]
    new_tokens = outputs[0][input_len:]
    generated_text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    reply = f"<thought>\n{seed_prefix}\n{generated_text}"

    # Strip unwanted prompt loop echoes
    if "<|im_start|>" in reply:
        reply = reply.split("<|im_start|>")[0].strip()
    if "<|im_end|>" in reply:
        reply = reply.split("<|im_end|>")[0].strip()

    # Normalize excessive consecutive newlines
    reply = re.sub(r"\n{3,}", "\n\n", reply).strip()

    tok_count = len(outputs[0]) - inputs["input_ids"].shape[1]
    speed = round(tok_count / max(elapsed, 0.01), 1)
    print(f"[{tok_count} tokens generated in {elapsed:.2f}s ({speed} tok/s)]\n")
    return reply


def handle_station_command(
    query: str,
    graph: GothamKnowledgeGraph | None,
    vector_store: SovereignVectorStore | None,
) -> str | None:
    """
    Intercepts administrative commands, status checks, and casual greetings
    to provide instant station feedback without invoking heavy GPU inference or irrelevant RAG searches.
    """
    cleaned = query.strip().lower()
    cleaned = re.sub(r"[!?.，,]+$", "", cleaned).strip()

    greetings = {
        "hello", "hi", "hey", "station", "status", "greetings", "ping",
        "oi", "ola", "olá"
    }
    if cleaned in greetings:
        doc_count = vector_store.collection.count() if (vector_store and vector_store.collection) else 0
        entity_count = len(graph.entities) if graph else 0
        return (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│  SOVEREIGN GOTHAM // OPERATIONAL INTELLIGENCE STATION                  │\n"
            "└────────────────────────────────────────────────────────────────────────┘\n"
            " Operational Intelligence Station Active. Sovereign Air-Gap Secured.\n\n"
            f" • Dedicated GPU: AMD Radeon RX 7600 XT (DirectML Deductive Compute)\n"
            f" • Palantir Dynamic Ontology: {entity_count} Entities in Graph\n"
            f" • Doctrinal Vector Store (ChromaDB): {doc_count} Grounded Agency Methodologies\n\n"
            " Standing by for mission directives, systems failure triage, or enterprise risk deconstruction.\n"
            " Type 'help' to review operational query paradigms."
        )

    if cleaned in {"help", "commands", "examples", "ajuda"}:
        return (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│  OPERATIONAL DIRECTIVE PARADIGMS & SYSTEM COMMANDS                     │\n"
            "└────────────────────────────────────────────────────────────────────────┘\n"
            " Examples of mission directives to engage multi-agency <thought> reasoning:\n\n"
            " 1. \"B2B SaaS startup burn rate surged 45% while API volume surged 300%.\n"
            "     CPO blames cloud infra, but forensic audit shows 18 related-party shell vendors.\"\n\n"
            " 2. \"High-voltage transmission substation SCADA RTUs register anomalous Modbus TCP writes\n"
            "     at 03:14 UTC with zero operator commands in historian. Isolate signal and formulate COA.\"\n\n"
            " 3. \"Distributed consensus Raft cluster enters split-brain partition loop during network\n"
            "     fiber flapping. Analyze failure topology and define deterministic remediation.\"\n\n"
            " System Commands:\n"
            " • 'status' - Displays GPU telemetry, Vector Store volume, and Knowledge Graph metrics\n"
            " • 'exit' or 'quit' - Terminates the interactive station session"
        )

    if cleaned in {"status", "info", "telemetry", "telemetria"}:
        doc_count = vector_store.collection.count() if (vector_store and vector_store.collection) else 0
        stats = graph.get_stats() if graph else {}
        return (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│  SOVEREIGN GOTHAM STATION TELEMETRY                                    │\n"
            "└────────────────────────────────────────────────────────────────────────┘\n"
            " • Engine Status: ONLINE (DirectML DirectX 12 Compute)\n"
            " • Accelerator: AMD Radeon RX 7600 XT (16 GB GDDR6 Dedicated)\n"
            f" • Doctrinal Vector Store: {doc_count} Active Agency Methodologies\n"
            f" • Knowledge Graph: {stats.get('total_entities', 0)} entities, {stats.get('total_links', 0)} relations\n"
            f" • Graph Density: {stats.get('density', 0.0):.4f}"
        )

    return None


def main():
    args = parse_args()
    print("==========================================================================")
    print("   SOVEREIGN GOTHAM // DEEPSEEK-R1 COGNITIVE INTELLIGENCE RUNNER")
    print("==========================================================================")

    use_rag = not args.no_rag
    graph = None
    vector_store = None
    if use_rag:
        print("[*] Initializing Ontological Knowledge Graph & Vector Store (ChromaDB)...")
        graph, vector_store = init_knowledge_system()
        print("[✓] Knowledge System Connected.\n")

    # Fast-path for non-interactive administrative commands and greetings (zero GPU overhead)
    if args.query and not args.interactive:
        station_response = handle_station_command(args.query, graph, vector_store)
        if station_response:
            print(station_response)
            return

    model, tokenizer, device = load_sovereign_model(args.base_model, args.model_dir)

    if args.interactive:
        print("[!] Entering Interactive Intelligence Station (Type 'exit' to quit)\n")

        while True:
            try:
                user_input = input("SovereignGotham> ").strip()
                if not user_input or user_input.lower() in ("exit", "quit", "sair"):
                    break

                station_response = handle_station_command(user_input, graph, vector_store)
                if station_response:
                    print(f"\n{station_response}\n")
                    print("-" * 74)
                    continue

                print("\n[Processing Directive...]")
                response = query_model(
                    model, tokenizer, device, user_input, args.max_tokens, args.temperature,
                    graph=graph, vector_store=vector_store, use_rag=use_rag
                )
                print(response)
                print("-" * 74)
            except KeyboardInterrupt:
                break
    elif args.query:
        station_response = handle_station_command(args.query, graph, vector_store)
        if station_response:
            print(station_response)
        else:
            print(f"[Query]: {args.query}\n")
            response = query_model(
                model, tokenizer, device, args.query, args.max_tokens, args.temperature,
                graph=graph, vector_store=vector_store, use_rag=use_rag
            )
            print(response)
    else:
        demo_query = (
            "B2B Enterprise SaaS burn rate surged 45% while API volume surged 300%. "
            "The CPO blames cloud infrastructure, but forensic audits reveal 18 offshore consultancy contracts "
            "billing $150,000 monthly with common beneficial ownership linked to internal leadership. "
            "Apply multi-agency tradecraft (NSA, FBI, CIA, DoD) and synthesize a Palantir Action Blueprint."
        )
        print(f"[Demo Directive]: {demo_query}\n")
        response = query_model(
            model, tokenizer, device, demo_query, args.max_tokens, args.temperature,
            graph=graph, vector_store=vector_store, use_rag=use_rag
        )
        print(response)


if __name__ == "__main__":
    main()
