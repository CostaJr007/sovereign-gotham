"""
Sovereign Gotham - Hugging Face Bulk CIA Declassified Harvester
Downloads the complete pre-packaged CIA collection from Hugging Face:
  Repository: manus4oHER/cia-declassified-reading-room
  Batches: 337 compressed JSONL.GZ files (~16,850 documents)
Decompresses and indexes all documents into D:/sovereign_gotham_data/crest_batch.
"""

from __future__ import annotations

import gzip
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

try:
    _project_root = str(Path(__file__).resolve().parent.parent.parent)
except NameError:
    _project_root = str(Path(".").resolve())

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SovereignGotham.HFCIAHarvester")


class HuggingFaceCIABulkHarvester:
    REPO_API = "https://huggingface.co/api/datasets/manus4oHER/cia-declassified-reading-room"
    RESOLVE_BASE = "https://huggingface.co/datasets/manus4oHER/cia-declassified-reading-room/resolve/main"

    def __init__(self, output_dir: str | Path = "D:/sovereign_gotham_data/crest_batch"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {"User-Agent": "SovereignGotham-DefenseResearch/2.0"}

    def get_all_batch_urls(self) -> list[str]:
        """Queries Hugging Face API to list all 337 compressed text batch files."""
        logger.info("Discovering all CIA batch files from Hugging Face repository...")
        with httpx.Client(timeout=25.0, headers=self.headers, follow_redirects=True) as client:
            resp = client.get(self.REPO_API)
            if resp.status_code != 200:
                logger.error(f"Failed to query HF API: HTTP {resp.status_code}")
                return []
            data = resp.json()
            siblings = data.get("siblings", [])
            batch_files = [
                s["rfilename"]
                for s in siblings
                if "cia-collection" in s["rfilename"] and s["rfilename"].endswith("texts.jsonl.gz")
            ]
            logger.info(f"Discovered {len(batch_files)} CIA collection batch archives.")
            return batch_files

    def download_and_extract_batch(self, batch_rfilename: str, client: httpx.Client) -> int:
        """Downloads a single .jsonl.gz batch file, decompresses, and writes text files."""
        url = f"{self.RESOLVE_BASE}/{batch_rfilename}"
        try:
            resp = client.get(url)
            if resp.status_code != 200:
                return 0

            decompressed = gzip.decompress(resp.content).decode("utf-8", errors="ignore")
            lines = decompressed.strip().split("\n")
            extracted_count = 0

            for line in lines:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    ident = record.get("identifier") or record.get("cia_document_id")
                    text = record.get("text", "").strip()

                    if not ident or len(text) < 200:
                        continue

                    # Sanitize filename
                    safe_ident = "".join(c for c in str(ident) if c.isalnum() or c in ("-", "_")).strip()
                    if not safe_ident:
                        continue

                    dest_file = self.output_dir / f"{safe_ident}.txt"
                    dest_file.write_text(text, encoding="utf-8")
                    extracted_count += 1
                except Exception:
                    continue

            return extracted_count
        except Exception as e:
            logger.error(f"Error extracting batch {batch_rfilename}: {e}")
            return 0

    def download_complete_archive(self, max_workers: int = 24) -> dict[str, Any]:
        """Downloads and decompresses the entire collection concurrently."""
        batch_files = self.get_all_batch_urls()
        if not batch_files:
            return {"batches": 0, "documents": 0}

        total_batches = len(batch_files)
        logger.info(f"Starting concurrent download of {total_batches} batch files using {max_workers} threads...")

        limits = httpx.Limits(max_keepalive_connections=32, max_connections=64)
        client = httpx.Client(timeout=40.0, headers=self.headers, follow_redirects=True, limits=limits)

        total_extracted = 0
        completed_batches = 0

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_batch = {
                    executor.submit(self.download_and_extract_batch, b, client): b
                    for b in batch_files
                }
                for future in as_completed(future_to_batch):
                    completed_batches += 1
                    res = future.result()
                    total_extracted += res
                    if completed_batches % 25 == 0 or completed_batches == total_batches:
                        logger.info(
                            f"Progress: [{completed_batches}/{total_batches}] batches processed | "
                            f"{total_extracted} total CIA documents unpacked so far..."
                        )
        finally:
            client.close()

        logger.info(f"[✓] BULK CIA HARVEST COMPLETE: {total_extracted} documents extracted from {total_batches} batches.")
        return {
            "total_batches": total_batches,
            "total_documents_extracted": total_extracted,
            "output_directory": str(self.output_dir),
        }


if __name__ == "__main__":
    harvester = HuggingFaceCIABulkHarvester()
    res = harvester.download_complete_archive()
    print("Final Bulk Ingestion Result:", res)
