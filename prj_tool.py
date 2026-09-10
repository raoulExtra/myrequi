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
    parser.add_argument("action", choices=["init", "list", "phases", "show", "parents", "subdirs", "tags", "context", "model"])
    parser.add_argument("project", help="Project directory name, e.g. demo")
    parser.add_argument("phase", nargs="?", help="Phase name for show")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Project filespace root")
    parser.add_argument("--max-depth", type=int, default=3, help="Max depth for tree listing")
    parser.add_argument("--auto-add", action="store_true", help="Auto-add model to DB if missing")
    parser.add_argument("--session-id", default=None, help="Override session id (from JSONL context)")
    parser.add_argument("--end-session", action="store_true", help="Close session's active model link")
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

    if args.action == "context":
        for line in session_context_lines():
            print(line)
        return 0

    if args.action == "model":
        if args.end_session:
            sid = args.session_id or detect_session_id()
            end_session(sid)
            return 0
        model, sid, status = sync_active_model(args.auto_add, args.session_id)
        print(f"  session_id: {sid}")
        print(f"  model: {model}")
        print(f"  status: {status}")
        return 0

    return 1



def detect_session_id() -> str:
    """Extract the active session ID from JSONL context info."""
    import pathlib, json
    session_dir = pathlib.Path("/home/peter/.pi/agent/sessions/--home-peter-xmyrequi-myrequi--")
    if not session_dir.exists():
        return "unknown"
    files = sorted(session_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return "unknown"
    with open(files[0], "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("type") == "session":
                    sid = entry.get("id")
                    if sid:
                        return sid
            except (json.JSONDecodeError, KeyError):
                continue
    return "unknown"


def sync_active_model(auto_add: bool = False, session_id: str | None = None) -> tuple[str, str, str]:
    """Sync active model to DB, using session ID from JSONL context."""
    import sqlite3, json, pathlib
    settings_path = pathlib.Path("/home/peter/.pi/agent/settings.json")
    models_store_path = pathlib.Path("/home/peter/.pi/agent/models-store.json")
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    model = settings.get("defaultModel", "unknown")
    model_info = None
    if models_store_path.exists():
        store = json.loads(models_store_path.read_text())
        for _provider, block in store.items():
            if isinstance(block, dict):
                for entry in block.get("models", []):
                    if entry.get("id") == model:
                        model_info = entry
                        break
            if model_info:
                break
    sid = session_id or detect_session_id()
    db_path = Path(__file__).resolve().parent / "continuity.db"
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.execute("SELECT object_key FROM object_metadata WHERE object_type='ai_model' AND object_key=?", (model,))
    exists = cur.fetchone()
    if exists:
        cur.execute("UPDATE ai_model_details SET is_active = 1 WHERE model_key = ?", (model,))
        cur.execute("UPDATE ai_model_details SET is_active = 0 WHERE model_key != ?", (model,))
        cur.execute("INSERT INTO model_session_link (model_key, session_id, is_active, context_window_tokens, provider, source_json) VALUES (?, ?, 1, ?, ?, ?)",
                    (model, sid, model_info.get("contextWindow") if model_info else None,
                     model_info.get("provider") if model_info else "unknown",
                     json.dumps({"settings": str(settings_path), "store": str(models_store_path)})))
        con.commit()
        con.close()
        return model, sid, "synced"
    if not auto_add:
        con.close()
        return model, sid, "missing"
    # auto-add
    tags = json.dumps([("provider:" + model_info.get("provider", "unknown")) if model_info else "provider:unknown",
                       ("context:" + str(model_info.get("contextWindow", 0))) if model_info else "context:0", "tier:active"]) if model_info else "[]"
    cur.execute("INSERT INTO object_metadata (object_type, object_key, sensitivity, review_status, tags_json) VALUES (?, ?, ?, ?, ?)",
                ("ai_model", model, "internal", "unreviewed", tags))
    cur.execute("INSERT INTO ai_model_details (model_key, version, architecture, context_window_tokens, training_cutoff, performance_json, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)",
                (model, model_info.get("version") if model_info else "latest",
                 model_info.get("name") if model_info else "unknown",
                 model_info.get("contextWindow") if model_info else None, None,
                 json.dumps({"cost": model_info.get("cost") if model_info else {}, "notes": "Auto-added from settings.json"})))
    cur.execute("INSERT INTO model_session_link (model_key, session_id, is_active, context_window_tokens, provider, source_json) VALUES (?, ?, 1, ?, ?, ?)",
                (model, sid, model_info.get("contextWindow") if model_info else None,
                 model_info.get("provider") if model_info else "unknown",
                 json.dumps({"settings": str(settings_path), "store": str(models_store_path)})))
    con.commit()
    con.close()
    return model, sid, "auto_added"


def end_session(session_id: str | None = None) -> None:
    """Close the active model link for a session."""
    import sqlite3
    sid = session_id or detect_session_id()
    db_path = Path(__file__).resolve().parent / "continuity.db"
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.execute("UPDATE model_session_link SET is_active = 0, ended_at = CURRENT_TIMESTAMP WHERE session_id = ? AND is_active = 1", (sid,))
    con.commit()
    con.close()
    print(f"Closed active model link for session {sid}")


if __name__ == "__main__":
    raise SystemExit(main())
