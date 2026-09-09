#!/usr/bin/env python3
"""Compatibility wrapper for prj/continuity_db/imple/V00.00.01/core/helper_for_db.py."""

import importlib.util
import sys
from pathlib import Path

_CORE_DIR = Path(__file__).resolve().parent / "prj" / "continuity_db" / "imple" / "V00.00.01" / "core"
_CORE_FILE = _CORE_DIR / "helper_for_db.py"
if str(_CORE_DIR) not in sys.path:
    sys.path.insert(0, str(_CORE_DIR))
_spec = importlib.util.spec_from_file_location("_continuity_core_helper_for_db", _CORE_FILE)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load {_CORE_FILE}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

for _key, _value in vars(_module).items():
    if not (_key.startswith("__") and _key not in {"__version__"}):
        globals()[_key] = _value

if __name__ == "__main__":
    _module.main()
