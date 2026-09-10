#!/usr/bin/env python3
from pathlib import Path
import sys

CORE_DIR = Path(__file__).resolve().parent / "prj" / "continuity_db" / "imple" / "V00.00.01" / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from continuity_db.migrations import *

if __name__ == "__main__":
    main()
