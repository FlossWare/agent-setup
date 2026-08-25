#!/usr/bin/env python3
"""Compatibility entry for the Setup TUI (legacy path).

Implementation lives in the flossware_setup package. Installers and the
flossware-ai launcher still invoke this path; it forwards to the same code as
scripts/setup.py and the flossware-setup console script.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from flossware_setup.tui import main

if __name__ == "__main__":
    raise SystemExit(main())
