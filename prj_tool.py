#!/usr/bin/env python3
"""Project filespace helper.

Use it to inspect a project directory like `prj/demo`.

Examples:
  python3 prj_tool.py init demo
  python3 prj_tool.py list demo
  python3 prj_tool.py phases demo
  python3 prj_tool.py show demo phase_0
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_BASE_DIR = ROOT / "prj"


def project_dir(project: str, base_dir: Path = DEFAULT_BASE_DIR) -> Path:
    return base_dir / project


def tree_lines(path: Path, max_depth: int = 3) -> list[str]:
    lines: list[str] = []
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    def walk(dir_path: Path, prefix: str = "", depth: int = 0) -> None:
        if depth > max_depth:
            return
        entries = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for i, entry in enumerate(entries):
            last = i == len(entries) - 1
            branch = "└── " if last else "├── "
            lines.append(f"{prefix}{branch}{entry.name}{'/' if entry.is_dir() else ''}")
            if entry.is_dir():
                extension = "    " if last else "│   "
                walk(entry, prefix + extension, depth + 1)

    lines.append(f"{path.name}/")
    walk(path)
    return lines


def phase_files(path: Path) -> list[Path]:
    if not path.exists():
        raise FileNotFoundError(path)
    files = [p for p in path.iterdir() if p.is_file() and p.name.startswith("phase_") and p.suffix == ".md"]
    def phase_key(p: Path):
        stem = p.stem.replace("phase_", "")
        try:
            return int(stem)
        except ValueError:
            return stem
    return sorted(files, key=phase_key)


def init_project(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "README.md").touch(exist_ok=True)
    return path


def show_phase(path: Path, phase: str) -> Path:
    candidates = [
        path / f"{phase}.md",
        path / f"{phase}.txt",
        path / f"phase_{phase}.md",
        path / f"phase_{phase}.txt",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    raise FileNotFoundError(f"no phase file for {phase!r} in {path}")


def phase_inherits_from(phase0_path: Path) -> str | None:
    if not phase0_path.exists() or not phase0_path.is_file():
        raise FileNotFoundError(phase0_path)
    for line in phase0_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("inherits_from:"):
            value = stripped.split(":", 1)[1].strip()
            return value or None
    return None


def phase_default_version(phase0_path: Path) -> str | None:
    if not phase0_path.exists() or not phase0_path.is_file():
        raise FileNotFoundError(phase0_path)
    for line in phase0_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("default_version:"):
            value = stripped.split(":", 1)[1].strip()
            return value or None
    return None


def _version_key(version: str) -> tuple[int, ...] | tuple[int, str]:
    text = (version or '').strip()
    if text.startswith(('V', 'v')):
        text = text[1:]
    parts = text.split('.')
    try:
        return tuple(int(part) for part in parts if part != '')
    except ValueError:
        return (0, version)


def highest_default_version(project: str, base_dir: Path = DEFAULT_BASE_DIR) -> str | None:
    best: str | None = None
    best_key: tuple[int, ...] | tuple[int, str] | None = None
    for ancestor in parent_chain(project, base_dir=base_dir):
        phase0 = project_dir(ancestor, base_dir=base_dir) / "phase_0.md"
        version = phase_default_version(phase0)
        if not version:
            continue
        key = _version_key(version)
        if best is None or key > best_key:
            best = version
            best_key = key
    return best


def parent_chain(project: str, base_dir: Path = DEFAULT_BASE_DIR) -> list[str]:
    chain: list[str] = []
    seen: set[str] = set()
    current = project
    while True:
        if current in seen:
            raise ValueError(f"cyclic inheritance detected at {current!r}")
        seen.add(current)
        chain.append(current)
        phase0 = project_dir(current, base_dir=base_dir) / "phase_0.md"
        parent = phase_inherits_from(phase0)
        if not parent or parent == "-":
            return chain
        current = parent


def _section_items(phase0_path: Path, section_name: str) -> list[str]:
    if not phase0_path.exists() or not phase0_path.is_file():
        raise FileNotFoundError(phase0_path)
    in_section = False
    items: list[str] = []
    for line in phase0_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{section_name}:"):
            in_section = True
            continue
        if not in_section:
            continue
        if not stripped:
            continue
        if not stripped.startswith("-"):
            break
        item = stripped[1:].strip()
        if not item:
            continue
        name = item.split(" — ", 1)[0].split(" - ", 1)[0].strip()
        if name:
            items.append(name)
    return items


def recommended_subdir_rules(phase0_path: Path) -> list[dict[str, str | None]]:
    if not phase0_path.exists() or not phase0_path.is_file():
        raise FileNotFoundError(phase0_path)
    in_section = False
    pending_tag: str | None = None
    rules: list[dict[str, str | None]] = []
    for line in phase0_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("recommended_subdirs:"):
            in_section = True
            pending_tag = None
            continue
        if not in_section:
            continue
        if not stripped:
            continue
        if lower.startswith("on tag:"):
            pending_tag = stripped.split(":", 1)[1].strip() or None
            continue
        if not stripped.startswith("-"):
            continue
        item = stripped[1:].strip()
        if not item:
            continue
        if item.lower().startswith("on tag:"):
            pending_tag = item.split(":", 1)[1].strip() or None
            continue
        name = item.split(" — ", 1)[0].split(" - ", 1)[0].strip()
        if name:
            rules.append({"path": name, "tag": pending_tag})
            pending_tag = None
    return rules


def recommended_subdirs(phase0_path: Path) -> list[str]:
    return [rule["path"] for rule in recommended_subdir_rules(phase0_path)]


def project_tags(phase0_path: Path) -> list[str]:
    return _section_items(phase0_path, "tags") or _section_items(phase0_path, "project_tags")


def current_project_tags(project: str, base_dir: Path = DEFAULT_BASE_DIR) -> list[str]:
    phase0 = project_dir(project, base_dir=base_dir) / "phase_0.md"
    return project_tags(phase0)


def create_recommended_subdirs(project: str, base_dir: Path = DEFAULT_BASE_DIR) -> list[str]:
    created: list[str] = []
    root = project_dir(project, base_dir=base_dir)
    root.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    version = highest_default_version(project, base_dir=base_dir)
    active_tags = set(current_project_tags(project, base_dir=base_dir))
    for ancestor in reversed(parent_chain(project, base_dir=base_dir)):
        phase0 = project_dir(ancestor, base_dir=base_dir) / "phase_0.md"
        for rule in recommended_subdir_rules(phase0):
            required_tag = rule.get("tag")
            if required_tag and required_tag not in active_tags:
                continue
            rel = str(rule["path"]).replace("<version>", version or "<version>")
            if rel in seen:
                continue
            seen.add(rel)
            cursor = root
            created_parts: list[str] = []
            for part in Path(rel).parts:
                cursor = cursor / part
                if not cursor.exists():
                    cursor.mkdir()
                    created_parts.append(str(Path(*cursor.relative_to(root).parts)) + "/")
            created.extend(created_parts)
    return sorted(dict.fromkeys(created))


def project_tags_for(project: str, base_dir: Path = DEFAULT_BASE_DIR) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for ancestor in parent_chain(project, base_dir=base_dir):
        phase0 = project_dir(ancestor, base_dir=base_dir) / "phase_0.md"
        for tag in project_tags(phase0):
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return tags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["init", "list", "phases", "show", "parents", "subdirs", "tags"])
    parser.add_argument("project", help="Project directory name, e.g. demo")
    parser.add_argument("phase", nargs="?", help="Phase name for show")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Project filespace root")
    parser.add_argument("--max-depth", type=int, default=3, help="Max depth for tree listing")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    pdir = project_dir(args.project, base_dir=base_dir)

    if args.action == "init":
        p = init_project(pdir)
        print(p)
        return 0

    if args.action == "list":
        for line in tree_lines(pdir, max_depth=args.max_depth):
            print(line)
        return 0

    if args.action == "phases":
        for path in phase_files(pdir):
            print(path.name)
        return 0

    if args.action == "show":
        if not args.phase:
            raise SystemExit("show requires a phase name")
        path = show_phase(pdir, args.phase)
        print(path.read_text())
        return 0

    if args.action == "parents":
        for item in parent_chain(args.project, base_dir=base_dir):
            print(item)
        return 0

    if args.action == "subdirs":
        for item in create_recommended_subdirs(args.project, base_dir=base_dir):
            print(item)
        return 0

    if args.action == "tags":
        for item in project_tags_for(args.project, base_dir=base_dir):
            print(item)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
