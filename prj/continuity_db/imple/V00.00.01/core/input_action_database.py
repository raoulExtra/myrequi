"""Database migration helpers for the continuity database router."""

import sqlite3


def migrate_evidence_ledger(cur: sqlite3.Cursor) -> None:
    """Add provenance columns required by the scientific evidence layer."""
    for ddl in (
        "ALTER TABLE evidence_ledger ADD COLUMN source_actor TEXT NOT NULL DEFAULT 'unknown'",
        "ALTER TABLE evidence_ledger ADD COLUMN provenance_json TEXT NOT NULL DEFAULT ''",
    ):
        try:
            cur.execute(ddl)
        except sqlite3.OperationalError:
            # The column already exists when the migration has run previously.
            pass
