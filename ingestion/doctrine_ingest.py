"""
Sovereign Gotham - Multi-Agency Doctrinal Methodology Ingestion Engine
Extracts, structures, and indexes the operational problem-solving doctrines of:
  1. NSA: Telemetry, SIGINT, Signal vs Noise, Cyber Threat Modeling, System Anomaly Profiling
  2. FBI: Forensic Causality, RICO & Financial Incentive Analysis, Behavioral Profiling, Evidentiary Corroboration
  3. CIA: Richards Heuer's ACH (Analysis of Competing Hypotheses), Bias Elimination, Red Teaming, Strategic Foresight
  4. DoD / US Army: OODA Loop, Mission Command (Auftragstaktik), JP 5-0 Joint Planning, Logistics Bottlenecks, ROE
Populates ChromaDB and GothamKnowledgeGraph for cross-agency reasoning.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    AgencyDoctrineType,
    ClearanceLevel,
    LinkType,
    OntologyLink,
    Procedure,
    ProcedureCategory,
)
from storage.vector_store import SovereignVectorStore


logger = logging.getLogger("SovereignGotham.DoctrineIngest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DOCTRINAL_CORPUS: list[dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # 1. NSA - SIGNALS INTELLIGENCE & MODERN CYBER TELEMETRY DOCTRINE
    # -------------------------------------------------------------------------
    {
        "id": "DOC-NSA-SIGINT-TRIAGE",
        "agency": "NSA",
        "doctrine_type": AgencyDoctrineType.NSA_SIGINT_TELEMETRY.value,
        "title": "NSA Signal vs Noise Triage & Telemetry Anomaly Baseline Protocol",
        "text": (
            "NSA DOCTRINAL FRAMEWORK: SIGNAL VS NOISE EXTRACTION & TELEMETRY TRIAGE.\n"
            "1. Axiom: Objective reality is found in telemetry, cold metrics, frequency distributions, and packets, "
            "not in subjective human narratives or emotional rationalizations.\n"
            "2. Signal-to-Noise Ratio (SNR) Optimization: When confronting any operational, corporate, or systemic problem, "
            "strip away the narrative friction. Identify the raw measurable vectors: volume, velocity, error rates, financial flows, "
            "time deltas, and access frequencies.\n"
            "3. Anomaly Detection Baseline: Define normal operating parameters through historical standard deviation. Any deviation "
            "greater than 2.5 sigma is an active signal anomaly requiring immediate investigative containment.\n"
            "4. Modern Cyber Threat Modeling & Zero Trust: Assume continuous breach. Verify explicitly, use least privilege access, "
            "and continuously inspect packet headers and behavioral telemetry. In non-technical domains (e.g., corporate strategy, "
            "interpersonal negotiations, skill acquisition), apply the same principle: treat all unverified claims as untrusted inputs, "
            "isolate single points of failure, and measure only verified output frequency."
        ),
        "metadata": {
            "agency": "NSA",
            "domain": "SIGINT_CYBER_TELEMETRY",
            "classification": "UNCLASSIFIED_DOCTRINE",
            "focus": "Signal extraction, noise filtering, telemetry anomaly detection",
        },
    },
    {
        "id": "DOC-NSA-CRYPTOLOG-METHODOLOGY",
        "agency": "NSA",
        "doctrine_type": AgencyDoctrineType.NSA_SIGINT_TELEMETRY.value,
        "title": "NSA Cryptologic Problem Solving: Mathematical Probability & Black-Box Inversion",
        "text": (
            "NSA CRYPTOLOGIC PROBLEM-SOLVING DOCTRINE.\n"
            "1. Black-Box Decomposition: When an adversary, a market competitor, or an unknown system exhibits obscure internal mechanics, "
            "treat it as an encrypted cipher stream. Analyze input-output pairs under varied environmental stimuli.\n"
            "2. Frequency Analysis: Repetitive patterns in human or systemic behavior always reveal underlying structural architecture. "
            "In language acquisition, identify the top 1,000 statistical root frequencies (Zipf's law) to capture 85% of functional comprehension. "
            "In business, monitor recurring customer churn points and supplier invoice timing.\n"
            "3. Cryptographic Verification: No assertion is accepted without mathematical or empirical proof. Avoid intuitive leaps; "
            "validate each step through deterministic correlation."
        ),
        "metadata": {
            "agency": "NSA",
            "domain": "CRYPTOLOGY_MATHEMATICAL_MODELING",
            "classification": "UNCLASSIFIED_DOCTRINE",
            "focus": "Frequency analysis, black box decomposition, empirical proof",
        },
    },

    # -------------------------------------------------------------------------
    # 2. FBI - FORENSIC CAUSALITY & INCENTIVE NETWORK ANALYSIS
    # -------------------------------------------------------------------------
    {
        "id": "DOC-FBI-RICO-INCENTIVES",
        "agency": "FBI",
        "doctrine_type": AgencyDoctrineType.FBI_FORENSIC_INCENTIVE.value,
        "title": "FBI Forensic Causality, Follow-The-Money & RICO Incentive Network Protocol",
        "text": (
            "FBI FORENSIC INVESTIGATIVE DOCTRINE: INCENTIVES & CAUSAL NETWORKS.\n"
            "1. Axiom: Human systems, corporate enterprises, and criminal conspiracies operate on underlying economic incentives. "
            "Follow the money, follow the status, follow the liability avoidance. Stated motives are almost always secondary rationalizations.\n"
            "2. RICO Enterprise Theory: To solve a complex organizational breakdown or fraud, do not isolate the front-line actor. "
            "Map the entire enterprise: who sanctioned the action, who benefited from the downstream revenue, who controlled the communication channel, "
            "and who bore the residual risk.\n"
            "3. Conflict of Interest Diagnosis: When two entities or partners present conflicting claims, analyze their payoff matrices. "
            "Identify asymmetric upsides (moral hazard) where one party captures profit while externalizing downside risk onto the system.\n"
            "4. Blind Evidentiary Corroboration: A piece of evidence is only valid if verified by an independent second vector that shares "
            "no common incentive or provenance with the first source. Reject uncorroborated single-source testimonials."
        ),
        "metadata": {
            "agency": "FBI",
            "domain": "FORENSIC_INCENTIVES_RICO",
            "classification": "UNCLASSIFIED_DOCTRINE",
            "focus": "Financial tracing, incentive alignment, network vulnerability",
        },
    },
    {
        "id": "DOC-FBI-BEHAVIORAL-LEVERAGE",
        "agency": "FBI",
        "doctrine_type": AgencyDoctrineType.FBI_FORENSIC_INCENTIVE.value,
        "title": "FBI Behavioral Analysis: Pattern of Life, Stress Vectors & Negotiation Leverage",
        "text": (
            "FBI BEHAVIORAL ANALYSIS & CRISIS NEGOTIATION METHODOLOGY.\n"
            "1. Pattern of Life (PoL): Establish the baseline behavioral cadence of the target or organization. Behavioral anomalies "
            "always precede tactical action or systemic default.\n"
            "2. Stress Vectors & M.I.C.E. Matrix: Individuals and counter-parties act under specific pressure vectors: "
            "Money (financial distress), Ideology (inflexible core dogmas), Compromise/Coercion (fear of exposure), Ego (need for validation). "
            "Identifying the active vector grants immediate predictive leverage.\n"
            "3. Tactical Empathy & Calibrated Inquiries: In high-stakes disputes, avoid accusatory binaries. Use calibrated open-ended questions "
            "('How am I supposed to do that?', 'What is the objective here?') to force the counterpart to solve your resource dilemma."
        ),
        "metadata": {
            "agency": "FBI",
            "domain": "BEHAVIORAL_PROFILING_NEGOTIATION",
            "classification": "UNCLASSIFIED_DOCTRINE",
            "focus": "Pattern of life, stress vectors, calibrated negotiation",
        },
    },

    # -------------------------------------------------------------------------
    # 3. CIA - ANALYSIS OF COMPETING HYPOTHESES (ACH) & STRATEGIC FORESIGHT
    # -------------------------------------------------------------------------
    {
        "id": "DOC-CIA-ACH-HEUER",
        "agency": "CIA",
        "doctrine_type": AgencyDoctrineType.CIA_STRATEGIC_ACH.value,
        "title": "CIA Richards Heuer Analysis of Competing Hypotheses (ACH) & Cognitive Bias Elimination",
        "text": (
            "CIA DOCTRINAL METHODOLOGY: ANALYSIS OF COMPETING HYPOTHESES (RICHARDS J. HEUER JR.).\n"
            "1. Axiom: The human mind instinctively selects a favorite hypothesis and seeks confirming evidence, blinding itself to alternatives. "
            "Strategic intelligence requires simultaneous evaluation of all plausible mutually exclusive hypotheses.\n"
            "2. Diagnostic Evidence Matrix: Create a matrix of Hypotheses (H1, H2, H3, ...) versus Evidence (E1, E2, E3, ...). "
            "Rate evidence not on how much it supports a hypothesis, but on its DIAGNOSTIC VALUE—whether it actively disproves or refutes a hypothesis.\n"
            "3. Refutation Principle: The most probable explanation is not the one with the most confirming evidence, but the one with the LEAST "
            "disconfirming evidence. Eliminate hypotheses systematically.\n"
            "4. Deception & Denial Detection: Explicitly calculate the probability that observable evidence has been curated, staged, or spoofed "
            "by an adversary or counter-party to mislead decision-makers."
        ),
        "metadata": {
            "agency": "CIA",
            "domain": "STRATEGIC_INTELLIGENCE_ACH",
            "classification": "UNCLASSIFIED_DOCTRINE",
            "focus": "ACH matrix, cognitive bias mitigation, deception detection",
        },
    },
    {
        "id": "DOC-CIA-STRUCTURED-ANALYTIC",
        "agency": "CIA",
        "doctrine_type": AgencyDoctrineType.CIA_STRATEGIC_ACH.value,
        "title": "CIA Structured Analytic Techniques: Red Teaming, Devil's Advocacy & Key Assumptions Check",
        "text": (
            "CIA TRADECRAFT PRIMER: STRUCTURED ANALYTIC TECHNIQUES.\n"
            "1. Key Assumptions Check (KAC): List all foundational premises taken for granted. For each premise, ask: 'If this assumption is false, "
            "does our entire strategy collapse?' If yes, it is a critical vulnerability.\n"
            "2. Red Team Analysis: Adopt the mindset, constraints, and aggression of the competitor, adversary, or hostile environment. "
            "Actively exploit your own operational seams and blind spots before the opponent does.\n"
            "3. High-Impact / Low-Probability (Black Swan) Scenarios: Model catastrophic or asymmetric events that conventional consensus dismisses. "
            "Construct robust trigger tripwires to alert leadership before the crisis materializes."
        ),
        "metadata": {
            "agency": "CIA",
            "domain": "RED_TEAMING_ASSUMPTIONS",
            "classification": "UNCLASSIFIED_DOCTRINE",
            "focus": "Red team analysis, key assumptions check, strategic foresight",
        },
    },

    # -------------------------------------------------------------------------
    # 4. DOD / US ARMY - OPERATIONAL DOCTRINE & MISSION COMMAND
    # -------------------------------------------------------------------------
    {
        "id": "DOC-DOD-OODA-BOYD",
        "agency": "DOD_ARMY",
        "doctrine_type": AgencyDoctrineType.DOD_ARMY_OODA_MISSION_COMMAND.value,
        "title": "DoD Boyd OODA Loop & Fast-Transient Decision Superiority Doctrine",
        "text": (
            "DOD / US AIR FORCE TACTICAL DOCTRINE: THE BOYD OODA LOOP (OBSERVE-ORIENT-DECIDE-ACT).\n"
            "1. Axiom: Decision-making is a continuous, fast-transient adaptive cycle. Victory belongs to the entity that cycles through "
            "the OODA loop faster and more accurately than the environment can generate friction.\n"
            "2. Orientation as Center of Gravity: Observation is raw data; Orientation is the filter (genetic heritage, cultural traditions, "
            "previous experiences, new information, analysis). Flawed orientation causes catastrophic tactical error.\n"
            "3. Tempo & Friction: Accelerate the tempo of your own loop while injecting uncertainty, ambiguity, and deception into the opponent's loop "
            "to cause cognitive paralysis (operating inside their decision cycle).\n"
            "4. Phased Course of Action (COA): Formulate decisive, phased directives:\n"
            "   - Phase 1 (T+24h): Rapid stabilization, containment, reconnaissance.\n"
            "   - Phase 2 (T+7d): Aggressive maneuver, seizing initiative, neutralizing bottlenecks.\n"
            "   - Phase 3 (T+30d): Systemic consolidation, redundancy hardening, mission completion."
        ),
        "metadata": {
            "agency": "DOD_ARMY",
            "domain": "OODA_TEMPO_DECISION_SUPERIORITY",
            "classification": "UNCLASSIFIED_DOCTRINE",
            "focus": "OODA loop, decision tempo, phased courses of action",
        },
    },
    {
        "id": "DOC-DOD-MISSION-COMMAND-ROE",
        "agency": "DOD_ARMY",
        "doctrine_type": AgencyDoctrineType.DOD_ARMY_OODA_MISSION_COMMAND.value,
        "title": "DoD JP 5-0 Joint Planning, Mission Command (Auftragstaktik) & Rules of Engagement",
        "text": (
            "DOD JOINT PUBLICATION 5-0 & MISSION COMMAND DOCTRINE.\n"
            "1. Mission Command (Auftragstaktik): Directives specify the 'WHAT' (Commander's Intent and End State) and 'WHY', "
            "while delegating the 'HOW' to operators on the scene to foster disciplined initiative under fluid conditions.\n"
            "2. Rules of Engagement (ROE): Inviolable ethical, legal, and operational boundaries. Define what actions are strictly forbidden "
            "regardless of situational pressure (e.g., zero illegal wiretapping, zero budget overruns exceeding 15%, zero contractual breaches).\n"
            "3. Abort Criteria & Stop-Loss: Every operation must possess predetermined, emotionless exit tripwires. If casualty rate, drawdown, "
            "or key metric breaches the stop-loss limit, abort immediately to preserve capital and operational survival."
        ),
        "metadata": {
            "agency": "DOD_ARMY",
            "domain": "JOINT_PLANNING_MISSION_COMMAND_ROE",
            "classification": "UNCLASSIFIED_DOCTRINE",
            "focus": "Mission command, ROE guardrails, abort criteria",
        },
    },
]


def ingest_doctrinal_frameworks(
    persist_dir: str = "storage/chroma_db",
    export_graph_path: str = "storage/gotham_knowledge_graph.json",
) -> tuple[int, int]:
    """
    Ingests doctrinal texts into ChromaDB and registers canonical procedures into GothamKnowledgeGraph.
    Returns (num_docs_indexed, num_graph_nodes).
    """
    logger.info("[*] Initializing Doctrinal Knowledge Ingestion Engine...")
    vector_store = SovereignVectorStore(persist_directory=persist_dir)
    graph = GothamKnowledgeGraph()

    # Load existing graph if available
    graph_file = Path(export_graph_path)
    if graph_file.exists():
        try:
            with open(graph_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"[*] Loaded existing graph with {len(data.get('entities', {}))} entities.")
        except Exception as e:
            logger.warning(f"Could not load previous graph: {e}")

    # 1. Index Doctrinal Documents into Vector Store
    texts = [d["text"] for d in DOCTRINAL_CORPUS]
    metas = [d["metadata"] for d in DOCTRINAL_CORPUS]
    ids = [d["id"] for d in DOCTRINAL_CORPUS]

    vector_store.add_texts(texts=texts, metadatas=metas, ids=ids)
    logger.info(f"[+] Successfully indexed {len(texts)} core doctrinal frameworks into Vector Store.")

    # 2. Register Cross-Agency Doctrinal Procedures into Knowledge Graph
    procedures = [
        Procedure(
            id="PROC-NSA-SIGINT-01",
            name="NSA Telemetry Anomaly & Signal Triage",
            category=ProcedureCategory.CYBER,
            steps=[
                "Isolate cold telemetry metrics from qualitative noise",
                "Calculate historical variance and flag 2.5-sigma anomalies",
                "Model cyber attack vectors and telemetry packet flow",
                "Formulate clean signal vector for forensic escalation",
            ],
            restrictions=["No reliance on subjective opinion", "Verify all packet telemetry headers"],
            required_clearance=ClearanceLevel.SECRET,
            roe_guidelines="Adhere to strict data integrity protocols.",
        ),
        Procedure(
            id="PROC-FBI-FORENSIC-01",
            name="FBI Forensic Causal & Incentive Mapping",
            category=ProcedureCategory.COUNTER_INTELLIGENCE,
            steps=[
                "Identify all stakeholders in the causal network",
                "Trace capital, resource, and status flows ('Follow the Money')",
                "Assess M.I.C.E. vulnerabilities and conflicting payoffs",
                "Corroborate claims via independent second-source validation",
            ],
            restrictions=["Single-source assertions are invalid", "Do not ignore hidden conflicts of interest"],
            required_clearance=ClearanceLevel.CONFIDENTIAL,
            roe_guidelines="Strict adherence to evidentiary chain of custody.",
        ),
        Procedure(
            id="PROC-CIA-ACH-01",
            name="CIA Analysis of Competing Hypotheses (ACH)",
            category=ProcedureCategory.COVERT_ACTION,
            steps=[
                "Enumerate mutually exclusive hypotheses (H1, H2, H3)",
                "Build diagnostic evidence matrix to test disconfirmation",
                "Eliminate hypotheses with strongest disproving evidence",
                "Run Red Team deception and counter-bias stress test",
            ],
            restrictions=["Never select a hypothesis prior to matrix scoring", "Screen for adversary deception"],
            required_clearance=ClearanceLevel.TOP_SECRET,
            roe_guidelines="Maintain rigorous analytical neutrality.",
        ),
        Procedure(
            id="PROC-DOD-OODA-01",
            name="DoD Joint Planning & Fast-OODA Directive",
            category=ProcedureCategory.SURVEILLANCE,
            steps=[
                "Synthesize orientation from signals, incentives, and ACH",
                "Formulate phased COA: Phase 1 (T+24h), Phase 2 (T+7d), Phase 3 (T+30d)",
                "Define non-negotiable Rules of Engagement (ROE)",
                "Set deterministic Stop-Loss and mission abort criteria",
            ],
            restrictions=["Never launch action without clear abort criteria", "Do not breach defined ROE"],
            required_clearance=ClearanceLevel.SECRET,
            roe_guidelines="Mission Command: define intent and boundaries, delegate tactical execution.",
        ),
    ]

    for p in procedures:
        graph.add_object(p)

    # Link the 4 agency procedures in the canonical problem-solving chain
    links = [
        OntologyLink(
            source_id="PROC-NSA-SIGINT-01",
            source_type="Procedure",
            target_id="PROC-FBI-FORENSIC-01",
            target_type="Procedure",
            link_type=LinkType.CORRELATES_WITH,
            notes="NSA Signal Triage feeds raw objective telemetry into FBI Forensic Incentive Analysis.",
        ),
        OntologyLink(
            source_id="PROC-FBI-FORENSIC-01",
            source_type="Procedure",
            target_id="PROC-CIA-ACH-01",
            target_type="Procedure",
            link_type=LinkType.EVALUATES_HYPOTHESIS,
            notes="FBI Incentive and Actor Graph supplies diagnostic evidence to CIA ACH Matrix.",
        ),
        OntologyLink(
            source_id="PROC-CIA-ACH-01",
            source_type="Procedure",
            target_id="PROC-DOD-OODA-01",
            target_type="Procedure",
            link_type=LinkType.COMMANDS_ACTION,
            notes="CIA Selected Strategic Hypothesis determines DoD Phased Course of Action and ROE.",
        ),
    ]

    for l in links:
        graph.add_link(l)

    graph_file.parent.mkdir(parents=True, exist_ok=True)
    graph.save_to_file(str(graph_file))
    logger.info(f"[+] Knowledge Graph updated with {len(procedures)} procedures and {len(links)} links.")
    logger.info(f"[✓] Saved updated ontology graph to {graph_file}")

    return len(DOCTRINAL_CORPUS), len(graph.entities)


if __name__ == "__main__":
    docs_count, nodes_count = ingest_doctrinal_frameworks()
    print(f"\n[DONE] Ingestion Complete: {docs_count} Doctrinal Documents Indexed, {nodes_count} Graph Entities Registered.")
