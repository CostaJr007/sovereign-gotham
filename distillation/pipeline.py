"""
Sovereign Gotham - Distillation Pipeline Orchestrator
Executes the full pipeline: Raw Ingestion -> Teacher Reasoning (AGY Gemini / Heuristic) -> DSpark Curation -> Student-Ready Dataset.
Features stateful tracking to skip already-processed documents across runs.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

try:
    _curr = Path(__file__).resolve()
    PROJECT_ROOT = _curr.parent.parent if _curr.parent.name == "distillation" else _curr.parent
except NameError:
    PROJECT_ROOT = Path(".").resolve()

if not (PROJECT_ROOT / "distillation").exists():
    fallback = Path(r"c:\Users\adeil\.gemini\antigravity\scratch\sovereign_gotham")
    if fallback.exists():
        PROJECT_ROOT = fallback

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from distillation.config import DistillationConfig, default_distill_config
from distillation.curator_filter import DistillationCuratorFilter
from distillation.teacher_engine import DistillationTeacherEngine, RawDistillSample
from ontology.graph import GothamKnowledgeGraph
from ontology.models import Operation, Target_Entity, ThreatLevel

import signal
import time

logger = logging.getLogger("SovereignGotham.DistillPipeline")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def build_sample_ontology() -> GothamKnowledgeGraph:
    """Pre-populates knowledge graph with standard Gotham intelligence nodes."""
    graph = GothamKnowledgeGraph()
    
    # Target Entities
    targets = [
        Target_Entity(id="T-01", name="STASI_SIGNAL_STATION_CHARLIE", type="INFRASTRUCTURE", threat_level=ThreatLevel.HIGH, affiliations=["EAST_BLOC_MINISTRY_STATE_SECURITY"]),
        Target_Entity(id="T-02", name="KGB_DEPARTMENT_V_LIAISON", type="INDIVIDUAL", threat_level=ThreatLevel.CRITICAL, affiliations=["KGB_FIRST_CHIEF_DIRECTORATE"]),
        Target_Entity(id="T-03", name="COVERT_FINANCIAL_HUB_ZURICH", type="ORGANIZATION", threat_level=ThreatLevel.MEDIUM, affiliations=["FRONT_COMPANY_NETWORK"]),
        Target_Entity(id="T-04", name="PROJECT_STARGATE_REMOTE_ASSET", type="INDIVIDUAL", threat_level=ThreatLevel.LOW, affiliations=["INSCOM_GRILL_FLAME"]),
        Target_Entity(id="T-05", name="PROJECT_MKULTRA_MONTREAL_LAB", type="INFRASTRUCTURE", threat_level=ThreatLevel.CRITICAL, affiliations=["ALLAN_MEMORIAL_INSTITUTE"]),
    ]
    for t in targets:
        graph.add_object(t)

    # Operations
    operations = [
        Operation(id="OP-01", codename="OP_CHOPIN", objective="Intercept and decipher diplomatic signals in Sector East"),
        Operation(id="OP-02", codename="OP_AEGIS_SHIELD", objective="Neutralize covert HUMINT networks penetrating NATO logistics"),
        Operation(id="OP-03", codename="PROJECT_MKULTRA_ARCHIVE", objective="Catalog and declassify behavioral control methodologies"),
        Operation(id="OP-04", codename="PROJECT_GRILL_FLAME", objective="Monitor parapsychological and telemetry remote sensing programs"),
    ]
    for op in operations:
        graph.add_object(op)

    return graph


def discover_candidate_files(config: DistillationConfig) -> list[Path]:
    """Discovers all eligible document files across all configured data lakes."""
    candidate_files: list[Path] = []
    data_lake = config.harvested_data_dir

    if data_lake.exists():
        # Scan all subdirectories (crest_batch, nsa, army, dod, fbi, etc.)
        for txt_file in data_lake.rglob("*.txt"):
            candidate_files.append(txt_file)

    sample_dir = PROJECT_ROOT / "sample_data" / "crest_harvested"
    if sample_dir.exists():
        candidate_files.extend(list(sample_dir.glob("*.txt")))

    # Deduplicate paths while preserving order
    seen: set[str] = set()
    unique_candidates: list[Path] = []
    for p in candidate_files:
        if p.name not in seen:
            seen.add(p.name)
            unique_candidates.append(p)

    return unique_candidates


def run_pipeline(
    limit: int = 50,
    continuous: bool = False,
    batch_size: int = 10,
    engine: str = "agy",
    model: str = "gemini-3.8-flash-high",
    config: DistillationConfig = default_distill_config,
) -> int:
    """
    Executes end-to-end distillation synthesis and curation.
    Supports continuous streaming micro-batches with atomic progress tracking.
    """
    start_time = time.time()
    logger.info("==========================================================================")
    logger.info("   SOVEREIGN GOTHAM // CONTINUOUS KNOWLEDGE DISTILLATION PIPELINE")
    logger.info("==========================================================================")
    logger.info(f"Storage Root: {config.storage_root}")
    logger.info(f"Teacher Engine: {engine.upper()} (Model: {model})")
    logger.info(f"Execution Mode: {'CONTINUOUS (Exhaust entire archive)' if continuous else f'BATCH (Limit: {limit})'}")
    logger.info(f"Micro-Batch Size: {batch_size} documents per commit")
    logger.info(f"Target Student: {config.student_model_id}")
    logger.info(f"Hardware Target: {config.gpu_name}")

    # Graceful shutdown handler
    shutdown_requested = False

    def handle_sigint(sig, frame):
        nonlocal shutdown_requested
        logger.warning("\n[!] Graceful shutdown requested (Ctrl+C). Completing current batch and flushing state...")
        shutdown_requested = True

    signal.signal(signal.SIGINT, handle_sigint)

    # 1. State Tracking (Resume where we left off)
    tracker_file = config.storage_root / "processed_files.json"
    processed_ids: set[str] = set()
    if tracker_file.exists():
        try:
            processed_ids = set(json.loads(tracker_file.read_text(encoding="utf-8")))
            logger.info(f"State Tracker: Found {len(processed_ids)} previously distilled documents. Skipping duplicates.")
        except Exception as e:
            logger.warning(f"Could not load tracker file: {e}")

    # 2. Initialize Graph & Engines
    graph = build_sample_ontology()
    teacher = DistillationTeacherEngine(graph, agy_model=model)
    curator = DistillationCuratorFilter(config)

    # 3. Gather Candidates
    all_candidates = discover_candidate_files(config)
    logger.info(f"Total archive files discovered in data lake: {len(all_candidates)}")

    # Filter out already processed documents
    pending_candidates: list[Path] = [f for f in all_candidates if f.stem not in processed_ids]
    logger.info(f"Pending documents awaiting distillation: {len(pending_candidates)}")

    if not pending_candidates:
        logger.info("[✓] All discovered documents have already been distilled! Nothing new to process.")
        return 0

    # Determine execution scope
    target_docs = pending_candidates if continuous or limit <= 0 else pending_candidates[:limit]
    total_to_process = len(target_docs)
    logger.info(f"Target queue size for this run: {total_to_process} documents")

    all_entities = list(graph.entities.values()) if hasattr(graph, "entities") else []
    target_objs = [e for e in all_entities if isinstance(e, Target_Entity)]
    op_objs = [e for e in all_entities if isinstance(e, Operation)]

    telemetry_dir = config.storage_root / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    status_file = telemetry_dir / "continuous_distillation_status.json"

    total_approved = 0
    total_rejected = 0
    processed_this_session = 0

    # Process in streaming micro-batches
    for batch_start in range(0, total_to_process, batch_size):
        if shutdown_requested:
            logger.info("[!] Halting distillation loop per user request.")
            break

        batch_files = target_docs[batch_start : batch_start + batch_size]
        batch_raw_samples: list[RawDistillSample] = []
        batch_processed_ids: list[str] = []

        for idx_in_batch, f in enumerate(batch_files):
            if shutdown_requested:
                break

            overall_idx = batch_start + idx_in_batch + 1
            doc_id = f.stem

            try:
                txt = f.read_text(encoding="utf-8", errors="replace").strip()
                if len(txt) < 150:
                    logger.debug(f"Skipping {doc_id}: Content too short ({len(txt)} chars)")
                    processed_ids.add(doc_id)
                    continue

                rec = {
                    "doc_id": doc_id,
                    "title": txt.splitlines()[0][:90] if txt.splitlines() else doc_id,
                    "body": txt,
                    "classification": "DECLASSIFIED",
                }

                t = target_objs[(overall_idx - 1) % len(target_objs)] if target_objs else None
                o = op_objs[(overall_idx - 1) % len(op_objs)] if op_objs else None

                pct = (overall_idx / total_to_process) * 100
                logger.info(f"[{overall_idx}/{total_to_process}] ({pct:.1f}%) Distilling via {engine.upper()}: {doc_id}...")

                if engine == "agy":
                    sample = teacher.synthesize_with_agy_cli(rec, target=t, operation=o)
                else:
                    sample = teacher.synthesize_ontological_reasoning(rec, target=t, operation=o)

                batch_raw_samples.append(sample)
                batch_processed_ids.append(doc_id)
                processed_this_session += 1

            except Exception as e:
                logger.warning(f"Error processing {doc_id}: {e}")
                batch_processed_ids.append(doc_id)

        # Curate and commit micro-batch to disk
        if batch_raw_samples:
            app, rej = curator.curate_and_export(batch_raw_samples, append=True)
            total_approved += app
            total_rejected += rej

        # Update and persist state tracker
        for pid in batch_processed_ids:
            processed_ids.add(pid)
        tracker_file.write_text(json.dumps(sorted(list(processed_ids)), indent=2), encoding="utf-8")

        # Telemetry snapshot
        elapsed = time.time() - start_time
        rate = processed_this_session / elapsed if elapsed > 0 else 0
        rem_docs = total_to_process - processed_this_session
        eta_sec = rem_docs / rate if rate > 0 else 0
        eta_str = f"{int(eta_sec // 3600)}h {int((eta_sec % 3600) // 60)}m"

        telemetry_data = {
            "status": "STOPPED" if shutdown_requested else "RUNNING",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_archive": len(all_candidates),
            "total_processed_all_time": len(processed_ids),
            "processed_this_session": processed_this_session,
            "session_approved": total_approved,
            "session_rejected": total_rejected,
            "progress_percent": round((len(processed_ids) / len(all_candidates)) * 100, 2) if all_candidates else 0.0,
            "rate_docs_per_minute": round(rate * 60, 2),
            "eta": eta_str,
        }
        status_file.write_text(json.dumps(telemetry_data, indent=2), encoding="utf-8")

        total_in_master = 0
        if config.curated_dataset_path.exists():
            total_in_master = len(config.curated_dataset_path.read_text(encoding="utf-8").splitlines())

        logger.info(
            f"[Commit] Batch committed. Master Dataset: {total_in_master} samples | Speed: {rate*60:.1f} doc/min | ETA: {eta_str}"
        )

    total_in_master = 0
    if config.curated_dataset_path.exists():
        total_in_master = len(config.curated_dataset_path.read_text(encoding="utf-8").splitlines())

    logger.info("==========================================================================")
    logger.info("[✓] Distillation Run Concluded!")
    logger.info(f" - Processed This Session: {processed_this_session}")
    logger.info(f" - Approved by Curator: {total_approved}")
    logger.info(f" - Rejected by Curator: {total_rejected}")
    logger.info(f" - Cumulative Processed Archive: {len(processed_ids)} / {len(all_candidates)}")
    logger.info(f" - Master Dataset Total: {total_in_master} samples")
    logger.info(f" - Dataset Path: {config.curated_dataset_path}")
    logger.info("==========================================================================")
    return total_approved


def parse_args():
    parser = argparse.ArgumentParser(description="Sovereign Gotham Distillation Pipeline")
    parser.add_argument("--continuous", action="store_true", help="Run continuously until the entire archive is exhausted")
    parser.add_argument("--limit", type=int, default=50, help="Max document samples to process (ignored if --continuous is set)")
    parser.add_argument("--batch-size", type=int, default=10, help="Micro-batch commit size (default: 10)")
    parser.add_argument("--engine", type=str, choices=["agy", "heuristic"], default="agy", help="Teacher engine")
    parser.add_argument("--model", type=str, default="gemini-3.8-flash-high", help="AGY teacher model")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        limit=args.limit,
        continuous=args.continuous,
        batch_size=args.batch_size,
        engine=args.engine,
        model=args.model,
    )

