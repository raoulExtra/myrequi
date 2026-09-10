"""Apply stable phase and component markers from the local test layout."""

from pathlib import Path
import sys

import pytest


TEST_ROOT = Path(__file__).resolve().parent
IMPLEMENTATION_ROOT = TEST_ROOT.parent
REPOSITORY_ROOT = TEST_ROOT.parents[4]
for import_path in (IMPLEMENTATION_ROOT / "core", IMPLEMENTATION_ROOT / "mindmap"):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

PHASES = {"unit", "sit", "uat"}


def pytest_collection_modifyitems(items):
    for item in items:
        try:
            relative_parts = set(Path(item.fspath).resolve().relative_to(TEST_ROOT).parts)
        except ValueError:
            continue
        phase = next((name for name in PHASES if name in relative_parts), None)
        if phase:
            item.add_marker(getattr(pytest.mark, phase))
        if "extension" in relative_parts:
            item.add_marker(pytest.mark.extension)
        elif "core" in relative_parts:
            item.add_marker(pytest.mark.core)
