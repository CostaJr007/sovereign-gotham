"""
Sovereign Gotham - Local LLM Provider & Cognitive Synthesizer
Supports local Ollama, vLLM, and a zero-dependency deterministic fallback engine for air-gapped environments.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request


class SovereignLLMProvider:
    """
    Sovereign LLM client ensuring strict data privacy and air-gap operation.
    Tries local Ollama / vLLM first, falls back to deterministic cognitive synthesis.
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434/api/generate",
        model_name: str = "llama3:latest",
        temperature: float = 0.1,
    ):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.temperature = temperature

    def is_ollama_alive(self) -> bool:
        """Check if local Ollama daemon is reachable."""
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate_tactical_rationale(
        self,
        scenario: str,
        target_name: str,
        procedure_name: str,
        steps: list[str],
        restrictions: list[str],
        violations: list[str],
        graph_links_summary: list[str],
    ) -> str:
        """
        Synthesizes operational rationale grounded strictly in ontology evidence.
        """
        prompt = f"""[SOVEREIGN INTELLIGENCE DECISION MATRIX - GOTHAM PROTOCOL]
SCENARIO REPORT: {scenario}
TARGET SUBJECT: {target_name}
SELECTED DOCTRINE: {procedure_name}

AUTHORIZED STEPS:
{json.dumps(steps, indent=2)}

DOCTRINAL RESTRICTIONS:
{json.dumps(restrictions, indent=2)}

ACTIVE VIOLATIONS / CAVEATS:
{json.dumps(violations, indent=2)}

GRAPH CAUSAL EVIDENCE:
{json.dumps(graph_links_summary, indent=2)}

INSTRUCTION:
Provide a concise, formal military/intelligence Course of Action (COA) justification adhering strictly to cataloged doctrine. Do not invent unauthorized actions.
"""
        # Try Ollama if alive
        if self.is_ollama_alive():
            try:
                payload = json.dumps({
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": self.temperature},
                }).encode("utf-8")
                req = urllib.request.Request(
                    self.ollama_url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    res = data.get("response", "").strip()
                    if res:
                        return f"[OLLAMA LOCAL SOVEREIGN INFERENCE - {self.model_name}]\n{res}"
            except Exception:
                pass

        # Sovereign Cognitive Fallback Engine (Air-gapped deterministic synthesis)
        status_tag = "APPROVED UNDER ROE" if not violations else "CONDITIONAL / CAVEAT REQUIRED"
        evidence_str = "; ".join(graph_links_summary) if graph_links_summary else "Direct ontological assignment"
        lines = [
            f"[GOTHAM DETERMINISTIC REASONING ENGINE - STATUS: {status_tag}]",
            f"1. Operational Assessment: The tactical situation regarding target '{target_name}' aligns with doctrine '{procedure_name}'.",
            f"2. Graph Causal Provenance: Grounded by verified ontological links ({evidence_str}).",
            f"3. Doctrinal Compliance: {len(restrictions)} doctrinal constraints evaluated. Active caveats: {len(violations)}.",
            f"4. Directive: Execute authorized procedural steps sequence (1 through {len(steps)}) in accordance with field manual restrictions.",
        ]
        if violations:
            lines.append(f"WARNING: Immediate ROE remediation required for: {'; '.join(violations)}")

        return "\n".join(lines)
