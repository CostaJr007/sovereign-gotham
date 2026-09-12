"""
Sovereign Gotham - Master Multi-Agency Mass Ingestion Pipeline
Executes high-throughput concurrent harvesting across all intelligence and defense feeds:
  1. CIA: Declassified CREST Collection
  2. NSA: Cryptolog Technical Journals (SIGINT/Cyber/TEMPEST)
  3. U.S. Army & Marines: Field Manuals (FM series) & Doctrine
  4. FBI: Live Wanted API targets + Declassified investigations
Saves directly to Drive D: (D:/sovereign_gotham_data/) with SHA-256 custody hashes.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

try:
    _project_root = str(Path(__file__).resolve().parent.parent)
except NameError:
    _project_root = str(Path(".").resolve())

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import httpx

from ingestion.scrapers.internet_archive_crest import InternetArchiveCIABatchHarvester
from ingestion.scrapers.multi_agency_harvester import MultiAgencyIntelligenceHarvester
from ontology.graph import GothamKnowledgeGraph
from training.dataset_generator import OntologicalDatasetGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SovereignGotham.MassPipeline")


def harvest_fbi_wanted_database(output_dir: Path, target_count: int = 150) -> int:
    """Harvests live investigated suspects directly from the official FBI Wanted REST API."""
    fbi_dir = output_dir / "fbi"
    fbi_dir.mkdir(parents=True, exist_ok=True)
    out_file = fbi_dir / "fbi_wanted_suspects.json"

    collected = []
    page = 1
    logger.info(f"Connecting to FBI Wanted REST API (Target: {target_count} suspects)...")

    with httpx.Client(timeout=20.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
        while len(collected) < target_count:
            try:
                resp = client.get("https://api.fbi.gov/wanted/v1/list", params={"page": page, "pageSize": 50})
                if resp.status_code != 200:
                    break
                data = resp.json()
                items = data.get("items", [])
                if not items:
                    break

                for it in items:
                    suspect = {
                        "uid": it.get("uid"),
                        "title": it.get("title"),
                        "aliases": it.get("aliases"),
                        "description": it.get("description"),
                        "details": it.get("details"),
                        "caution": it.get("caution"),
                        "field_offices": it.get("field_offices"),
                        "subjects": it.get("subjects"),
                        "warning_message": it.get("warning_message"),
                        "publication": it.get("publication"),
                    }
                    collected.append(suspect)
                    if len(collected) >= target_count:
                        break

                page += 1
            except Exception as e:
                logger.error(f"Error fetching FBI page {page}: {e}")
                break

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(collected, f, indent=2, ensure_ascii=False)

    logger.info(f"[✓] Successfully harvested {len(collected)} FBI wanted records to {out_file}")
    return len(collected)


def run_mass_pipeline():
    logger.info("==========================================================================")
    logger.info("     SOVEREIGN GOTHAM // MULTI-AGENCY MASS HARVESTING OPERATION")
    logger.info("==========================================================================")

    base_dir = Path("D:/sovereign_gotham_data") if Path("D:/").exists() else Path("./data/sovereign_gotham_data")
    base_dir.mkdir(parents=True, exist_ok=True)

    harvester = MultiAgencyIntelligenceHarvester(output_dir=base_dir)
    cia_harvester = InternetArchiveCIABatchHarvester(output_dir=base_dir / "crest_batch")

    # 1. Harvest CIA CREST Batch (150 docs)
    logger.info("\n[*] PHASE 1: Harvesting CIA CREST Declassified Archive (150 records)...")
    cia_docs = cia_harvester.harvest_batch(count=150, page=2, max_workers=16)
    logger.info(f"[✓] CIA Phase Complete: {len(cia_docs)} documents harvested.")

    # 2. Harvest NSA Cryptolog Batch (20 volumes)
    logger.info("\n[*] PHASE 2: Harvesting NSA Cryptolog Technical Journal Series (20 volumes)...")
    nsa_docs = harvester.harvest_agency("NSA", count=20, page=2, max_workers=16)
    logger.info(f"[✓] NSA Phase Complete: {len(nsa_docs)} volumes harvested.")

    # 3. Harvest U.S. Army & Military Doctrine (20 manuals)
    logger.info("\n[*] PHASE 3: Harvesting U.S. Army & Military Doctrine Manuals (20 manuals)...")
    army_docs = harvester.harvest_agency("ARMY", count=20, page=1, max_workers=16)
    logger.info(f"[✓] Army Phase Complete: {len(army_docs)} manuals harvested.")

    # 4. Harvest FBI Wanted API (150 suspects)
    logger.info("\n[*] PHASE 4: Harvesting FBI Official Wanted Suspect Database (150 suspects)...")
    fbi_count = harvest_fbi_wanted_database(base_dir, target_count=150)

    # 5. Recompile DeepSeek-R1 Super-Dataset
    logger.info("\n[*] PHASE 5: Compiling Consolidated Intelligence Training Dataset...")
    graph = GothamKnowledgeGraph()
    generator = OntologicalDatasetGenerator(graph)
    results = generator.generate_all(Path("training_data"))

    total_samples = results.get("unified_deepseek_r1_agent", 0)
    logger.info("==========================================================================")
    logger.info(f"MASS INGESTION COMPLETE: {total_samples} Total Training Samples Ready for DeepSeek-R1!")
    logger.info("Target VRAM Allocation: 10 GB (batch_size=2, max_seq_length=4096, lora_r=32)")
    logger.info("==========================================================================")


if __name__ == "__main__":
    run_mass_pipeline()
