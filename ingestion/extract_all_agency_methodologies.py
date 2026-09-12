"""
Sovereign Gotham - Full Cross-Agency Operational Methodology Miner
Exhaustively extracts problem-solving methodologies from:
  - ALL 58 NSA Cryptolog issues
  - ALL 16 US Army doctrine manuals & DTIC studies
  - ALL 3 DoD joint operational files
  - ALL FBI investigative files
  - Curated diverse CIA analytical reports (estimates, surveys, tech assessments)
Uses ThreadPoolExecutor to parallelize Gemini (AGY CLI) calls,
with thread-safe incremental persistence into Knowledge Graph, ChromaDB, and JSON catalog.
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ontology.graph import GothamKnowledgeGraph
from ontology.models import ClearanceLevel, Procedure, ProcedureCategory
from storage.vector_store import SovereignVectorStore

logger = logging.getLogger("SovereignGotham.FullExtractor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class FullAgencyMethodologyExtractor:
    def __init__(
        self,
        data_root: str = "D:/sovereign_gotham_data",
        output_catalog: str = "storage/extracted_agency_methodologies.json",
        max_workers: int = 5,
    ):
        self.data_root = Path(data_root)
        self.output_catalog = Path(output_catalog)
        self.output_catalog.parent.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self.lock = threading.Lock()

        # Load existing methodologies to avoid re-processing
        self.catalog: list[dict[str, Any]] = []
        self.processed_sources: set[str] = set()
        if self.output_catalog.exists():
            try:
                with open(self.output_catalog, "r", encoding="utf-8") as f:
                    self.catalog = json.load(f)
                    for item in self.catalog:
                        if "source_file" in item:
                            self.processed_sources.add(item["source_file"])
                logger.info(f"[*] Loaded {len(self.catalog)} existing methodologies. {len(self.processed_sources)} sources already processed.")
            except Exception as e:
                logger.warning(f"Failed loading existing catalog: {e}")

        self.graph = GothamKnowledgeGraph()
        self.vector_store = SovereignVectorStore(persist_directory="storage/chroma_db")

    def extract_single_doc(self, doc_path: Path, agency: str, max_chars: int = 4000) -> dict[str, Any] | None:
        """Invokes Gemini CLI to extract operational methodology from an authentic document."""
        filename = doc_path.name
        if filename in self.processed_sources:
            return None

        try:
            raw_text = doc_path.read_text(encoding="utf-8", errors="ignore")[:max_chars].strip()
            if len(raw_text) < 150:
                return None

            prompt = (
                f"You are Sovereign Gotham Chief Intelligence Ontologist.\n"
                f"Analyze this authentic declassified {agency} document excerpt:\n"
                f"Document Filename: {filename}\n"
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
                timeout=75,
            )

            if res.returncode == 0 and res.stdout:
                json_match = re.search(r"```json(.*?)```", res.stdout, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1).strip())
                    parsed["source_file"] = filename
                    return parsed
        except Exception as e:
            logger.warning(f"Error extracting {filename}: {e}")
        return None

    def save_methodology(self, method_data: dict[str, Any]):
        """Thread-safe persistence into catalog, ChromaDB, and Knowledge Graph."""
        with self.lock:
            self.catalog.append(method_data)
            self.processed_sources.add(method_data["source_file"])
            agency = method_data.get("agency", "UNKNOWN")
            idx = len(self.catalog)

            # Vector Store Indexing
            text_blob = (
                f"{agency} OPERATIONAL METHODOLOGY: {method_data.get('method_name')}\n"
                f"Domain: {method_data.get('doctrine_domain')}\n"
                f"Principles: {', '.join(method_data.get('core_principles', []))}\n"
                f"Algorithmic Workflow:\n"
                + "\n".join(f" - {s}" for s in method_data.get("algorithmic_steps", []))
                + f"\nReal World Application: {method_data.get('real_world_application')}"
            )
            doc_id = f"DOC-METHOD-{agency}-{idx:04d}"
            try:
                self.vector_store.add_texts(
                    texts=[text_blob],
                    metadatas=[{
                        "id": doc_id,
                        "agency": agency,
                        "classification": "UNCLASSIFIED_DOCTRINE",
                        "method_name": method_data.get("method_name", "Unknown"),
                        "source_file": method_data["source_file"],
                    }],
                    ids=[doc_id],
                )
            except Exception as ve:
                logger.warning(f"ChromaDB insert warning: {ve}")

            # Knowledge Graph Procedure Node
            proc_cat = (
                ProcedureCategory.CYBER if "CYBER" in str(method_data.get("doctrine_domain"))
                else ProcedureCategory.SURVEILLANCE
            )
            proc = Procedure(
                id=f"PROC-{agency}-{idx:04d}",
                name=method_data.get("method_name", "Operational Method"),
                category=proc_cat,
                steps=method_data.get("algorithmic_steps", []),
                restrictions=method_data.get("inviolable_rules", []),
                required_clearance=ClearanceLevel.SECRET,
                roe_guidelines=method_data.get("real_world_application"),
            )
            self.graph.add_object(proc)

            # Save catalog to disk incrementally
            with open(self.output_catalog, "w", encoding="utf-8") as f:
                json.dump(self.catalog, f, indent=2, ensure_ascii=False)

    def run_full_harvest(self):
        """Executes full harvest across all authentic data folders."""
        tasks: list[tuple[Path, str]] = []

        # 1. NSA - All 58 files
        nsa_folder = self.data_root / "nsa"
        if nsa_folder.exists():
            for f in sorted(nsa_folder.glob("*.txt")):
                if f.name not in self.processed_sources:
                    tasks.append((f, "NSA"))

        # 2. US Army - All 16 files
        army_folder = self.data_root / "army"
        if army_folder.exists():
            for f in sorted(army_folder.glob("*.txt")):
                if f.name not in self.processed_sources:
                    tasks.append((f, "DOD_ARMY"))

        # 3. DoD - All 3 files
        dod_folder = self.data_root / "dod"
        if dod_folder.exists():
            for f in sorted(dod_folder.glob("*.txt")):
                if f.name not in self.processed_sources:
                    tasks.append((f, "DOD"))

        # 4. FBI - All files
        fbi_folder = self.data_root / "fbi"
        if fbi_folder.exists():
            for f in sorted(fbi_folder.glob("*.txt")):
                if f.name not in self.processed_sources:
                    tasks.append((f, "FBI"))

        # 5. CIA CREST - Select top 25 high-value analytical files
        cia_folder = self.data_root / "crest_batch"
        if cia_folder.exists():
            cia_all = sorted(cia_folder.glob("*.txt"))
            # Prioritize surveys, bulletins, estimates, and situation reports
            keywords = ["Survey", "Bulletin", "Digest", "Situation", "Estimate", "Memorandum"]
            curated_cia = [f for f in cia_all if any(k.lower() in f.name.lower() for k in keywords) and f.name not in self.processed_sources]
            tasks.extend([(f, "CIA") for f in curated_cia[:25]])

        logger.info(f"[+] Total pending files to process: {len(tasks)} (across NSA, Army, DoD, FBI, CIA)")

        if not tasks:
            logger.info("[✓] All target documents have already been extracted.")
            return

        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.extract_single_doc, doc_path, agency): (doc_path, agency)
                for doc_path, agency in tasks
            }
            for future in concurrent.futures.as_completed(future_to_file):
                doc_path, agency = future_to_file[future]
                completed += 1
                try:
                    result = future.result()
                    if result:
                        self.save_methodology(result)
                        logger.info(f"[{completed}/{len(tasks)}] [✓] ({agency}) {result.get('method_name')}")
                    else:
                        logger.info(f"[{completed}/{len(tasks)}] [-] ({agency}) {doc_path.name} (no structured methodology)")
                except Exception as exc:
                    logger.warning(f"[{completed}/{len(tasks)}] [!] Error processing {doc_path.name}: {exc}")

        # Final Knowledge Graph save
        self.graph.save_to_file("storage/gotham_knowledge_graph.json")
        logger.info(f"\n[✓] FULL HARVEST COMPLETE! Total methodologies in catalog: {len(self.catalog)}")


if __name__ == "__main__":
    extractor = FullAgencyMethodologyExtractor(max_workers=4)
    extractor.run_full_harvest()
