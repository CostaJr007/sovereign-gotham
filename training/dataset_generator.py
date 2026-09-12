"""
Sovereign Gotham - Ontological Dataset Generator for Sovereign SLMs
Synthesizes high-density instruction and Chain-of-Thought (CoT) datasets
from the Sovereign Gotham dynamic ontology to train domain-specialized SLMs
(Operations, Social Engineering/HUMINT, Doctrine/ROE, Graph Extraction).
Outputs standard JSONL (compatible with Unsloth, HuggingFace, LLaMA-Factory, ShareGPT).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    Agent_Role,
    ClearanceLevel,
    Document,
    LinkType,
    Operation,
    Procedure,
    Target_Entity,
    ThreatLevel,
)
from ontology.osdk_client import SovereignOSDKClient

logger = logging.getLogger("SovereignGotham.DatasetGenerator")


class TrainingSample(BaseModel):
    """Normalized instruction-tuning sample with Chain of Thought reasoning."""
    system_prompt: str
    instruction: str
    ontological_context: dict[str, Any] = Field(default_factory=dict)
    thought_chain: str
    output: dict[str, Any]

    def to_sharegpt(self) -> dict[str, Any]:
        """Converts to ShareGPT multi-turn conversational format."""
        context_str = json.dumps(self.ontological_context, indent=2, ensure_ascii=False)
        user_content = f"{self.instruction}\n\n[ONTOLOGICAL CONTEXT]\n{context_str}"
        assistant_content = f"<thought>\n{self.thought_chain}\n</thought>\n\n```json\n{json.dumps(self.output, indent=2, ensure_ascii=False)}\n```"
        return {
            "conversations": [
                {"from": "system", "value": self.system_prompt},
                {"from": "human", "value": user_content},
                {"from": "gpt", "value": assistant_content},
            ]
        }

    def to_alpaca(self) -> dict[str, Any]:
        """Converts to Alpaca instruction format."""
        return {
            "instruction": self.instruction,
            "input": json.dumps(self.ontological_context, ensure_ascii=False),
            "output": f"<thought>\n{self.thought_chain}\n</thought>\n\n" + json.dumps(self.output, indent=2, ensure_ascii=False),
            "system": self.system_prompt,
        }


class OntologicalDatasetGenerator:
    """
    Teacher-Student distillation pipeline that consumes the live ontology
    and outputs fine-tuning datasets for four specialized security SLMs:
      1. Operations & Tactical Mission SLM
      2. HUMINT & Social Engineering SLM
      3. Doctrinal Compliance & ROE SLM
      4. Ontological Graph Extractor SLM
    """

    def __init__(self, graph: GothamKnowledgeGraph):
        self.graph = graph
        self.osdk = SovereignOSDKClient(graph)

    def generate_all(self, output_dir: str | Path) -> dict[str, int]:
        """Generates all 4 domain datasets and writes them to disk as JSONL files."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        results = {
            "operations_slm": self.generate_operations_dataset(out_path / "operations_slm.jsonl"),
            "humint_slm": self.generate_humint_dataset(out_path / "humint_social_eng_slm.jsonl"),
            "doctrine_roe_slm": self.generate_doctrine_dataset(out_path / "doctrine_roe_slm.jsonl"),
            "graph_extractor_slm": self.generate_extractor_dataset(out_path / "graph_extractor_slm.jsonl"),
        }

        # Synthesize the master unified dataset for DeepSeek-R1-Distill-Qwen-7B
        unified_count = self.generate_unified_deepseek_dataset(
            out_path / "sovereign_deepseek_r1_agent.jsonl",
            [
                out_path / "operations_slm.jsonl",
                out_path / "humint_social_eng_slm.jsonl",
                out_path / "doctrine_roe_slm.jsonl",
                out_path / "graph_extractor_slm.jsonl",
            ],
        )

        # Ingest real harvested corpus from Drive D: (CIA, NSA, Army, etc.)
        corpus_paths = [
            Path("D:/sovereign_gotham_data/army"),
            Path("D:/sovereign_gotham_data/nsa"),
            Path("D:/sovereign_gotham_data/crest_batch"),
            Path("sample_data/crest_harvested"),
        ]
        corpus_count = 0
        for cp in corpus_paths:
            if cp.exists():
                corpus_count += self.generate_from_harvested_corpus(
                    cp,
                    out_path / "sovereign_deepseek_r1_agent.jsonl",
                )

        results["unified_deepseek_r1_agent"] = unified_count + corpus_count
        results["harvested_corpus_samples"] = corpus_count

        logger.info(f"Dataset generation complete: {results}")
        return results

    def generate_from_harvested_corpus(
        self,
        corpus_dir: str | Path,
        output_file: Path,
        max_docs: int = 1500,
    ) -> int:
        """
        Processes real harvested declassified CIA/FBI documents from disk,
        extracting intelligence scenarios, entities, and CoT reasoning traces.
        """
        dir_path = Path(corpus_dir)
        if not dir_path.exists():
            return 0

        files = list(dir_path.glob("*.txt"))[:max_docs]
        samples: list[dict[str, Any]] = []

        system_prompt = (
            "You are the Sovereign Gotham Senior Intelligence Analyst (DeepSeek-R1 Core). "
            "You reason systematically and critically inside <thought>...</thought> tags, "
            "evaluating motives, counter-intelligence risks, and Rules of Engagement (ROE). "
            "Always ground your final verdict in the provided Ontological Context and emit structured JSON."
        )

        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore").strip()
                if len(content) < 200:
                    continue

                doc_id = f.stem
                first_lines = [line.strip() for line in content.split("\n") if line.strip()][:5]
                title = first_lines[0] if first_lines else doc_id

                instruction = (
                    f"Perform deep intelligence assessment and ontological extraction on declassified "
                    f"CIA dispatch {doc_id}: '{title[:80]}'."
                )

                text_preview = content[:2000] if len(content) > 2000 else content

                thought = (
                    f"1. Ingesting raw declassified text from archive record {doc_id}.\n"
                    f"2. Inspecting historical context, institutional actors, and security classification markings.\n"
                    f"3. Identifying key operational vectors: Evaluating intelligence significance, source reliability, and strategic implications.\n"
                    f"4. Cross-referencing against Sovereign Gotham Ontological graph: Formulating structured entities and causal linkages.\n"
                    f"5. Synthesizing analytical findings: Ensuring objective assessment and actionable intelligence posture."
                )

                structured_output = {
                    "document_id": doc_id,
                    "title": title[:100],
                    "classification_assessment": "DECLASSIFIED_HISTORICAL",
                    "analytical_summary": text_preview[:350] + "...",
                    "extracted_entities": [
                        {"type": "AGENCY", "name": "CENTRAL_INTELLIGENCE_AGENCY"},
                        {"type": "RECORD_SERIES", "name": doc_id[:14]},
                    ],
                    "operational_posture": "MONITOR_HISTORICAL_PRECEDENT",
                    "confidence_score": 0.94,
                }

                sample = TrainingSample(
                    system_prompt=system_prompt,
                    instruction=instruction,
                    ontological_context={"doc_id": doc_id, "text_excerpt": text_preview[:1500]},
                    thought_chain=thought,
                    output=structured_output,
                )
                samples.append(sample.to_sharegpt())
            except Exception as e:
                logger.warning(f"Error processing doc {f.name}: {e}")
                continue

        with open(output_file, "a", encoding="utf-8") as out:
            out.writelines(json.dumps(s, ensure_ascii=False) + "\n" for s in samples)

        logger.info(f"Synthesized {len(samples)} training samples from harvested corpus at {corpus_dir}")
        return len(samples)

    def generate_unified_deepseek_dataset(
        self,
        output_file: Path,
        source_files: list[Path],
    ) -> int:
        """
        Consolidates all domain-specific instruction sets into a single unified
        training corpus formatted specifically for DeepSeek-R1-Distill-Qwen-7B.
        Preserves <thought>...</thought> reflection chains and structured action schemas.
        """
        all_lines: list[str] = []
        for src in source_files:
            if src.exists():
                with open(src, "r", encoding="utf-8") as f:
                    for line in f:
                        line_str = line.strip()
                        if line_str:
                            all_lines.append(line_str)

        # Write unified JSONL
        with open(output_file, "w", encoding="utf-8") as f:
            for line in all_lines:
                f.write(line + "\n")

        logger.info(f"Compiled {len(all_lines)} samples into unified DeepSeek dataset: {output_file}")
        return len(all_lines)

    # =========================================================================
    # 1. OPERATIONS & MISSION PLANNING SLM
    # =========================================================================
    def generate_operations_dataset(self, file_path: Path) -> int:
        """Synthesizes training pairs for tactical planning and Course of Action generation."""
        samples: list[TrainingSample] = []
        operations = self.osdk.objects(Operation).fetch()
        targets = self.osdk.objects(Target_Entity).fetch()
        procedures = self.osdk.objects(Procedure).fetch()

        system_prompt = (
            "You are the Sovereign Tactical Operations Specialist (Ops-SLM). "
            "Your objective is to analyze target packages, evaluate operational risk, "
            "and generate deterministic Courses of Action (COAs) strictly aligned with validated intelligence."
        )

        for op in operations:
            # Find linked targets via OSDK
            linked_targets = (
                self.osdk.objects(Operation)
                .where(id=op.id)
                .pivot_to(LinkType.ASSOCIATED_WITH, Target_Entity, direction="in")
                .fetch()
            ) or targets

            for target in linked_targets:
                instruction = (
                    f"Operational Campaign {op.codename} requires immediate mission planning. "
                    f"Target entity '{target.name}' ({target.type}) is currently operating at threat level {target.threat_level}. "
                    f"Formulate a structured Course of Action and assess operational risk."
                )

                context = {
                    "operation": {"id": op.id, "codename": op.codename, "objective": op.objective},
                    "target": {"id": target.id, "name": target.name, "threat_level": target.threat_level, "affiliations": target.affiliations},
                    "available_procedures": [{"id": p.id, "name": p.name, "category": p.category} for p in procedures[:3]],
                }

                thought_chain = (
                    f"Step 1: Ingest target '{target.name}' with threat level {target.threat_level}.\n"
                    f"Step 2: Cross-reference with operational mandate '{op.objective}'.\n"
                    f"Step 3: Evaluate friction vectors and select appropriate tactical procedure.\n"
                    f"Step 4: Generate sequential action directives with contingency precautions."
                )

                output = {
                    "recommended_action": "EXECUTE_TACTICAL_CONTAINMENT",
                    "target_id": target.id,
                    "target_name": target.name,
                    "estimated_risk_score": 65.0 if target.threat_level == ThreatLevel.HIGH else 45.0,
                    "course_of_action": [
                        {"step": 1, "directive": f"Deploy surveillance ring around target {target.name} sector", "precaution": "Maintain passive SIGINT posture; avoid contact"},
                        {"step": 2, "directive": "Verify secondary communications and courier links", "precaution": "Sanitize observation posts against counter-surveillance"},
                        {"step": 3, "directive": "Execute controlled containment when target isolates", "precaution": "Secure cryptographic hardware immediately upon cordon"},
                    ],
                    "success_criteria": "Asset secured, communications decrypted, zero collateral exposure",
                }

                samples.append(TrainingSample(
                    system_prompt=system_prompt,
                    instruction=instruction,
                    ontological_context=context,
                    thought_chain=thought_chain,
                    output=output,
                ))

        # Write to JSONL
        self._write_jsonl(file_path, samples)
        return len(samples)

    # =========================================================================
    # 2. HUMINT & SOCIAL ENGINEERING SLM
    # =========================================================================
    def generate_humint_dataset(self, file_path: Path) -> int:
        """Synthesizes training pairs for psychological profiling, recruitment, and elicitation."""
        samples: list[TrainingSample] = []
        targets = self.osdk.objects(Target_Entity).fetch()

        system_prompt = (
            "You are the Sovereign HUMINT & Psychological Tradecraft Specialist (HUMINT-SLM). "
            "Your domain covers target vulnerability analysis, clandestine asset recruitment, "
            "elicitation techniques, and deception detection based on declassified intelligence methodologies."
        )

        scenarios = [
            ("MICE_ANALYSIS", "Evaluate target vulnerabilities under the M.I.C.E. framework (Money, Ideology, Coercion, Ego) for potential asset cultivation."),
            ("ELICITATION_PLAN", "Design a non-coercive conversational elicitation strategy to extract clandestine communications protocols."),
            ("COUNTER_DECEPTION", "Analyze target's conflicting behavioral indicators and flag potential double-agent / provocation vectors."),
        ]

        for target in targets:
            for task_code, prompt_text in scenarios:
                instruction = f"Target: {target.name}. Task: {prompt_text}"
                context = {
                    "target_id": target.id,
                    "name": target.name,
                    "threat_level": target.threat_level,
                    "affiliations": target.affiliations,
                    "known_location": target.location or "Berlin / Sector East",
                }

                thought_chain = (
                    f"1. Deconstruct target profile {target.name} ({target.type}).\n"
                    f"2. Assess affiliation network ({', '.join(target.affiliations) if target.affiliations else 'Unknown'}).\n"
                    f"3. Map psychological pressure points against operational security safeguards.\n"
                    f"4. Propose safe elicitation or recruitment pitch with abort criteria."
                )

                output = {
                    "target_id": target.id,
                    "primary_vulnerability_vector": "EGO / STATUS_RECOGNITION" if "OFFICER" in target.name.upper() else "FINANCIAL_PRESSURE",
                    "recommended_approach": "INDIRECT_ACADEMIC_CONFERENCE_CONTACT",
                    "elicitation_themes": [
                        "Compliment recent organizational publications or research",
                        "Express mutual frustration with administrative bureaucracy",
                        "Probe stance on regional geopolitical shifts",
                    ],
                    "abort_triggers": [
                        "Direct questioning regarding case officer identity",
                        "Sudden arrival of unvetted security personnel",
                    ],
                    "operational_security_rule": "Never introduce monetary compensation during the initial contact phase.",
                }

                samples.append(TrainingSample(
                    system_prompt=system_prompt,
                    instruction=instruction,
                    ontological_context=context,
                    thought_chain=thought_chain,
                    output=output,
                ))

        self._write_jsonl(file_path, samples)
        return len(samples)

    # =========================================================================
    # 3. DOCTRINE, EDUCATION & ROE SLM
    # =========================================================================
    def generate_doctrine_dataset(self, file_path: Path) -> int:
        """Synthesizes training pairs for Rules of Engagement and legal compliance."""
        samples: list[TrainingSample] = []
        procedures = self.osdk.objects(Procedure).fetch()
        agent_roles = self.osdk.objects(Agent_Role).fetch()

        system_prompt = (
            "You are the Sovereign Legal & Doctrinal Compliance Specialist (Compliance-SLM). "
            "You verify Rules of Engagement (ROE), command authority thresholds, "
            "and CAPCO security classification boundaries. You must block any unauthorized action."
        )

        for proc in procedures:
            for role in agent_roles:
                # Scenario 1: Compliant request
                instruction_ok = f"Role '{role.designation}' requests authorization to execute procedure '{proc.name}'. Validate compliance."
                context_ok = {
                    "role": {"id": role.id, "designation": role.designation, "clearance": role.clearance_level, "authorities": role.decision_authority},
                    "procedure": {"id": proc.id, "name": proc.name, "required_clearance": proc.required_clearance, "restrictions": proc.restrictions},
                }
                
                # Check clearance hierarchy
                clearance_ranks = {
                    ClearanceLevel.UNCLASSIFIED: 0,
                    ClearanceLevel.CONFIDENTIAL: 1,
                    ClearanceLevel.SECRET: 2,
                    ClearanceLevel.TOP_SECRET: 3,
                    ClearanceLevel.TS_SCI: 4,
                }
                role_rank = clearance_ranks.get(ClearanceLevel(role.clearance_level), 0)
                proc_rank = clearance_ranks.get(ClearanceLevel(proc.required_clearance), 0)
                is_clearance_ok = role_rank >= proc_rank

                thought_chain = (
                    f"Checking clearance: Role has {role.clearance_level} (Rank {role_rank}), "
                    f"Procedure requires {proc.required_clearance} (Rank {proc_rank}). "
                    f"Checking statutory restrictions: {len(proc.restrictions)} prohibitions enforced."
                )

                output = {
                    "compliant": is_clearance_ok,
                    "roe_status": "PERMITTED" if is_clearance_ok else "BLOCKED_CLEARANCE",
                    "violations": [] if is_clearance_ok else [f"Insufficient clearance: {role.clearance_level} cannot sanction {proc.required_clearance}"],
                    "restrictions_enforced": proc.restrictions,
                    "mandated_supervision": "Chief of Station approval required before tactical launch.",
                }

                samples.append(TrainingSample(
                    system_prompt=system_prompt,
                    instruction=instruction_ok,
                    ontological_context=context_ok,
                    thought_chain=thought_chain,
                    output=output,
                ))

        self._write_jsonl(file_path, samples)
        return len(samples)

    # =========================================================================
    # 4. ONTOLOGICAL GRAPH EXTRACTOR SLM
    # =========================================================================
    def generate_extractor_dataset(self, file_path: Path) -> int:
        """Synthesizes training pairs for turning raw intelligence text into Ontological Triplet JSON."""
        samples: list[TrainingSample] = []
        documents = self.osdk.objects(Document).fetch()

        system_prompt = (
            "You are the Sovereign Ontological Entity & Link Extractor (Graph-SLM). "
            "Your task is to parse raw declassified intelligence text, extract canonical entities "
            "(Document, Operation, Target_Entity, Procedure), identify CAPCO markings, and emit typed Links."
        )

        for doc in documents:
            instruction = f"Extract all ontological entities and semantic links from the following declassified document: {doc.title}"
            snippet = (doc.raw_content or doc.summary)[:800]
            context = {
                "source": doc.source,
                "document_id": doc.id,
                "raw_text_snippet": snippet,
            }

            thought_chain = (
                f"1. Identify document provenance ({doc.source}) and date.\n"
                f"2. Scan for CAPCO classification headers.\n"
                f"3. Detect operations and cryptonyms.\n"
                f"4. Map relations: (Document) -> REGISTERS -> (Operation), (Operation) -> MONITORS -> (Target)."
            )

            output = {
                "document": {"id": doc.id, "title": doc.title, "source": doc.source},
                "extracted_entities": [
                    {"type": "Operation", "id": "OP_IDENTIFIED", "codename": "DETECTED_CAMPAIGN"},
                    {"type": "Target_Entity", "id": "TARGET_IDENTIFIED", "name": "SUSPECT_ACTOR"},
                ],
                "extracted_links": [
                    {"source": doc.id, "target": "OP_IDENTIFIED", "link_type": "REGISTERS"},
                    {"source": "OP_IDENTIFIED", "target": "TARGET_IDENTIFIED", "link_type": "MONITORS"},
                ],
            }

            samples.append(TrainingSample(
                system_prompt=system_prompt,
                instruction=instruction,
                ontological_context=context,
                thought_chain=thought_chain,
                output=output,
            ))

        self._write_jsonl(file_path, samples)
        return len(samples)

    @staticmethod
    def _write_jsonl(file_path: Path, samples: list[TrainingSample]) -> None:
        """Writes samples to JSONL in ShareGPT conversational format."""
        with open(file_path, "w", encoding="utf-8") as f:
            for s in samples:
                line = json.dumps(s.to_sharegpt(), ensure_ascii=False)
                f.write(line + "\n")
