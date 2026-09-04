from __future__ import annotations

import json
import sqlite3
from pathlib import Path

META_TRACE_STATE_KEY = "self_learn_meta_trace"
META_TRACE_VERSION = 1


def _repo_root(root: Path) -> Path:
    root = root.resolve()
    if len(root.parents) >= 2:
        return root.parents[1]
    return root


def build_meta_trace(
    root: Path,
    phase_report: list[dict[str, object]],
    modularity_budget: list[dict[str, object]],
    status_snapshot: dict[str, object] | None = None,
) -> dict[str, object]:
    snapshot = status_snapshot or {}
    active_plans = list(snapshot.get("active_plans", []))
    done_plans = list(snapshot.get("done_plans", []))
    missing_phases = [item["phase"] for item in phase_report if item.get("missing")]
    recommendations: list[dict[str, object]] = []
    signals: list[str] = []

    if modularity_budget:
        signals.append("modularity_budget_not_clean")
        recommendations.append(
            {
                "area": "modularity",
                "action": "modularize oversized files before the next checkpoint",
                "count": len(modularity_budget),
            }
        )
    else:
        signals.append("modularity_budget_clean")

    if missing_phases:
        signals.append("phase_definitions_need_review")
        recommendations.append(
            {
                "area": "phase_requirements",
                "action": "tighten the missing phase requirements before treating the phase as stable",
                "phases": missing_phases,
            }
        )
    else:
        signals.append("phase_definitions_clear")

    if not active_plans:
        signals.append("no_active_plan")
        recommendations.append(
            {
                "area": "planning",
                "action": "define or promote an active plan for the next self-learn move",
            }
        )
    else:
        signals.append("active_plan_present")

    if done_plans:
        signals.append("history_available")

    ready = not modularity_budget and not missing_phases and bool(active_plans)
    summary = "Meta optimization is ready." if ready else "Meta optimization needs attention."
    return {
        "version": META_TRACE_VERSION,
        "summary": summary,
        "ready": ready,
        "root": str(root),
        "phase_count": len(phase_report),
        "active_plan_count": len(active_plans),
        "done_plan_count": len(done_plans),
        "modularity_issue_count": len(modularity_budget),
        "phase_gap_count": len(missing_phases),
        "missing_phases": missing_phases,
        "signals": signals,
        "recommendations": recommendations,
    }


def render_meta_optimization_doc(trace: dict[str, object]) -> str:
    lines = [
        "# Meta optimization trace",
        "",
        trace.get("summary", "Meta optimization trace."),
        "",
        f"- ready: {trace.get('ready')}",
        f"- phase count: {trace.get('phase_count')}",
        f"- active plan count: {trace.get('active_plan_count')}",
        f"- done plan count: {trace.get('done_plan_count')}",
        f"- modularity issue count: {trace.get('modularity_issue_count')}",
        f"- phase gap count: {trace.get('phase_gap_count')}",
        "",
        "## signals",
    ]
    lines.extend(f"- {signal}" for signal in trace.get("signals", []))
    lines.extend(["", "## recommendations"])
    recommendations = trace.get("recommendations", [])
    if recommendations:
        for rec in recommendations:
            lines.append(f"- {rec.get('area')}: {rec.get('action')}")
    else:
        lines.append("- none")
    lines.extend(["", "## raw trace", "```json", json.dumps(trace, indent=2, sort_keys=True), "```"])
    return "\n".join(lines) + "\n"


def write_meta_trace_files(root: Path, trace: dict[str, object]) -> dict[str, str]:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    json_path = docs_dir / "meta-trace.json"
    md_path = docs_dir / "meta-optimization.md"
    json_path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_meta_optimization_doc(trace), encoding="utf-8")
    return {"meta_trace": str(json_path), "meta_optimization": str(md_path)}


def update_meta_trace_state(root: Path, trace: dict[str, object]) -> dict[str, object]:
    repo_root = _repo_root(root)
    db_path = repo_root / "continuity.db"
    if not db_path.exists():
        return {"updated": False, "reason": "continuity.db missing"}
    payload = json.dumps(trace, sort_keys=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            create table if not exists metacognitive_state (
                state_key text primary key,
                value text,
                version integer,
                updated_at text default current_timestamp
            )
            """
        )
        columns = {row[1] for row in conn.execute("pragma table_info(metacognitive_state)")}
        insert_columns = ["state_key"]
        values = [META_TRACE_STATE_KEY]
        if "category" in columns:
            insert_columns.append("category")
            values.append("meta_trace")
        if "value" in columns:
            insert_columns.append("value")
            values.append(payload)
        if "confidence" in columns:
            insert_columns.append("confidence")
            values.append(1.0)
        if "provenance" in columns:
            insert_columns.append("provenance")
            values.append("self_learn_meta")
        if "version" in columns:
            insert_columns.append("version")
            values.append(META_TRACE_VERSION)
        placeholders = ", ".join("?" for _ in insert_columns)
        column_sql = ", ".join(insert_columns)
        update_columns = [col for col in insert_columns if col != "state_key"]
        update_sql = ", ".join(f"{col}=excluded.{col}" for col in update_columns)
        sql = f"insert into metacognitive_state({column_sql}) values({placeholders})"
        if "state_key" in columns:
            sql += f" on conflict(state_key) do update set {update_sql}"
            if "updated_at" in columns:
                sql += ", updated_at=CURRENT_TIMESTAMP"
        conn.execute(sql, values)
        conn.commit()
    finally:
        conn.close()
    return {"updated": True, "state_key": META_TRACE_STATE_KEY, "version": META_TRACE_VERSION}
