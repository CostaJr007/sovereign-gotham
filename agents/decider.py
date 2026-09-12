"""
Sovereign Gotham - Operational Decision Engine (Palantir Decider Pattern)
Integrates Knowledge Graph topology, Vector RAG, Risk Modeling, and ROE Compliance.
"""

from __future__ import annotations

import uuid
from typing import Any

from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    CourseOfAction,
    EvaluateRiskRequest,
    EvaluateRiskResponse,
    Procedure,
    RecommendActionRequest,
    RecommendActionResponse,
    RiskLevel,
    Target_Entity,
    ValidateComplianceRequest,
)
from storage.sqlite_store import OperationalLedger
from storage.vector_store import SovereignVectorStore

from .compliance import ComplianceEngine
from .llm_provider import SovereignLLMProvider


class GothamDecisionEngine:
    """
    Main analytic agent synthesizing Ontological Reasoning (OAG).
    Evaluates tactical scenarios and simulates responses strictly adherent to protocol.
    """

    def __init__(
        self,
        graph: GothamKnowledgeGraph,
        vector_store: SovereignVectorStore,
        ledger: OperationalLedger,
        llm_provider: SovereignLLMProvider | None = None,
    ):
        self.graph = graph
        self.vector_store = vector_store
        self.ledger = ledger
        self.compliance_engine = ComplianceEngine(graph)
        self.llm_provider = llm_provider or SovereignLLMProvider()

    def evaluate_risk(self, request: EvaluateRiskRequest) -> EvaluateRiskResponse:
        """
        Quantifies operational and collateral risk based on target threat, procedure domain, and context.
        """
        base_score = 25.0
        factors = []
        mitigations = []

        # Target factor
        if request.target_id:
            target = self.graph.get_object(request.target_id)
            if isinstance(target, Target_Entity):
                threat_val = target.threat_level.value if hasattr(target.threat_level, "value") else str(target.threat_level)
                if threat_val == "CRITICAL":
                    base_score += 35.0
                    factors.append(f"Target '{target.name}' holds CRITICAL threat tier.")
                elif threat_val == "HIGH":
                    base_score += 25.0
                    factors.append(f"Target '{target.name}' flagged with HIGH threat rating.")
                elif threat_val == "MEDIUM":
                    base_score += 15.0
                    factors.append(f"Target '{target.name}' classified as MEDIUM threat.")

        # Procedure factor
        if request.procedure_id:
            proc = self.graph.get_object(request.procedure_id)
            if isinstance(proc, Procedure):
                cat_val = proc.category.value if hasattr(proc.category, "value") else str(proc.category)
                if cat_val in ["EXTRACTION", "COVERT_ACTION"]:
                    base_score += 20.0
                    factors.append(f"Kinetic/exfiltration domain '{cat_val}' introduces high friction.")
                elif cat_val in ["SURVEILLANCE", "CYBER"]:
                    base_score += 10.0
                    mitigations.append("Passive collection reduces kinetic exposure.")

        # Environmental & contextual vectors
        ctx = request.context or {}
        if ctx.get("is_daytime", False):
            base_score += 10.0
            factors.append("Daylight operation increases risk of visual exposure.")
        else:
            mitigations.append("Night envelope provides visual concealment.")

        if ctx.get("in_hostile_sector", True):
            base_score += 15.0
            factors.append("Operating within non-permissive hostile jurisdiction.")
        else:
            mitigations.append("Friendly or neutral sector lowers intercept probability.")

        score = min(max(base_score, 5.0), 99.0)

        if score >= 75.0:
            level = RiskLevel.EXTREME
            acceptable = False
        elif score >= 50.0:
            level = RiskLevel.HIGH
            acceptable = True
        elif score >= 30.0:
            level = RiskLevel.MODERATE
            acceptable = True
        else:
            level = RiskLevel.LOW
            acceptable = True

        return EvaluateRiskResponse(
            risk_level=level,
            risk_score=score,
            risk_factors=factors or ["Standard operational baseline variance."],
            mitigations=mitigations or ["Continuous telemetry and visual monitoring."],
            acceptable=acceptable,
        )

    def recommend_action(
        self,
        request: RecommendActionRequest,
        context: dict[str, Any] | None = None,
    ) -> RecommendActionResponse:
        """
        Executes Palantir Gotham Ontological Course of Action (COA) recommendation.
        Crosses Knowledge Graph topology + Vector memory + ROE Compliance.
        """
        session_id = f"GOTHAM-SESSION-{uuid.uuid4().hex[:8].upper()}"
        ctx = context or {}

        # 1. Resolve Target
        target = self.graph.get_object(request.target_id)
        if not target or not isinstance(target, Target_Entity):
            raise ValueError(f"Target Entity '{request.target_id}' not found in sovereign ontology.")

        # 2. Discover Candidate Procedures from Graph Topology
        candidates = self.graph.find_procedures_for_target(target.id)

        # If no direct target link, pull all registered procedures in ontology
        if not candidates:
            all_procs = [p for p in self.graph.entities.values() if isinstance(p, Procedure)]
            candidates = [(p, 0.5) for p in all_procs]

        if not candidates:
            raise ValueError("No operational procedures cataloged in Gotham ontology.")

        # 3. Vector Similarity Search over declassified intelligence chunks
        search_hits = self.vector_store.similarity_search(request.scenario, top_k=3)
        relevant_text_ids = [h.get("id") for h in search_hits]

        # 4. Rank Candidate Procedures (Topological Score + Vector Score)
        scored_candidates = []
        for proc, topo_conf in candidates:
            match_score = topo_conf
            # Keyword or vector resonance bonus
            proc_text = f"{proc.name} {proc.category} {' '.join(proc.steps)}".lower()
            scen_words = set(request.scenario.lower().split())
            overlap = len(scen_words.intersection(set(proc_text.split())))
            match_score += min(overlap * 0.05, 0.4)

            scored_candidates.append((proc, match_score))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        chosen_proc, best_score = scored_candidates[0]

        # 5. Execute Compliance and ROE Audit
        cat_str = str(chosen_proc.category.value if hasattr(chosen_proc.category, "value") else chosen_proc.category)
        action_name = f"Authorize{cat_str.replace('_', ' ').title().replace(' ', '')}"
        compliance_req = ValidateComplianceRequest(
            action_name=action_name,
            procedure_id=chosen_proc.id,
            agent_role_id=request.agent_role_id,
            context=ctx,
        )
        compliance_res = self.compliance_engine.validate(compliance_req)

        # 6. Execute Quantitative Risk Evaluation
        risk_req = EvaluateRiskRequest(
            scenario=request.scenario,
            target_id=target.id,
            procedure_id=chosen_proc.id,
            context=ctx,
        )
        risk_res = self.evaluate_risk(risk_req)

        # 7. Gather Causal Evidence Chain (Ontology Links)
        evidence_chain = self.graph.get_links(target_id=target.id) + self.graph.get_links(
            source_id=chosen_proc.id
        )

        evidence_summaries = [
            f"({l.source_id}) -[:{l.link_type}]-> ({l.target_id})" for l in evidence_chain[:4]
        ]

        # 8. Synthesize Doctrinal Rationale via Local Sovereign LLM
        rationale = self.llm_provider.generate_tactical_rationale(
            scenario=request.scenario,
            target_name=target.name,
            procedure_name=chosen_proc.name,
            steps=chosen_proc.steps,
            restrictions=chosen_proc.restrictions,
            violations=compliance_res.violations,
            graph_links_summary=evidence_summaries,
        )

        # 9. Format Action Directives
        coa_steps = []
        for idx, step in enumerate(chosen_proc.steps, 1):
            precaution = (
                chosen_proc.restrictions[idx - 1]
                if idx - 1 < len(chosen_proc.restrictions)
                else "Maintain operational security and secure communications."
            )
            coa_steps.append(
                CourseOfAction(
                    step_number=idx,
                    directive=step,
                    precaution=precaution,
                )
            )

        # 10. Record in Relational Ledger
        self.ledger.record_decision(
            session_id=session_id,
            scenario=request.scenario,
            target_id=target.id,
            agent_role_id=request.agent_role_id,
            recommended_procedure_id=chosen_proc.id,
            risk_level=risk_res.risk_level.value,
            risk_score=risk_res.risk_score,
            compliance_status=compliance_res.roe_status,
            violations=compliance_res.violations,
            rationale=rationale,
        )

        return RecommendActionResponse(
            recommended_procedure_id=chosen_proc.id,
            procedure_name=chosen_proc.name,
            course_of_action=coa_steps,
            rationale=rationale,
            evidence_chain=evidence_chain,
            risk_assessment=risk_res,
            compliance_validation=compliance_res,
            sovereignty_proof={
                "session_id": session_id,
                "offline_mode": True,
                "graph_topology_nodes": len(self.graph.entities),
                "graph_topology_edges": len(self.graph.links),
            },
        )
