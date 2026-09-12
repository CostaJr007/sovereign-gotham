"""
Sovereign Gotham - SQLite Operational Ledger & Audit Store
Maintains tamper-evident audit trail of all ingestion events, decision queries,
and compliance validations with WAL (Write-Ahead Logging) enabled.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class OperationalLedger:
    """Air-gapped relational ledger for audit logs, decisions, and system provenance."""

    def __init__(self, db_path: str = "storage/gotham_audit.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        """Initialize database schema for operational ledger."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS ingestion_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    provenance_hash TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    entities_extracted INTEGER DEFAULT 0,
                    links_created INTEGER DEFAULT 0,
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS decision_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    scenario TEXT NOT NULL,
                    target_id TEXT,
                    agent_role_id TEXT,
                    recommended_procedure_id TEXT,
                    risk_level TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    compliance_status TEXT NOT NULL,
                    violations TEXT, -- JSON array
                    rationale TEXT,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS compliance_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_name TEXT NOT NULL,
                    procedure_id TEXT NOT NULL,
                    agent_role_id TEXT NOT NULL,
                    compliant INTEGER NOT NULL, -- 0 or 1
                    violations TEXT, -- JSON array
                    roe_status TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def record_ingestion(
        self,
        document_id: str,
        source: str,
        provenance_hash: str,
        classification: str,
        entities_count: int,
        links_count: int,
    ) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO ingestion_log 
                (document_id, source, provenance_hash, classification, entities_extracted, links_created)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (document_id, source, provenance_hash, classification, entities_count, links_count),
            )
            return cursor.lastrowid

    def record_decision(
        self,
        session_id: str,
        scenario: str,
        target_id: str | None,
        agent_role_id: str,
        recommended_procedure_id: str,
        risk_level: str,
        risk_score: float,
        compliance_status: str,
        violations: list[str],
        rationale: str,
    ) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO decision_audit_log 
                (session_id, scenario, target_id, agent_role_id, recommended_procedure_id,
                 risk_level, risk_score, compliance_status, violations, rationale)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    scenario,
                    target_id,
                    agent_role_id,
                    recommended_procedure_id,
                    risk_level,
                    risk_score,
                    compliance_status,
                    json.dumps(violations),
                    rationale,
                ),
            )
            return cursor.lastrowid

    def get_recent_decisions(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM decision_audit_log ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_ingestion_history(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM ingestion_log ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
