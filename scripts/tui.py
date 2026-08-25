"""Compatibility entry for the FlossWare Setup TUI.

All TUI entry points use flossware_setup.tui. Legacy operator menus lived here
historically; the authoritative implementation is the package TUI.
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
