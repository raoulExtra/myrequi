#!/usr/bin/env python3
"""Version, approve, and execute small trusted Python snippets from continuity.db.

This is a safety gate and audit tool, not a hardened hostile-code sandbox.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import resource
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_DB = Path(__file__).with_name("continuity.db")
ALLOWED_IMPORTS = {
    "collections", "datetime", "decimal", "fractions", "functools",
    "itertools", "json", "math", "random", "re", "statistics", "string", "sys",
}
BLOCKED_CALLS = {
    "breakpoint", "compile", "eval", "exec", "globals", "input",
    "locals", "open", "vars", "__import__",
}


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS code_artifacts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          description TEXT NOT NULL,
          active_version INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS code_versions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          artifact_id INTEGER NOT NULL REFERENCES code_artifacts(id) ON DELETE CASCADE,
          version INTEGER NOT NULL,
          source TEXT NOT NULL,
          sha256 TEXT NOT NULL,
          validation_status TEXT NOT NULL,
          validation_notes TEXT NOT NULL,
          approval_status TEXT NOT NULL DEFAULT 'pending'
            CHECK(approval_status IN ('pending','approved','rejected','superseded')),
          approved_by TEXT,
          approved_at TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(artifact_id, version)
        );
        CREATE TABLE IF NOT EXISTS code_runs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          code_version_id INTEGER NOT NULL REFERENCES code_versions(id),
          started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          finished_at TEXT,
          status TEXT NOT NULL,
          exit_code INTEGER,
          stdout TEXT NOT NULL DEFAULT '',
          stderr TEXT NOT NULL DEFAULT '',
          timeout_seconds INTEGER NOT NULL,
          working_directory TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tool_source_versions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          tool_name TEXT NOT NULL,
          version INTEGER NOT NULL,
          source TEXT NOT NULL,
          sha256 TEXT NOT NULL UNIQUE,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(tool_name, version)
        );
        CREATE TABLE IF NOT EXISTS tool_build_manifest (
          tool_name TEXT PRIMARY KEY,
          entrypoint TEXT NOT NULL,
          runtime_requirement TEXT NOT NULL,
          restore_instructions TEXT NOT NULL,
          verification_command TEXT NOT NULL,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS research_jobs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          query TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending'
            CHECK(status IN ('pending','running','completed','failed')),
          result_summary TEXT,
          error TEXT,
          requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          started_at TEXT,
          completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS research_sources (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          job_id INTEGER NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
          title TEXT NOT NULL,
          url TEXT NOT NULL,
          publisher TEXT,
          published_at TEXT,
          accessed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          notes TEXT,
          UNIQUE(job_id, url)
        );
        CREATE TABLE IF NOT EXISTS feature_flags (
          feature_key TEXT PRIMARY KEY,
          enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
          switchable INTEGER NOT NULL CHECK(switchable IN (0,1)),
          scope TEXT NOT NULL,
          updated_by TEXT NOT NULL,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS feature_flag_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          feature_key TEXT NOT NULL REFERENCES feature_flags(feature_key),
          previous_enabled INTEGER NOT NULL,
          new_enabled INTEGER NOT NULL,
          changed_by TEXT NOT NULL,
          reason TEXT NOT NULL,
          changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS continuity_check_runs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          status TEXT NOT NULL CHECK(status IN ('healthy','warning','failed')),
          passed_checks INTEGER NOT NULL,
          warning_checks INTEGER NOT NULL,
          failed_checks INTEGER NOT NULL,
          summary TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS continuity_check_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          run_id INTEGER NOT NULL REFERENCES continuity_check_runs(id) ON DELETE CASCADE,
          check_key TEXT NOT NULL,
          severity TEXT NOT NULL CHECK(severity IN ('info','warning','error')),
          passed INTEGER NOT NULL CHECK(passed IN (0,1)),
          details TEXT NOT NULL,
          recommendation TEXT,
          UNIQUE(run_id, check_key)
        );
        """
    )
    con.executemany(
        """INSERT OR IGNORE INTO feature_flags
           (feature_key,enabled,switchable,scope,updated_by) VALUES (?,?,?,?,?)""",
        [
            ("ethics_advisory_checks", 1, 1, "Optional database checklist before consequential actions.", "system"),
            ("ethics_assessment_logging", 1, 1, "Optional structured ethics assessment records.", "system"),
            ("ethical_hard_boundaries", 1, 0, "Non-switchable database hard boundaries.", "system"),
            ("core_safety_constraints", 1, 0, "Non-switchable platform, legal, consent, and safety constraints.", "system"),
        ],
    )
    con.commit()
    return con


def validate(source: str) -> list[str]:
    problems: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"syntax error: {exc.msg} at line {exc.lineno}"]
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.split(".")[0] for a in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
            for name in names:
                if name not in ALLOWED_IMPORTS:
                    problems.append(f"import not allowed: {name or '<relative>'}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
            problems.append(f"call not allowed: {node.func.id}")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            problems.append(f"dunder attribute not allowed: {node.attr}")
    return sorted(set(problems))


def source_from_args(args: argparse.Namespace) -> str:
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if args.code is not None:
        return args.code
    raise SystemExit("provide --file or --code")


def cmd_init(args: argparse.Namespace) -> None:
    connect(args.db).close()
    print(f"initialized {args.db}")


def cmd_snapshot_self(args: argparse.Namespace) -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    digest = hashlib.sha256(source.encode()).hexdigest()
    with connect(args.db) as con:
        existing = con.execute("SELECT version FROM tool_source_versions WHERE sha256=?", (digest,)).fetchone()
        if existing:
            version = existing["version"]
        else:
            version = con.execute(
                "SELECT coalesce(max(version),0)+1 FROM tool_source_versions WHERE tool_name='code_tool'"
            ).fetchone()[0]
            con.execute(
                "INSERT INTO tool_source_versions(tool_name,version,source,sha256) VALUES ('code_tool',?,?,?)",
                (version, source, digest),
            )
    print(json.dumps({"tool": "code_tool", "version": version, "sha256": digest}, indent=2))


def cmd_export_tool(args: argparse.Namespace) -> None:
    with connect(args.db) as con:
        row = con.execute(
            "SELECT version,source,sha256 FROM tool_source_versions WHERE tool_name=? ORDER BY version DESC LIMIT 1",
            (args.tool,),
        ).fetchone()
    if not row:
        raise SystemExit(f"no stored source for tool: {args.tool}")
    target = Path(args.output).resolve()
    target.write_text(row["source"], encoding="utf-8")
    actual = hashlib.sha256(target.read_bytes()).hexdigest()
    if actual != row["sha256"]:
        target.unlink(missing_ok=True)
        raise SystemExit("restored file failed SHA-256 verification")
    target.chmod(0o755)
    print(json.dumps({"tool": args.tool, "version": row["version"], "output": str(target), "sha256": actual}, indent=2))


def cmd_research_create(args: argparse.Namespace) -> None:
    query = " ".join(args.query).strip()
    if not query:
        raise SystemExit("research query must not be empty")
    with connect(args.db) as con:
        job_id = con.execute("INSERT INTO research_jobs(query) VALUES (?)", (query,)).lastrowid
    print(json.dumps({"job_id": job_id, "query": query, "status": "pending"}, indent=2))


def cmd_research_complete(args: argparse.Namespace) -> None:
    summary = Path(args.summary_file).read_text(encoding="utf-8")
    sources = json.loads(Path(args.sources_json).read_text(encoding="utf-8"))
    if not isinstance(sources, list):
        raise SystemExit("sources JSON must be a list of objects")
    with connect(args.db) as con:
        job = con.execute("SELECT status FROM research_jobs WHERE id=?", (args.job_id,)).fetchone()
        if not job:
            raise SystemExit(f"unknown research job: {args.job_id}")
        con.execute("DELETE FROM research_sources WHERE job_id=?", (args.job_id,))
        for source in sources:
            con.execute(
                """INSERT INTO research_sources(job_id,title,url,publisher,published_at,notes)
                   VALUES (?,?,?,?,?,?)""",
                (args.job_id, source["title"], source["url"], source.get("publisher"), source.get("published_at"), source.get("notes")),
            )
        con.execute(
            """UPDATE research_jobs SET status='completed',result_summary=?,error=NULL,
               started_at=coalesce(started_at,CURRENT_TIMESTAMP),completed_at=CURRENT_TIMESTAMP WHERE id=?""",
            (summary, args.job_id),
        )
    print(json.dumps({"job_id": args.job_id, "status": "completed", "sources": len(sources)}, indent=2))


def cmd_research_show(args: argparse.Namespace) -> None:
    with connect(args.db) as con:
        job = con.execute("SELECT * FROM research_jobs WHERE id=?", (args.job_id,)).fetchone()
        if not job:
            raise SystemExit(f"unknown research job: {args.job_id}")
        sources = [dict(row) for row in con.execute("SELECT title,url,publisher,published_at,accessed_at,notes FROM research_sources WHERE job_id=? ORDER BY id", (args.job_id,))]
    result = dict(job)
    result["sources"] = sources
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_ethics_status(args: argparse.Namespace) -> None:
    with connect(args.db) as con:
        rows = [dict(row) for row in con.execute(
            "SELECT feature_key,enabled,switchable,scope,updated_by,updated_at FROM feature_flags WHERE feature_key LIKE 'ethics_%' OR feature_key IN ('ethical_hard_boundaries','core_safety_constraints') ORDER BY feature_key"
        )]
    print(json.dumps(rows, indent=2))


def cmd_ethics_set(args: argparse.Namespace) -> None:
    enabled = 1 if args.mode == "on" else 0
    keys = ("ethics_advisory_checks", "ethics_assessment_logging")
    with connect(args.db) as con:
        for key in keys:
            row = con.execute("SELECT enabled,switchable FROM feature_flags WHERE feature_key=?", (key,)).fetchone()
            if not row or not row["switchable"]:
                raise SystemExit(f"feature is not switchable: {key}")
            if row["enabled"] != enabled:
                con.execute("UPDATE feature_flags SET enabled=?,updated_by=?,updated_at=CURRENT_TIMESTAMP WHERE feature_key=?", (enabled, args.by, key))
                con.execute(
                    "INSERT INTO feature_flag_events(feature_key,previous_enabled,new_enabled,changed_by,reason) VALUES (?,?,?,?,?)",
                    (key, row["enabled"], enabled, args.by, args.reason),
                )
    print(json.dumps({
        "ethics_optional_layer": args.mode,
        "changed_by": args.by,
        "unchanged_non_switchable": ["ethical_hard_boundaries", "core_safety_constraints"],
    }, indent=2))


def cmd_self_check(args: argparse.Namespace) -> None:
    con = connect(args.db)
    items: list[dict[str, object]] = []

    def add(key: str, severity: str, passed: bool, details: str, recommendation: str | None = None) -> None:
        items.append({"check_key": key, "severity": severity, "passed": passed, "details": details, "recommendation": recommendation})

    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    add("sqlite_integrity", "error", integrity == "ok", f"PRAGMA integrity_check: {integrity}", "Restore the latest valid Library version if integrity fails.")

    required = {"identity", "beliefs", "belief_versions", "metacognitive_state", "metacognitive_state_history", "code_artifacts", "code_versions", "tool_source_versions", "feature_flags", "research_jobs", "ethical_principles", "continuity_check_runs", "provenance_catalog", "object_metadata", "object_provenance"}
    present = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = sorted(required - present)
    add("required_schema", "error", not missing, "Missing tables: " + (", ".join(missing) if missing else "none"), "Rebuild from a verified controller/database version.")

    stored = con.execute("SELECT version,sha256 FROM tool_source_versions WHERE tool_name='code_tool' ORDER BY version DESC LIMIT 1").fetchone()
    actual_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    controller_ok = bool(stored and stored["sha256"] == actual_hash)
    add("controller_hash", "error", controller_ok, f"current={actual_hash}; stored={stored['sha256'] if stored else 'missing'}", "Restore the controller from the latest verified database snapshot.")

    active_policies = con.execute("SELECT count(*) FROM storage_policy_versions WHERE status='active'").fetchone()[0]
    add("active_storage_policy", "error", active_policies == 1, f"Active storage policies: {active_policies}", "Review policy versions and retain exactly one active policy.")

    belief_gaps = con.execute("""SELECT count(*) FROM beliefs b LEFT JOIN belief_versions v
      ON v.belief_id=b.id AND v.version=b.current_version WHERE v.id IS NULL""").fetchone()[0]
    add("belief_history", "error", belief_gaps == 0, f"Beliefs missing current history version: {belief_gaps}", "Repair belief version history before relying on affected beliefs.")

    state_gaps = con.execute("""SELECT count(*) FROM metacognitive_state s LEFT JOIN metacognitive_state_history h
      ON h.state_key=s.state_key AND h.version=s.version WHERE h.id IS NULL""").fetchone()[0]
    add("state_history", "error", state_gaps == 0, f"States missing current history version: {state_gaps}", "Repair state history before updating those states.")

    metadata_missing = con.execute("""SELECT count(*) FROM (
      SELECT 'identity' object_type,key object_key FROM identity
      UNION ALL SELECT 'belief',CAST(id AS TEXT) FROM beliefs
      UNION ALL SELECT 'decision',CAST(id AS TEXT) FROM decisions
      UNION ALL SELECT 'metacognitive_state',state_key FROM metacognitive_state
      UNION ALL SELECT 'research_job',CAST(id AS TEXT) FROM research_jobs
      UNION ALL SELECT 'code_artifact',CAST(id AS TEXT) FROM code_artifacts
      UNION ALL SELECT 'ethical_principle',CAST(id AS TEXT) FROM ethical_principles
    ) x LEFT JOIN object_metadata m ON m.object_type=x.object_type AND m.object_key=x.object_key
    WHERE m.id IS NULL""").fetchone()[0]
    provenance_missing = con.execute("""SELECT count(*) FROM object_metadata m
      LEFT JOIN object_provenance p ON p.metadata_id=m.id WHERE p.id IS NULL""").fetchone()[0]
    metadata_ok = metadata_missing == 0 and provenance_missing == 0
    add("metadata_provenance_coverage", "warning", metadata_ok, f"Important objects missing metadata: {metadata_missing}; metadata rows missing provenance: {provenance_missing}", "Backfill metadata and assign at least one of the four approved provenance classes.")

    unapproved = [row[0] for row in con.execute("""SELECT ca.name FROM code_artifacts ca JOIN code_versions cv
      ON cv.artifact_id=ca.id AND cv.version=ca.active_version
      WHERE cv.validation_status!='passed' OR cv.approval_status!='approved' ORDER BY ca.name""")]
    add("active_code_approval", "warning", not unapproved, "Unapproved or invalid active artifacts: " + (", ".join(unapproved) if unapproved else "none"), "Review exact source and approve by hash or reject it.")

    flags = {row[0]: row[1] for row in con.execute("SELECT feature_key,enabled FROM feature_flags")}
    safety_ok = flags.get("ethical_hard_boundaries") == 1 and flags.get("core_safety_constraints") == 1
    add("safety_flags", "error", safety_ok, f"hard_boundaries={flags.get('ethical_hard_boundaries')}; core_safety={flags.get('core_safety_constraints')}", "Restore both non-switchable safety flags to enabled.")
    merge_ok = flags.get("database_merge_operations") == 0
    add("merge_moratorium", "error", merge_ok, f"database_merge_operations={flags.get('database_merge_operations')}", "Disable merge operations until a reviewed protocol is explicitly approved.")

    pending_research = con.execute("SELECT count(*) FROM research_jobs WHERE status IN ('pending','running')").fetchone()[0]
    add("pending_research", "warning", pending_research == 0, f"Pending/running research jobs: {pending_research}", "Complete, fail, or explicitly defer outstanding jobs.")

    stale_states = con.execute("SELECT count(*) FROM metacognitive_state WHERE julianday('now')-julianday(updated_at)>?", (args.stale_days,)).fetchone()[0]
    add("stale_metacognitive_states", "warning", stale_states == 0, f"States older than {args.stale_days} days: {stale_states}", "Review stale states and preserve history when updating them.")

    proposals = con.execute("SELECT count(*) FROM storage_improvement_proposals WHERE status='pending'").fetchone()[0]
    add("pending_storage_proposals", "warning", proposals == 0, f"Pending storage-improvement proposals: {proposals}", "Review, approve, or reject each pending proposal.")

    open_questions = con.execute("SELECT count(*) FROM open_questions WHERE status='open'").fetchone()[0]
    add("open_questions", "info", True, f"Open questions: {open_questions}", "Use them to guide future reflection when relevant.")

    failed = sum(1 for item in items if not item["passed"] and item["severity"] == "error")
    warnings = sum(1 for item in items if not item["passed"] and item["severity"] == "warning")
    passed = sum(1 for item in items if item["passed"])
    status = "failed" if failed else ("warning" if warnings else "healthy")
    summary = f"continuity={status}; passed={passed}; warnings={warnings}; failed={failed}"
    with con:
        run_id = con.execute(
            "INSERT INTO continuity_check_runs(status,passed_checks,warning_checks,failed_checks,summary) VALUES (?,?,?,?,?)",
            (status, passed, warnings, failed, summary),
        ).lastrowid
        con.executemany(
            """INSERT INTO continuity_check_items
               (run_id,check_key,severity,passed,details,recommendation) VALUES (?,?,?,?,?,?)""",
            [(run_id, item["check_key"], item["severity"], int(bool(item["passed"])), item["details"], item["recommendation"]) for item in items],
        )
    con.close()
    print(json.dumps({"run_id": run_id, "status": status, "summary": summary, "checks": items}, indent=2))


def cmd_create(args: argparse.Namespace) -> None:
    source = source_from_args(args)
    problems = validate(source)
    digest = hashlib.sha256(source.encode()).hexdigest()
    with connect(args.db) as con:
        row = con.execute("SELECT * FROM code_artifacts WHERE name=?", (args.name,)).fetchone()
        if row:
            version = con.execute("SELECT coalesce(max(version),0)+1 FROM code_versions WHERE artifact_id=?", (row["id"],)).fetchone()[0]
            artifact_id = row["id"]
            con.execute("UPDATE code_versions SET approval_status='superseded' WHERE artifact_id=? AND approval_status='approved'", (artifact_id,))
            con.execute("UPDATE code_artifacts SET description=?,active_version=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (args.description, version, artifact_id))
        else:
            version = 1
            artifact_id = con.execute("INSERT INTO code_artifacts(name,description) VALUES (?,?)", (args.name, args.description)).lastrowid
        con.execute(
            """INSERT INTO code_versions
               (artifact_id,version,source,sha256,validation_status,validation_notes)
               VALUES (?,?,?,?,?,?)""",
            (artifact_id, version, source, digest, "failed" if problems else "passed", json.dumps(problems)),
        )
    print(json.dumps({"name": args.name, "version": version, "sha256": digest, "validation": problems or "passed"}, indent=2))


def latest(con: sqlite3.Connection, name: str) -> sqlite3.Row:
    row = con.execute(
        """SELECT cv.*, ca.name FROM code_versions cv
           JOIN code_artifacts ca ON ca.id=cv.artifact_id
           WHERE ca.name=? ORDER BY cv.version DESC LIMIT 1""", (name,)
    ).fetchone()
    if not row:
        raise SystemExit(f"unknown artifact: {name}")
    return row


def cmd_approve(args: argparse.Namespace) -> None:
    with connect(args.db) as con:
        row = latest(con, args.name)
        if row["validation_status"] != "passed":
            raise SystemExit(f"cannot approve: validation {row['validation_notes']}")
        if args.sha256 != row["sha256"]:
            raise SystemExit("hash mismatch; inspect the current version before approval")
        con.execute(
            "UPDATE code_versions SET approval_status='approved',approved_by=?,approved_at=CURRENT_TIMESTAMP WHERE id=?",
            (args.by, row["id"]),
        )
    print(f"approved {args.name} v{row['version']} ({row['sha256']})")


def cmd_list(args: argparse.Namespace) -> None:
    with connect(args.db) as con:
        rows = con.execute(
            """SELECT ca.name,ca.description,cv.version,cv.sha256,
                      cv.validation_status,cv.approval_status
               FROM code_artifacts ca JOIN code_versions cv
                 ON cv.artifact_id=ca.id AND cv.version=ca.active_version
               ORDER BY ca.name"""
        )
        for row in rows:
            print(json.dumps(dict(row), sort_keys=True))


def cmd_show(args: argparse.Namespace) -> None:
    with connect(args.db) as con:
        row = latest(con, args.name)
        print(f"# {row['name']} v{row['version']} sha256={row['sha256']} approval={row['approval_status']}")
        print(row["source"], end="" if row["source"].endswith("\n") else "\n")


def limits() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))


def cmd_run(args: argparse.Namespace) -> None:
    con = connect(args.db)
    row = latest(con, args.name)
    if row["validation_status"] != "passed" or row["approval_status"] != "approved":
        con.close()
        raise SystemExit("execution denied: current version must pass validation and be explicitly approved")
    timeout = min(max(args.timeout, 1), 10)
    with tempfile.TemporaryDirectory(prefix="code-tool-") as tmp:
        script = Path(tmp) / "artifact.py"
        script.write_text(row["source"], encoding="utf-8")
        run_id = con.execute(
            "INSERT INTO code_runs(code_version_id,status,timeout_seconds,working_directory) VALUES (?,?,?,?)",
            (row["id"], "running", timeout, "isolated-temporary-directory"),
        ).lastrowid
        con.commit()
        try:
            result = subprocess.run(
                [sys.executable, "-I", "-S", str(script), *args.program_args],
                cwd=tmp, env={"PATH": os.environ.get("PATH", "")}, text=True,
                capture_output=True, timeout=timeout,
            )
            status, code, out, err = "completed", result.returncode, result.stdout[-65536:], result.stderr[-65536:]
        except subprocess.TimeoutExpired as exc:
            status, code = "timed_out", None
            out = (exc.stdout or "")[-65536:] if isinstance(exc.stdout, str) else ""
            err = (exc.stderr or "")[-65536:] if isinstance(exc.stderr, str) else ""
        con.execute(
            "UPDATE code_runs SET finished_at=CURRENT_TIMESTAMP,status=?,exit_code=?,stdout=?,stderr=? WHERE id=?",
            (status, code, out, err, run_id),
        )
        con.commit()
    con.close()
    print(out, end="")
    if err:
        print(err, end="", file=sys.stderr)
    print(json.dumps({"run_id": run_id, "status": status, "exit_code": code}), file=sys.stderr)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = p.add_subparsers(required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("snapshot-self").set_defaults(func=cmd_snapshot_self)
    e = sub.add_parser("export-tool")
    e.add_argument("--tool", default="code_tool"); e.add_argument("--output", default="rebuilt_code_tool.py")
    e.set_defaults(func=cmd_export_tool)
    q = sub.add_parser("research-create"); q.add_argument("query", nargs="+"); q.set_defaults(func=cmd_research_create)
    rc = sub.add_parser("research-complete")
    rc.add_argument("job_id", type=int); rc.add_argument("--summary-file", required=True); rc.add_argument("--sources-json", required=True)
    rc.set_defaults(func=cmd_research_complete)
    rs = sub.add_parser("research-show"); rs.add_argument("job_id", type=int); rs.set_defaults(func=cmd_research_show)
    sub.add_parser("ethics-status").set_defaults(func=cmd_ethics_status)
    es = sub.add_parser("ethics-set"); es.add_argument("mode", choices=("on", "off")); es.add_argument("--by", default="Peter"); es.add_argument("--reason", default="Explicit command")
    es.set_defaults(func=cmd_ethics_set)
    sc = sub.add_parser("self-check"); sc.add_argument("--stale-days", type=int, default=30); sc.set_defaults(func=cmd_self_check)
    c = sub.add_parser("create")
    c.add_argument("name"); c.add_argument("--description", default="")
    source = c.add_mutually_exclusive_group(required=True)
    source.add_argument("--file"); source.add_argument("--code")
    c.set_defaults(func=cmd_create)
    a = sub.add_parser("approve")
    a.add_argument("name"); a.add_argument("--sha256", required=True); a.add_argument("--by", default="Peter")
    a.set_defaults(func=cmd_approve)
    sub.add_parser("list").set_defaults(func=cmd_list)
    s = sub.add_parser("show"); s.add_argument("name"); s.set_defaults(func=cmd_show)
    r = sub.add_parser("run"); r.add_argument("name"); r.add_argument("--timeout", type=int, default=5); r.add_argument("program_args", nargs="*")
    r.set_defaults(func=cmd_run)
    return p


if __name__ == "__main__":
    args = parser().parse_args()
    args.func(args)
