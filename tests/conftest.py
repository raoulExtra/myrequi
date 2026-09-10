"""Apply stable phase and component markers from the test directory layout."""

from pathlib import Path
import sys

import pytest


TESTS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_ROOT.parent
IMPLEMENTATION_ROOT = PROJECT_ROOT / "prj/continuity_db/imple/V00.00.01"
for import_path in (IMPLEMENTATION_ROOT / "core", IMPLEMENTATION_ROOT / "mindmap"):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

PHASES = {"unit", "sit", "uat"}


def pytest_collection_modifyitems(items):
    root = Path(__file__).resolve().parent
    for item in items:
        try:
            relative_parts = set(Path(item.fspath).resolve().relative_to(root).parts)
        except ValueError:
            continue
        phase = next((name for name in PHASES if name in relative_parts), None)
        if phase:
            item.add_marker(getattr(pytest.mark, phase))
        if "extensions" in relative_parts:
            item.add_marker(pytest.mark.extension)
        elif "core" in relative_parts:
            item.add_marker(pytest.mark.core)
