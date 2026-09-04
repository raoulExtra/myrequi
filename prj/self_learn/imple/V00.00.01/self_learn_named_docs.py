from __future__ import annotations

from pathlib import Path


def write_named_phase_1_doc(root: Path) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-1-next-path.md"
    content = """# Phase 1: next path

This is the named, human-friendly companion to `phase_1.md`.
It keeps the phase easy to browse like the named files in `prj/demo`.

## core requirements
- define the first usable path candidates.
- challenge each candidate with explicit criteria.
- keep a review loop and feedback path.
- preserve the modularity budget.

## navigation
- [Phase 1](../phase_1.md)
- [Project index](./index.md)
- [Phase requirements](./phase-requirements.md)
- [Phase challenge](./phase-challenge.md)
"""
    path.write_text(content, encoding="utf-8")
    return path
