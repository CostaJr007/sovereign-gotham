import subprocess

prompt = """You are an intelligence data synthesizer for Sovereign Gotham.
Analyze this CIA record: CIA-RDP96-00788R001700210016-5 on Project Grill Flame.

Output your response with these exact sections:
[REASONING_CHAIN]
1. Ingestion: Provenance verification and authenticity checks.
2. Threat Vectors: Identify active risks and Soviet counter-intel infiltration.
3. Ontological Grounding: Link Fort Meade asset to Project Grill Flame in Gotham graph.
4. Strategic Decision: Formulate containment directives.
[/REASONING_CHAIN]

```json
{
  "document_id": "CIA-RDP96-00788R001700210016-5",
  "threat_rating": "HIGH",
  "course_of_action": ["Audit OPSEC log", "Compartmentalize telemetry asset"],
  "compliance_status": "PERMITTED",
  "confidence_score": 0.92
}
```"""

proc = subprocess.run(
    ["agy", "--model", "gemini-3.8-flash-high", "-p", prompt],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
    timeout=60,
)

print("[+] Result:\n", proc.stdout)
