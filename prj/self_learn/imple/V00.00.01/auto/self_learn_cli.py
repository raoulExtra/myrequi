from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from . import self_learn_automation_core as core
from . import self_learn_meta as meta
from . import self_learn_prompt as prompt


def _root_path(value: str) -> Path:
    return Path(value)


def _mark_plan_completed(plan: Path) -> None:
    text = plan.read_text(encoding="utf-8")
    lower = text.lower()
    if "status: completed" in lower:
        return
    if "status: active" in lower:
        plan.write_text(text.replace("status: active", "status: completed", 1), encoding="utf-8")
        return
    if "status:" in lower:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if line.strip().startswith("status:"):
                lines[index] = "status: completed"
                plan.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return
    plan.write_text(text.rstrip() + "\n\nstatus: completed\n", encoding="utf-8")


def _promote_prep_plan(root: Path, number: str) -> dict[str, object]:
    prep_plan = root / "plans" / "prep" / f"{number}_plan.md"
    target_plan = root / "plans" / f"{number}_plan.md"
    if not prep_plan.exists():
        raise SystemExit(f"prep plan not found: {prep_plan}")
    target_plan.parent.mkdir(parents=True, exist_ok=True)
    prep_plan.rename(target_plan)
    return {
        "promoted": str(target_plan),
        "active_plan_handoff": str(core.write_active_plan_handoff(root)),
    }


def _check_gloss(root: Path, expand: bool = False) -> dict[str, object]:
    glossary_path = root / "docs" / "glossary.md"
    if not glossary_path.exists():
        raise SystemExit(f"glossary not found: {glossary_path}")
    terms = []
    in_table = False
    for raw_line in glossary_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "## Canonical terms":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) != 3 or parts[0] == "Term" or parts[0] == "---":
            continue
        terms.append({"term": parts[0], "meaning": parts[1], "notes": parts[2]})

    glossary_terms = {item["term"].lower() for item in terms}
    phase_report = core.phase_requirement_report(root)
    active_phases = [item for item in phase_report if item.get("status") == "active"]
    phase_files = [root / item["phase"] for item in active_phases]
    current_phase = active_phases[-1] if active_phases else (phase_report[-1] if phase_report else None)

    token_pattern = re.compile(r"\b[a-z][a-z0-9]+(?: [a-z][a-z0-9]+){1,4}\b", re.IGNORECASE)
    common = {
        "current project",
        "project state",
        "phase state",
        "phase docs",
        "core requirements",
        "phase requirements",
        "phase challenge",
        "next path",
        "meta trace",
        "manual trigger",
        "manual trigger cli",
        "active plan",
        "active plans",
        "phase history",
        "phase 0",
        "phase 1",
        "phase 2",
        "phase 3",
        "phase generation",
    }

    discovered: list[dict[str, object]] = []
    seen: set[str] = set()
    for path in phase_files:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for match in token_pattern.finditer(text):
            phrase = re.sub(r"\s+", " ", match.group(0).strip())
            normalized = phrase.lower()
            if normalized in seen or normalized in glossary_terms or normalized in common:
                continue
            words = normalized.split()
            if len(words) < 2 or len(words) > 5:
                continue
            if not any(keyword in normalized for keyword in ["cli", "plan", "phase", "trace", "prompt", "review", "mission", "handoff", "packaging", "generation", "glossary"]):
                continue
            seen.add(normalized)
            discovered.append({"term": phrase, "source": str(path), "important": True})

    payload = {"glossary": str(glossary_path), "term_count": len(terms), "terms": terms}
    if expand:
        docs_dir = root / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        expanded_path = docs_dir / "glossary-check.md"
        lines = [
            "# Glossary phase check",
            "",
            "This report checks whether the current phase introduced new important terms.",
            "",
            f"- current phase: {current_phase['phase'] if current_phase else 'none'}",
            f"- glossary term count: {len(terms)}",
            f"- new important term count: {len(discovered)}",
            "",
            "## new important terms",
        ]
        if discovered:
            for item in discovered:
                lines.extend([
                    f"- {item['term']}",
                    f"  - source: {item['source']}",
                ])
        else:
            lines.append("- none detected")
        lines.extend([
            "",
            "## glossary source",
            f"- glossary: {glossary_path}",
            "",
            "## canonical terms",
        ])
        for item in terms:
            lines.append(f"- {item['term']}")
        expanded_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        payload["expanded_doc"] = str(expanded_path)
        payload["docs_index"] = str(core.docs_index(root))
        payload["new_important_terms"] = discovered
        payload["current_phase"] = current_phase
    return payload


def _next_phase_ai(root: Path) -> dict[str, object]:
    phase_report = core.phase_requirement_report(root)
    active_plans = []
    for plan in core._active_plan_paths(root):  # noqa: SLF001
        title, objective, when_to_run, steps = core._extract_plan_title_and_objective(plan)  # noqa: SLF001
        active_plans.append(
            {
                "name": plan.name,
                "path": str(plan),
                "phase_related": core._plan_is_phase_related(plan),  # noqa: SLF001
                "title": title,
                "purpose": objective if core._plan_is_phase_related(plan) else "",  # noqa: SLF001
                "objective": "" if core._plan_is_phase_related(plan) else objective,  # noqa: SLF001
                "when_to_run": when_to_run,
                "steps": steps,
            }
        )

    prep_plans = []
    prep_dir = root / "plans" / "prep"
    if prep_dir.exists():
        for plan in sorted(prep_dir.glob("*_plan.md")):
            title, objective, when_to_run, steps = core._extract_plan_title_and_objective(plan)  # noqa: SLF001
            prep_plans.append(
                {
                    "name": plan.name,
                    "path": str(plan),
                    "title": title,
                    "objective": objective,
                    "when_to_run": when_to_run,
                    "steps": steps,
                }
            )

    candidates = [
        {
            "key": "NPG-1",
            "generation": "phase 3 automation packaging and manual trigger CLI",
            "why": "the repo now needs a stable manual trigger surface plus better packaging so the current automation can be driven on demand.",
            "impact": 5,
            "reuse": 5,
            "testability": 5,
            "cost": 2,
            "risk": 1,
        },
        {
            "key": "NPG-2",
            "generation": "phase 3 next-phase generation docs and AI handoff refinement",
            "why": "the project already has phase docs and handoffs; the next phase could specialize in generating the next phase recommendation itself.",
            "impact": 4,
            "reuse": 5,
            "testability": 4,
            "cost": 2,
            "risk": 1,
        },
        {
            "key": "NPG-3",
            "generation": "phase 3 plan lifecycle hardening and execution recording",
            "why": "the plan prep/routing flow exists and can be tightened into a clearer promote-run-record cycle.",
            "impact": 4,
            "reuse": 4,
            "testability": 5,
            "cost": 2,
            "risk": 1,
        },
    ]
    for item in candidates:
        item["score"] = int(item["impact"]) + int(item["reuse"]) + int(item["testability"]) - int(item["cost"]) - int(item["risk"])

    ranked = sorted(candidates, key=lambda item: (-int(item["score"]), -int(item["impact"]), -int(item["reuse"]), item["key"]))
    selected = ranked[0]
    payload = {
        "summary": "suggest the best next phase generation",
        "phase_goal": "improve packaging and add a manual trigger CLI for the automation",
        "phase_0_purpose": next((item["purpose"] for item in phase_report if item["phase"] == "phase_0.md"), ""),
        "active_plans": active_plans,
        "prep_plans": prep_plans,
        "candidates": candidates,
        "ranked_candidates": ranked,
        "selected": selected,
        "recommended_next_phase": {
            "phase": "phase_3.md",
            "title": selected["generation"],
            "purpose": selected["generation"],
            "why": selected["why"],
            "source": "current phase history, active plans, prep plans, and the packaging/CLI request",
        },
    }

    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    doc_path = docs_dir / "next-phase-generation.md"
    lines = [
        "# Next phase generation",
        "",
        payload["summary"],
        "",
        f"- phase 0 purpose: {payload['phase_0_purpose']}",
        f"- recommended phase: {payload['recommended_next_phase']['phase']}",
        f"- recommended title: {payload['recommended_next_phase']['title']}",
        "",
        "## candidates",
    ]
    for candidate in candidates:
        lines.extend([
            f"- {candidate['key']}: {candidate['generation']}",
            f"  - why: {candidate['why']}",
            f"  - score: impact {candidate['impact']} + reuse {candidate['reuse']} + testability {candidate['testability']} - cost {candidate['cost']} - risk {candidate['risk']} = {candidate['score']}",
        ])
    lines.extend([
        "",
        "## ranking",
    ])
    for index, candidate in enumerate(ranked, start=1):
        lines.extend([
            f"{index}. {candidate['key']} ({candidate['score']}) - {candidate['generation']}",
            f"   - why: {candidate['why']}",
        ])
    lines.extend([
        "",
        "## selected",
        f"- {selected['key']}: {selected['generation']}",
        f"- rationale: {selected['why']}",
        "",
        "## active plans",
    ])
    for item in active_plans or [{"name": "none"}]:
        if item.get("name") == "none":
            lines.append("- none")
            break
        lines.append(f"- {item['name']}")
    lines.extend([
        "",
        "## prep plans",
    ])
    for item in prep_plans or [{"name": "none"}]:
        if item.get("name") == "none":
            lines.append("- none")
            break
        lines.append(f"- {item['name']}")
    doc_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "next_phase_generation": payload,
        "doc": str(doc_path),
        "active_plan_handoff": str(core.write_active_plan_handoff(root)),
        "docs_index": str(core.docs_index(root)),
    }


def _trigger(root: Path, args: argparse.Namespace) -> dict[str, object]:
    element = args.element
    if element == "handoff":
        return {"active_plan_handoff": str(core.write_active_plan_handoff(root))}
    if element == "next-phase-ai":
        return _next_phase_ai(root)
    if element == "prep-plan":
        if not args.number:
            raise SystemExit("prep-plan requires a plan number")
        return _promote_prep_plan(root, args.number)
    if element == "check-gloss":
        return _check_gloss(root, expand=bool(args.expand))
    if element == "phase-0":
        return {"phase_0": str(core.write_phase_0(root))}
    if element == "phase-1":
        return {"phase_1": str(core.write_phase_1(root))}
    if element == "phase-2":
        phase_report = core.phase_requirement_report(root)
        packet = core.select_phase_2_mission(phase_report)
        return {
            "phase_2": str(core.write_phase_2(root, phase_report, packet)),
            "phase_2_mission": str(core.write_named_phase_2_doc(root, phase_report)),
            "phase_2_core_requi": str(core.write_phase_2_core_requi_doc(root, phase_report)),
            "phase_2_core_review": str(core.write_phase_2_core_review_doc(root, phase_report)),
        }
    if element == "phase-docs":
        phase_report = core.phase_requirement_report(root)
        return {
            "phase_requirements": str(core.write_phase_requirements_doc(root, phase_report)),
            "phase_challenge": str(core.write_phase_challenge_doc(root, phase_report)),
            "modularity": str(core.write_modularity_doc(root, core.MAX_FILE_LINES)),
            "working_rules": str(core.write_working_rules_doc(root)),
            "active_plan_handoff": str(core.write_active_plan_handoff(root)),
            "docs_index": str(core.docs_index(root)),
        }
    if element == "meta-trace":
        phase_report = core.phase_requirement_report(root)
        modularity = core.modularity_budget(root)
        snapshot = core.status(root)
        trace = meta.build_meta_trace(root, phase_report, modularity, snapshot)
        files = meta.write_meta_trace_files(root, trace)
        state = meta.update_meta_trace_state(root, trace)
        return {"meta_trace": trace, **files, "meta_state": state}
    if element == "promote-prep":
        return core.sync(root).as_dict()
    if element == "record-plan":
        plan_value = getattr(args, "plan", None)
        if not plan_value:
            raise SystemExit("record-plan requires --plan")
        plan = Path(plan_value)
        if not plan.is_absolute():
            plan = (root / plan).resolve()
        if not plan.exists():
            raise SystemExit(f"plan not found: {plan}")
        record = core.write_plan_execution_record(root, plan, args.summary or "manual execution record", list(args.detail or []))
        if args.complete_source:
            _mark_plan_completed(plan)
            sync_report = core.sync(root)
            return {"plan_record": str(record), "sync": sync_report.as_dict()}
        return {"plan_record": str(record)}
    raise SystemExit(f"unknown trigger element: {element}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Self-learn manual trigger CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ["sync", "refresh", "advance", "checkpoint", "status", "budget", "challenge", "review"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--root", default=str(core.PROJECT_ROOT), help="Project root directory")

    ask_parser = sub.add_parser("ask", help="prompt the user with a question")
    ask_parser.add_argument("question", help="The question to ask")
    ask_parser.add_argument("--options", help="Comma-separated list of options")
    ask_parser.add_argument("--note", help="Note to display before the question")
    ask_parser.add_argument("--default", help="Default answer if user enters nothing")
    ask_parser.add_argument("--root", default=str(core.PROJECT_ROOT), help="Project root directory")

    trigger = sub.add_parser("trigger", help="manually trigger one automation element")
    trigger.add_argument("element", choices=["handoff", "next-phase-ai", "prep-plan", "check-gloss", "phase-0", "phase-1", "phase-2", "phase-docs", "meta-trace", "promote-prep", "record-plan"])
    trigger.add_argument("number", nargs="?", help="Plan number for prep-plan")
    trigger.add_argument("--root", default=str(core.PROJECT_ROOT), help="Project root directory")
    trigger.add_argument("--plan", help="Plan file to record")
    trigger.add_argument("--expand", action="store_true", help="Expand glossary output for check-gloss")
    trigger.add_argument("--summary", default="", help="Short summary for record-plan")
    trigger.add_argument("--detail", action="append", default=[], help="Extra detail line for record-plan")
    trigger.add_argument("--complete-source", action="store_true", help="Mark the source plan completed and sync it")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = _root_path(getattr(args, "root", str(core.PROJECT_ROOT)))

    if args.command == "sync":
        print(core.sync(root).as_dict())
        return 0
    if args.command == "refresh":
        print(core.refresh(root))
        return 0
    if args.command == "advance":
        print(core.advance(root))
        return 0
    if args.command == "checkpoint":
        print(core.checkpoint(root))
        return 0
    if args.command == "status":
        print(core.status(root))
        return 0
    if args.command == "budget":
        print({"limit": core.MAX_FILE_LINES, "modularity_budget": core.modularity_budget(root)})
        return 0
    if args.command == "challenge":
        phase_report = core.phase_requirement_report(root)
        print({"phase_manifest": core.phase_manifest(root), "phase_challenge_bundle": core.phase_challenge_bundle(root), "phase_challenge": str(core.write_phase_challenge_doc(root, phase_report))})
        return 0
    if args.command == "review":
        print({"phase_manifest": core.phase_manifest(root), "phase_challenge_bundle": core.phase_challenge_bundle(root), "phase_review": core.phase_challenge_bundle(root)})
        return 0
    if args.command == "ask":
        options_list = [item.strip() for item in args.options.split(",")] if args.options else None
        answer = prompt.ask(
            args.question,
            options=options_list,
            note=args.note or "",
            default=args.default or "",
        )
        print(json.dumps({"answer": answer}, indent=2, sort_keys=True))
        return 0
    if args.command == "trigger":
        print(json.dumps(_trigger(root, args), indent=2, sort_keys=True))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
