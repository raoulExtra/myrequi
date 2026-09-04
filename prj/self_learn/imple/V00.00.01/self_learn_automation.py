from __future__ import annotations

import argparse
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CANONICAL_DIRS = [
    "archive",
    "assets",
    "decisions",
    "docs",
    "examples",
    "imple/V00.00.01",
    "imple/V00.00.01/test",
    "plans",
    "plans/done",
    "references",
]


@dataclass
class SyncReport:
    created_dirs: list[str]
    moved_plans: list[str]

    def as_dict(self) -> dict[str, list[str]]:
        return {"created_dirs": self.created_dirs, "moved_plans": self.moved_plans}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def ensure_canonical_dirs(root: Path = PROJECT_ROOT) -> list[str]:
    created: list[str] = []
    root.mkdir(parents=True, exist_ok=True)
    for rel in CANONICAL_DIRS:
        path = root / rel
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path.relative_to(root)) + "/")
    return created


def move_completed_plans(root: Path = PROJECT_ROOT) -> list[str]:
    plans_dir = root / "plans"
    done_dir = plans_dir / "done"
    done_dir.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for plan in sorted(plans_dir.glob("*_plan.md")):
        if plan.parent == done_dir:
            continue
        text = _read_text(plan).lower()
        if "status: completed" not in text and "status: done" not in text:
            continue
        target = done_dir / plan.name
        shutil.move(str(plan), str(target))
        moved.append(f"plans/done/{plan.name}")
    return moved


def sync(root: Path = PROJECT_ROOT) -> SyncReport:
    created_dirs = ensure_canonical_dirs(root)
    moved_plans = move_completed_plans(root)
    return SyncReport(created_dirs=created_dirs, moved_plans=moved_plans)


def docs_index(root: Path = PROJECT_ROOT) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    plans_dir = root / "plans"
    done_dir = plans_dir / "done"
    active_plans = sorted(p.name for p in plans_dir.glob("*_plan.md") if p.parent != done_dir)
    done_plans = sorted(p.name for p in done_dir.glob("*_plan.md")) if done_dir.exists() else []
    docs = sorted(p.name for p in docs_dir.glob("*.md") if p.name != "index.md")
    content = [
        "# self_learn index",
        "",
        "## docs",
    ]
    content.extend(f"- [{name}](./{name})" for name in docs)
    content.extend(["", "## active plans"])
    content.extend(f"- [{name}](../plans/{name})" for name in active_plans)
    content.extend(["", "## done plans"])
    content.extend(f"- [{name}](../plans/done/{name})" for name in done_plans)
    content.extend(["", "## canonical dirs"])
    content.extend(f"- {rel}/" for rel in CANONICAL_DIRS)
    content.extend(["", "## refresh", "Run `python3 imple/V00.00.01/self_learn_automation.py refresh --root .` to resync the tree."])
    path = docs_dir / "index.md"
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def status(root: Path = PROJECT_ROOT) -> dict[str, object]:
    plans_dir = root / "plans"
    done_dir = plans_dir / "done"
    active_plans = sorted(p.name for p in plans_dir.glob("*_plan.md") if p.parent != done_dir)
    done_plans = sorted(p.name for p in done_dir.glob("*_plan.md")) if done_dir.exists() else []
    return {
        "root": str(root),
        "dirs": [str((root / rel).relative_to(root)) + "/" for rel in CANONICAL_DIRS if (root / rel).exists()],
        "active_plans": active_plans,
        "done_plans": done_plans,
        "docs": sorted(p.name for p in (root / "docs").glob("*.md")) if (root / "docs").exists() else [],
        "docs_index": str(root / "docs" / "index.md") if (root / "docs" / "index.md").exists() else None,
    }


def _repo_root(root: Path) -> Path:
    root = root.resolve()
    if (root / ".git").exists():
        return root
    if len(root.parents) >= 2:
        return root.parents[1]
    return root


def git_checkpoint(root: Path = PROJECT_ROOT, message: str = "self_learn: filesystem checkpoint") -> dict[str, object]:
    repo_root = _repo_root(root)
    rel_root = str(root.resolve().relative_to(repo_root))
    subprocess.run(["git", "-C", str(repo_root), "add", rel_root, "continuity.db"], check=True)
    diff = subprocess.run(["git", "-C", str(repo_root), "diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        return {"repo_root": str(repo_root), "staged": [], "committed": False, "message": message}
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", message], check=True)
    rev = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"], check=True, capture_output=True, text=True)
    return {"repo_root": str(repo_root), "staged": [rel_root, "continuity.db"], "committed": True, "message": message, "commit": rev.stdout.strip()}


def refresh(root: Path = PROJECT_ROOT) -> dict[str, object]:
    report = sync(root)
    index_path = docs_index(root)
    return {**report.as_dict(), "docs_index": str(index_path)}


def checkpoint(root: Path = PROJECT_ROOT, message: str = "self_learn: filesystem checkpoint") -> dict[str, object]:
    report = refresh(root)
    git_report = git_checkpoint(root, message=message)
    return {**report, "git": git_report}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Self-learn filesystem automation helper")
    parser.add_argument("action", choices=["sync", "refresh", "checkpoint", "status"])
    parser.add_argument("--root", default=str(PROJECT_ROOT), help="Project root directory")
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = Path(args.root)

    if args.action == "sync":
        report = sync(root)
        print(report.as_dict())
        return 0
    if args.action == "refresh":
        report = refresh(root)
        print(report)
        return 0
    if args.action == "checkpoint":
        report = checkpoint(root)
        print(report)
        return 0
    if args.action == "status":
        print(status(root))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
