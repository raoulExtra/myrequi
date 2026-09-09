#!/usr/bin/env python3
"""Generate improvement plan markdown files from continuity.db plans or prompts.

Usage examples:
  python gen_improv_plan.py --plan-key self_improve_memory_system
  python gen_improv_plan.py --prompt "Create a memory-assisted self-improvement interface"
"""

import argparse
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[4]  # Go up to project root
DEFAULT_DB = ROOT / "continuity.db"
DEFAULT_OUTPUT_DIR = ROOT / "prj" / "self_learn" / "plans"


@dataclass
class PlanSource:
    kind: str  # 'db' or 'prompt'
    key: str
    title: str
    objective: str
    prompt: str
    steps: list[str]
    linked: list[dict]


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def next_index(output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    max_idx = 0
    for path in output_dir.glob("*-plan.md"):
        m = re.match(r"^(\d+)-plan\.md$", path.name)
        if m:
            max_idx = max(max_idx, int(m.group(1)))
    return max_idx + 1


def slug_title(text: str, fallback: str = "Generated plan") -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return fallback
    words = text.split()
    short = " ".join(words[:10]).strip(" .,:;-")
    if len(short) < len(text) and len(words) > 10:
        short += "…"
    return short[:80]


def fetch_plan(conn: sqlite3.Connection, plan_key: str) -> PlanSource | None:
    plan = conn.execute(
        "select plan_key, title, objective, prompt from work_plans where plan_key=?",
        (plan_key,),
    ).fetchone()
    if plan is None:
        return None

    steps = conn.execute(
        """
        select step_order, step_key, description
        from work_plan_steps
        where plan_id=(select id from work_plans where plan_key=?)
        order by step_order
        """,
        (plan_key,),
    ).fetchall()
    
    linked = conn.execute(
        """
        select l.relation, l.target_plan_key, tp.title as target_title, l.target_step_key, l.note
        from work_plan_links l
        join work_plans sp on sp.id = l.source_plan_id
        join work_plans tp on tp.plan_key = l.target_plan_key
        where sp.plan_key=?
        order by l.created_at, l.id
        """,
        (plan_key,),
    ).fetchall()
    
    return PlanSource(
        kind="db",
        key=plan["plan_key"],
        title=plan["title"] or slug_title(plan_key),
        objective=plan["objective"] or "",
        prompt=plan["prompt"] or "",
        steps=[row["description"] for row in steps],
        linked=[dict(r) for r in linked],
    )


def extract_only_steps(prompt: str) -> list[str] | None:
    """Extract steps from prompt text that contains 'only' guidance."""
    text = prompt or ""
    
    # Look for "only" followed by steps
    markers = list(re.finditer(r"(?im)^\s*only\s*:\s*", text, re.MULTILINE))
    if markers:
        tail = text[markers[0].end():].strip()
    else:
        # Try to find numbered list after prompts
        m = re.search(r"(?is)\bthe only step in this plan\b\s*[:\-]?\s*(.+)$", text)
        if m:
            tail = m.group(1).strip()
        else:
            m = re.search(r"(?is)\bonly step(?:s)?(?: in this plan)?\s*[:\-]?\s*(.+)$", text)
            if m:
                tail = m.group(1).strip()
            else:
                return None
    
    if not tail:
        return None
    
    # Split on numbered lists
    numbered = re.findall(r"(?:^|\s)(\d+)[\)\.\:]\s*([^\d].*?)(?=(?:\s+\d+[\)\.\:])|$)", tail, flags=re.S)
    if numbered:
        steps = [re.sub(r"\s+", " ", item).strip(" .;") for _, item in numbered if item.strip()]
        if steps:
            return steps
    
    return None


def build_prompt_source(prompt: str, name: str | None = None) -> PlanSource:
    title = name or slug_title(prompt, fallback="Prompt-generated plan")
    only_steps = extract_only_steps(prompt)
    steps = only_steps if only_steps else [
        f"Clarify the goal for {title}.",
        "Identify the main inputs, evidence, or dependencies.",
        "Choose the next concrete action.",
        "Validate the result and record what changed.",
    ]
    return PlanSource(
        kind="prompt",
        key="prompt_" + datetime.now().strftime("%Y%m%d%H%M%S"),
        title=title,
        objective=slug_title(prompt, fallback="Prompt-driven planning"),
        prompt=prompt,
        steps=steps,
        linked=[],
    )


def unique_plan_sources(sources: Iterable[PlanSource]) -> list[PlanSource]:
    seen: set[tuple[str, str]] = set()
    result: list[PlanSource] = []
    for src in sources:
        key = (src.kind, src.key)
        if key in seen:
            continue
        seen.add(key)
        result.append(src)
    return result


def expand_linked_plans(conn: sqlite3.Connection, base: list[PlanSource], include_linked: bool) -> list[PlanSource]:
    if not include_linked:
        return base

    expanded = list(base)
    seen = {src.key for src in base if src.kind == "db"}
    queue = [src for src in base if src.kind == "db"]

    while queue:
        src = queue.pop(0)
        linked_keys = conn.execute(
            """
            select distinct l.target_plan_key
            from work_plan_links l
            join work_plans sp on sp.id = l.source_plan_id
            where sp.plan_key=?
            order by l.target_plan_key
            """,
            (src.key,),
        ).fetchall()
        for row in linked_keys:
            target_key = row[0]
            if target_key in seen:
                continue
            target = fetch_plan(conn, target_key)
            if target is None:
                continue
            seen.add(target_key)
            expanded.append(target)
            queue.append(target)
    return expanded


def render_markdown(plan: PlanSource, ordinal: int) -> str:
    only_steps = extract_only_steps(plan.prompt) if plan.kind == "prompt" else None
    
    if only_steps is not None:
        lines = []
        lines.append("## Prompt")
        lines.append(plan.prompt)
        lines.append("")
        lines.append("## Steps")
        for idx, step in enumerate(only_steps, start=1):
            lines.append(f"{idx}. TODO[ ] {step}")
        lines.append("")
        return "\n".join(lines)

    lines = []
    lines.append(f"# {plan.title}")
    lines.append("")
    lines.append(f"- file: {ordinal}-plan.md")
    lines.append(f"- kind: {plan.kind}")
    lines.append("")
    lines.append("## Name")
    lines.append(plan.title)
    lines.append("")
    lines.append(f"## Source")
    if plan.kind == "db":
        lines.append(f"- work_plan: `{plan.key}`")
    else:
        lines.append("- prompt input")
    lines.append("")
    lines.append("## Objective")
    lines.append(plan.objective or "")
    lines.append("")
    if plan.prompt:
        lines.append("## Prompt")
        lines.append(plan.prompt)
        lines.append("")
    if plan.linked:
        lines.append("## Linked plans")
        for link in plan.linked:
            lines.append(
                f"- {link['relation']}: `{link['target_plan_key']}` — {link['target_title']}"
            )
            if link.get("note"):
                lines.append(f"  - note: {link['note']}")
        lines.append("")
    lines.append("## Steps")
    for step in plan.steps:
        lines.append(f"- TODO[ ] {step}")
    lines.append("")
    lines.append("## Notes")
    lines.append("- keep steps small, testable, and auditable")
    lines.append("- revise if the linked-plan structure changes")
    lines.append("")
    
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to continuity.db")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Folder for generated plan markdown files")
    parser.add_argument("--no-linked", action="store_true", help="Do not include linked plans recursively")
    parser.add_argument("--name", help="Optional explicit name for prompt-generated plan")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan-key", action="append", help="Generate from one or more DB plan keys")
    group.add_argument("--prompt", help="Generate a plan from a prompt")
    args = parser.parse_args()

    db_path = Path(args.db)
    out_dir = Path(args.output_dir)
    
    conn = connect(db_path)
    try:
        sources: list[PlanSource] = []
        if args.prompt:
            sources.append(build_prompt_source(args.prompt, name=args.name))
        else:
            for key in args.plan_key or []:
                plan = fetch_plan(conn, key)
                if plan is None:
                    raise SystemExit(f"unknown plan_key: {key}")
                sources.append(plan)
            sources = expand_linked_plans(conn, sources, include_linked=not args.no_linked)

        sources = unique_plan_sources(sources)
        if not sources:
            raise SystemExit("no plan sources to generate")

        idx = next_index(out_dir)
        created = []
        for offset, src in enumerate(sources):
            path = out_dir / f"{idx + offset}-plan.md"
            path.write_text(render_markdown(src, idx + offset))
            created.append(str(path))
        
        print(json.dumps({"created": created, "count": len(created)}))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())