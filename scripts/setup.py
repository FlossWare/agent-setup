"""Compatibility entry point for the FlossWare coding-agent setup TUI.

Implementation lives in the flossware_setup package. This script remains the
stable path used by installers, documentation, and dogfood checks.

Package console script: flossware-setup
Managed install launcher: flossware-ai setup
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
