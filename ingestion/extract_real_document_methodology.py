"""
Sovereign Gotham - Automated Real Document Methodology Extractor
Leverages Gemini (AGY CLI) to read authentic documents across agencies:
  - NSA: Cryptolog Technical Series, Signals Triage, Ciphers
  - DoD / US Army: Combat Doctrine, Joint Planning, OODA, Sustainment
  - FBI: Investigative Case Files, Forensic Procedures, Asset Tracking
  - CIA: CREST Analytical Dispatches, Intelligence Estimates, Tradecraft
Extracts formal operational problem-solving workflows and indexes them
into the Gotham Ontological Graph and ChromaDB Vector Store.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ontology.graph import GothamKnowledgeGraph
from ontology.models import (
    ClearanceLevel,
    LinkType,
    OntologyLink,
    Procedure,
    ProcedureCategory,
)
from storage.vector_store import SovereignVectorStore

logger = logging.getLogger("SovereignGotham.DocumentMethodologyExtractor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class RealDocumentMethodologyExtractor:
    """
    Automates extraction of pure problem-solving methodologies from real documents.
    """

    def __init__(
        self,
        data_root: str = "D:/sovereign_gotham_data",
        output_catalog: str = "storage/extracted_agency_methodologies.json",
    ):
        self.data_root = Path(data_root)
        self.output_catalog = Path(output_catalog)
        self.output_catalog.parent.mkdir(parents=True, exist_ok=True)
        self.graph = GothamKnowledgeGraph()
        self.vector_store = SovereignVectorStore(persist_directory="storage/chroma_db")

    def extract_methodology_with_gemini(
        self, doc_path: Path, agency: str, max_chars: int = 3500
    ) -> dict[str, Any] | None:
        """Invokes Gemini via AGY CLI to extract the methodology from raw text."""
        try:
            raw_text = doc_path.read_text(encoding="utf-8", errors="ignore")[:max_chars].strip()
            if len(raw_text) < 200:
                return None

            prompt = (
                f"You are Sovereign Gotham Chief Intelligence Ontologist.\n"
                f"Analyze this authentic declassified {agency} document excerpt:\n"
                f"Document Filename: {doc_path.name}\n"
                f"----------------------------------------\n"
                f"{raw_text}\n"
                f"----------------------------------------\n"
                f"Task:\n"
                f"1. Extract the operational PROBLEM-SOLVING METHODOLOGY, WORKFLOW, or HEURISTIC embedded in this text.\n"
                f"   Focus on HOW problems are diagnosed, decomposed, filtered, or executed, not on trivial historical trivia.\n"
                f"2. Formulate how this exact {agency} methodology solves real-world modern challenges (in business, engineering, logistics, cybersecurity, or personal strategy).\n"
                f"3. Return strictly valid JSON inside a ```json ... ``` codeblock with this exact structure:\n"
                f"{{\n"
                f'  "method_name": "Concise Descriptive Name of the Method",\n'
                f'  "agency": "{agency}",\n'
                f'  "doctrine_domain": "CYBER / FORENSIC / STRATEGIC / OPERATIONS / SIGNAL",\n'
                f'  "core_principles": ["Principle 1", "Principle 2"],\n'
                f'  "algorithmic_steps": ["Step 1", "Step 2", "Step 3", "Step 4"],\n'
                f'  "inviolable_rules": ["Boundary rule 1", "Boundary rule 2"],\n'
                f'  "real_world_application": "How this applies to modern business/tech problem solving"\n'
                f"}}\n"
            )

            res = subprocess.run(
                ["agy", "--model", "gemini-3.8-flash-high", "-p", prompt],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=90,
            )

            if res.returncode == 0 and res.stdout:
                json_match = re.search(r"```json(.*?)```", res.stdout, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1).strip())
                    parsed["source_file"] = str(doc_path.name)
                    return parsed
        except Exception as e:
            logger.warning(f"Failed extracting methodology for {doc_path.name}: {e}")
        return None

    def run_harvest(self, limit_per_agency: int = 5) -> list[dict[str, Any]]:
        """Harvests methodologies across NSA, Army, FBI, and CIA real files."""
        logger.info("[*] Starting Cross-Agency Real Document Methodology Extraction...")
        extracted_catalog: list[dict[str, Any]] = []

        agency_folders = {
            "NSA": self.data_root / "nsa",
            "DOD_ARMY": self.data_root / "army",
            "CIA": self.data_root / "crest_batch",
            "DOD": self.data_root / "dod",
            "FBI": self.data_root / "fbi",
        }

        for agency, folder in agency_folders.items():
            if not folder.exists():
                continue
            txt_files = list(folder.glob("*.txt"))[:limit_per_agency]
            logger.info(f"[*] Processing {len(txt_files)} real files for {agency}...")

            for f in txt_files:
                logger.info(f"    -> Analyzing {f.name} via Gemini...")
                method_data = self.extract_methodology_with_gemini(f, agency)
                if method_data:
                    extracted_catalog.append(method_data)
                    logger.info(f"       [✓] Extracted: {method_data.get('method_name')}")

                    # Index into ChromaDB Vector Store
                    text_blob = (
                        f"{agency} OPERATIONAL METHODOLOGY: {method_data.get('method_name')}\n"
                        f"Domain: {method_data.get('doctrine_domain')}\n"
                        f"Principles: {', '.join(method_data.get('core_principles', []))}\n"
                        f"Algorithmic Workflow:\n"
                        + "\n".join(f" - {s}" for s in method_data.get("algorithmic_steps", []))
                        + f"\nReal World Application: {method_data.get('real_world_application')}"
                    )
                    doc_id = f"DOC-METHOD-{agency}-{len(extracted_catalog):03d}"
                    self.vector_store.add_texts(
                        texts=[text_blob],
                        metadatas=[{
                            "id": doc_id,
                            "agency": agency,
                            "classification": "UNCLASSIFIED_DOCTRINE",
                            "method_name": method_data.get("method_name", "Unknown"),
                            "source_file": f.name,
                        }],
                        ids=[doc_id],
                    )

                    # Register as Procedure in Knowledge Graph
                    proc_cat = ProcedureCategory.CYBER if "CYBER" in str(method_data.get("doctrine_domain")) else ProcedureCategory.SURVEILLANCE
                    proc = Procedure(
                        id=f"PROC-{agency}-{len(extracted_catalog):03d}",
                        name=method_data.get("method_name", "Operational Method"),
                        category=proc_cat,
                        steps=method_data.get("algorithmic_steps", []),
                        restrictions=method_data.get("inviolable_rules", []),
                        required_clearance=ClearanceLevel.SECRET,
                        roe_guidelines=method_data.get("real_world_application"),
                    )
                    self.graph.add_object(proc)

        # Save complete extracted catalog
        with open(self.output_catalog, "w", encoding="utf-8") as f:
            json.dump(extracted_catalog, f, indent=2, ensure_ascii=False)

        # Persist updated graph
        self.graph.save_to_file("storage/gotham_knowledge_graph.json")
        logger.info(f"[+] Total Methodologies Extracted and Grounded: {len(extracted_catalog)}")
        logger.info(f"[✓] Saved catalog to {self.output_catalog}")
        return extracted_catalog


if __name__ == "__main__":
    extractor = RealDocumentMethodologyExtractor()
    results = extractor.run_harvest(limit_per_agency=4)
    print(f"\n[DONE] Extracted {len(results)} methodologies from real agency documents.")
