import json
import sqlite3

import pytest

import scientist_command
from prj.continuity_db.plans.research_audit import (
    ensure_research_audit_schema,
    query_research_audit,
    record_research_audit,
)


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "create table research_jobs (id integer primary key, query text not null)"
    )
    conn.executemany(
        "insert into research_jobs(query) values (?)", [("first",), ("second",)]
    )
    ensure_research_audit_schema(conn)
    return conn


def test_audit_schema_has_required_fields_and_indexes_without_raw_content_column():
    conn = make_db()

    columns = {row[1] for row in conn.execute("pragma table_info(research_audit_receipts)")}
    indexes = {
        row[1]
        for row in conn.execute("pragma index_list(research_audit_receipts)")
    }

    assert {
        "research_job_id",
        "audit_type",
        "source_url",
        "content_hash",
        "policy_version",
        "scanner_provider",
        "decision",
        "denial_reason",
        "recorded_at",
        "provenance_metadata",
    } <= columns
    assert "raw_content" not in columns
    assert "idx_research_audit_job" in indexes
    assert "idx_research_audit_decision" in indexes
    assert "idx_research_audit_type_job" in indexes


def test_record_hashes_content_and_never_stores_raw_content():
    conn = make_db()
    raw_content = "secret retrieved source content"

    receipt_id = record_research_audit(
        conn,
        research_job_id=1,
        source_url="https://www.nist.gov/research",
        content=raw_content,
        policy_version="policy-v1",
        scanner_provider="policy",
        allowed=True,
        provenance_metadata={"source_class": "trusted"},
    )

    row = conn.execute(
        "select * from research_audit_receipts where id=?", (receipt_id,)
    ).fetchone()
    assert raw_content not in repr(row)
    assert row[7] == "allow"
    assert json.loads(row[10])["source_class"] == "trusted"
    assert row[1] == "research_source_scan"


def test_explicit_audit_type_is_preserved():
    conn = make_db()

    receipt_id = record_research_audit(
        conn,
        research_job_id=1,
        audit_type="research_source_scan",
        source_url="https://www.nist.gov/research",
        content="safe",
        policy_version="policy-v1",
        scanner_provider="policy",
        allowed=True,
    )

    row = conn.execute(
        "select audit_type from research_audit_receipts where id=?", (receipt_id,)
    ).fetchone()
    assert row[0] == "research_source_scan"


def test_trusted_source_can_still_be_denied_and_rejected_content_is_not_accepted():
    decision = scientist_command.classify_source(
        "https://www.nist.gov/research",
        "Research",
        "sexually explicit erotic content",
    )

    assert decision["allowed"] is False
    assert decision["class"] == "blocked_unwanted_content"
    assert scientist_command.filter_research_results(
        [{
            "title": "Research",
            "url": "https://www.nist.gov/research",
            "text": "sexually explicit erotic content",
        }]
    ) == []


def test_denial_receipt_and_query_by_research_job():
    conn = make_db()
    record_research_audit(
        conn,
        research_job_id=1,
        source_url="https://www.nist.gov/unsafe",
        content="unsafe page",
        policy_version="policy-v1",
        scanner_provider="content-guard",
        allowed=False,
        denial_reason="unwanted content: erotic",
        provenance_metadata={"source_class": "blocked_unwanted_content"},
    )

    rows = query_research_audit(conn, research_job_id=1)

    assert len(rows) == 1
    assert rows[0]["decision"] == "deny"
    assert rows[0]["denial_reason"] == "unwanted content: erotic"
    assert query_research_audit(conn, research_job_id=2) == []


def test_accepted_research_source_gets_audit_receipt(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        create table research_jobs (
            id integer primary key,
            query text not null,
            status text not null default 'pending',
            result_summary text,
            error text,
            completed_at text
        );
        create table research_sources (
            id integer primary key,
            job_id integer not null,
            title text not null,
            url text not null,
            publisher text,
            notes text
        );
        """
    )
    raw_content = "safe source body that must only be hashed"
    result = {
        "title": "Research",
        "url": "https://www.nist.gov/research",
        "source_class": "trusted",
    }
    target = getattr(scientist_command, "_module", scientist_command)
    monkeypatch.setattr(target, "duckduckgo_search", lambda *args, **kwargs: [result])
    monkeypatch.setattr(target, "filter_research_results", lambda rows: rows)
    monkeypatch.setattr(target, "fetch_url_text", lambda url: raw_content)
    monkeypatch.setattr(target, "summarize_text_for_query", lambda text, topic: "summary")

    research = target.perform_web_research(conn, "topic")

    assert len(research["sources"]) == 1
    receipts = query_research_audit(conn, research_job_id=research["job_id"])
    assert len(receipts) == 1
    assert receipts[0]["decision"] == "allow"
    assert raw_content not in repr(receipts[0])


def test_audit_receipts_are_immutable():
    conn = make_db()
    receipt_id = record_research_audit(
        conn,
        research_job_id=1,
        source_url="https://www.nist.gov/research",
        content="safe",
        policy_version="policy-v1",
        scanner_provider="policy",
        allowed=True,
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "update research_audit_receipts set decision='deny' where id=?",
            (receipt_id,),
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("delete from research_audit_receipts where id=?", (receipt_id,))
