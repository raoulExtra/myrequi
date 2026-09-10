"""Immutable audit receipts for guarded research-source decisions."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any


TABLE = "research_audit_receipts"
_FORBIDDEN_METADATA_KEYS = {"raw_content", "content", "text", "body", "page_text"}


def ensure_research_audit_schema(conn: sqlite3.Connection) -> None:
    """Create the audit table, indexes, and immutability triggers."""
    conn.execute(
        f"""
        create table if not exists {TABLE} (
            id integer primary key,
            research_job_id integer not null,
            source_url text not null,
            content_hash text not null,
            policy_version text not null,
            scanner_provider text not null,
            decision text not null check (decision in ('allow', 'deny')),
            denial_reason text,
            recorded_at text not null default current_timestamp,
            provenance_metadata text not null default '{{}}',
            foreign key (research_job_id) references research_jobs(id)
        )
        """
    )
    conn.execute(
        f"create index if not exists idx_research_audit_job on {TABLE}(research_job_id)"
    )
    conn.execute(
        f"create index if not exists idx_research_audit_decision on {TABLE}(decision)"
    )
    conn.execute(
        f"""
        create trigger if not exists research_audit_receipts_no_update
        before update on {TABLE}
        begin
            select raise(abort, 'research audit receipts are immutable');
        end
        """
    )
    conn.execute(
        f"""
        create trigger if not exists research_audit_receipts_no_delete
        before delete on {TABLE}
        begin
            select raise(abort, 'research audit receipts are immutable');
        end
        """
    )
    conn.commit()


def content_hash(content: str | bytes) -> str:
    """Return a stable SHA-256 without retaining the content in the receipt."""
    payload = content if isinstance(content, bytes) else str(content).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _metadata_json(provenance_metadata: Mapping[str, Any] | None) -> str:
    metadata = dict(provenance_metadata or {})
    forbidden = _FORBIDDEN_METADATA_KEYS.intersection(metadata)
    if forbidden:
        raise ValueError(f"raw content fields are not allowed: {sorted(forbidden)}")
    return json.dumps(metadata, sort_keys=True, separators=(",", ":"))


def record_research_audit(
    conn: sqlite3.Connection,
    *,
    research_job_id: int,
    source_url: str,
    content: str | bytes,
    policy_version: str,
    scanner_provider: str,
    allowed: bool,
    denial_reason: str | None = None,
    provenance_metadata: Mapping[str, Any] | None = None,
) -> int:
    """Store one decision receipt; raw content is used only to calculate a hash."""
    ensure_research_audit_schema(conn)
    decision = "allow" if allowed else "deny"
    if allowed:
        denial_reason = None
    metadata = _metadata_json(provenance_metadata)
    cursor = conn.execute(
        f"""
        insert into {TABLE} (
            research_job_id, source_url, content_hash, policy_version,
            scanner_provider, decision, denial_reason, provenance_metadata
        ) values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            research_job_id,
            source_url,
            content_hash(content),
            policy_version,
            scanner_provider,
            decision,
            denial_reason,
            metadata,
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def query_research_audit(conn: sqlite3.Connection, *, research_job_id: int, limit: int = 10) -> list[dict[str, Any]]:
    """Return bounded audit receipts for one research job."""
    if limit < 1:
        raise ValueError("limit must be positive")
    cursor = conn.execute(
        f"select * from {TABLE} where research_job_id=? order by id limit ?",
        (research_job_id, limit),
    )
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
