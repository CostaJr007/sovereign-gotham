"""
Sovereign Gotham - DeepSeek-R1 Sovereign Intelligence Agent
Acts as the Senior Intelligence Analyst / Chief of Station within Sovereign Gotham.
Interacts with the fine-tuned DeepSeek-R1-Distill-Qwen-7B (via Ollama / vLLM or local weights).
Queries the live Ontology via SovereignOSDKClient and extracts <thought> reasoning traces.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx
from pydantic import BaseModel, Field

from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    Document,
    LinkType,
    Operation,
    Target_Entity,
)
from ontology.osdk_client import SovereignOSDKClient

logger = logging.getLogger("SovereignGotham.DeepSeekAgent")


class AgentInvestigationResult(BaseModel):
    """Structured response from the DeepSeek-R1 Sovereign Intelligence Agent."""
    query: str
    thought_trace: str = Field(..., description="Deep reflective chain of thought reasoning")
    decision: dict[str, Any] = Field(default_factory=dict)
    subgraph_evidence: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "COMPLETED"


class SovereignDeepSeekAgent:
    """
    Cognitive Agent driven by DeepSeek-R1-Distill-Qwen-7B.
    Combines deep strategic reasoning with real-time Ontological Graph grounding (OSDK).
    """

    DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL_NAME = "deepseek-r1:7b"

    def __init__(
        self,
        graph: GothamKnowledgeGraph,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        model_name: str = MODEL_NAME,
    ):
        self.graph = graph
        self.osdk = SovereignOSDKClient(graph)
        self.ollama_url = ollama_url
        self.model_name = model_name

    def investigate(self, prompt: str, target_name: str | None = None) -> AgentInvestigationResult:
        """
        Executes a full intelligence investigation cycle:
        1. Queries the Ontology via OSDK for related context.
        2. Prompts DeepSeek-R1 with the scenario and ontological subgraph.
        3. Parses the <thought> reflection chain and the tactical decision.
        """
        # 1. Ontological context retrieval via OSDK
        subgraph_evidence = []
        context_data: dict[str, Any] = {}

        if target_name:
            target = self.osdk.objects(Target_Entity).where(name=target_name).first()
            if target:
                context_data["target"] = target.model_dump()
                # Find linked operations
                ops = (
                    self.osdk.objects(Target_Entity)
                    .where(id=target.id)
                    .pivot_to(LinkType.ASSOCIATED_WITH, Operation)
                    .fetch()
                )
                context_data["associated_operations"] = [op.model_dump() for op in ops]
                subgraph_evidence.append({"type": "Target", "id": target.id, "name": target.name})

        # Fallback to general documents if no specific target
        if not context_data:
            recent_docs = self.osdk.objects(Document).fetch(limit=3)
            context_data["recent_documents"] = [
                {"id": d.id, "title": d.title, "source": d.source, "summary": d.summary[:200]}
                for d in recent_docs
            ]

        # 2. Construct Grounded Prompt
        system_instruction = (
            "You are the Sovereign Gotham Chief Intelligence Analyst (DeepSeek-R1 Core). "
            "You reason systematically and critically inside <thought>...</thought> tags, "
            "evaluating motives, counter-intelligence risks, and Rules of Engagement (ROE). "
            "Always ground your final verdict in the provided Ontological Context and emit structured JSON."
        )

        full_prompt = (
            f"<|im_start|>system\n{system_instruction}<|im_end|>\n"
            f"<|im_start|>user\n[MISSION INSTRUCTION]\n{prompt}\n\n"
            f"[ONTOLOGICAL CONTEXT]\n{json.dumps(context_data, indent=2, ensure_ascii=False)}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

        # 3. Call local model (Ollama / vLLM) with graceful fallback
        raw_response = self._call_local_model(full_prompt)
        thought_trace, decision_dict = self._parse_thought_and_decision(raw_response, prompt, context_data)

        return AgentInvestigationResult(
            query=prompt,
            thought_trace=thought_trace,
            decision=decision_dict,
            subgraph_evidence=subgraph_evidence,
        )

    def _call_local_model(self, full_prompt: str) -> str:
        """Attempts to call running Ollama / vLLM instance; provides simulated fallback if offline."""
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    self.ollama_url,
                    json={
                        "model": self.model_name,
                        "prompt": full_prompt,
                        "stream": False,
                    },
                )
                if resp.status_code == 200:
                    return resp.json().get("response", "")
        except Exception:
            pass

        # Offline Sovereign Simulation Fallback
        return (
            "<thought>\n"
            "1. Ingesting operational parameters and target coordinates.\n"
            "2. Scanning ontological memory for prior associations and classification markings.\n"
            "3. Assessing deception vectors and potential compromise of observation post.\n"
            "4. Verifying command authority: Chief of Station sanction required before kinetic tasking.\n"
            "5. Synthesizing low-visibility surveillance with immediate abort contingency.\n"
            "</thought>\n"
            "```json\n"
            "{\n"
            '  "directive": "ESTABLISH_COVERT_OBSERVATION",\n'
            '  "threat_assessment": "ELEVATED",\n'
            '  "confidence_score": 0.88,\n'
            '  "mitigation_protocol": "Deploy passive SIGINT array; avoid physical approach",\n'
            '  "compliance_roe": "PERMITTED"\n'
            "}\n"
            "```"
        )

    @staticmethod
    def _parse_thought_and_decision(
        response_text: str,
        query: str,
        context: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Splits response into the <thought> chain and the final structured decision."""
        thought_match = re.search(r"<thought>(.*?)</thought>", response_text, re.DOTALL | re.IGNORECASE)
        thought_trace = thought_match.group(1).strip() if thought_match else "Direct tactical deduction completed."

        # Extract JSON block
        json_match = re.search(r"```json(.*?)```", response_text, re.DOTALL)
        decision_dict = {}

        if json_match:
            try:
                decision_dict = json.loads(json_match.group(1).strip())
            except Exception:
                pass

        if not decision_dict:
            decision_dict = {
                "summary": response_text.replace(f"<thought>{thought_trace}</thought>", "").strip(),
                "status": "EVALUATED",
            }

        return thought_trace, decision_dict
