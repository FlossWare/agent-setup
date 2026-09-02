"""FlossWare AI setup application.

Persistent user state is rooted at ``~/.FlossWare/ai`` by default. Set
``FLOSSWARE_AI_HOME`` to redirect it for tests, CI, containers, or unusual
installations. Credential values remain outside FlossWare state.

Public package layout:

- catalog: domain/catalog data (agents, capabilities, providers, budgets)
- config: configuration model and project persistence (no secrets)
- credentials: presence checks only; never stores secret values
- artifacts: generated project files and pip package refs
- installer: capability package installation
- tui: curses control-center UI (keyboard + mouse)
"""

import os
from pathlib import Path

# Keep older callers that consult FLOSSWARE_AI_ROOT working while establishing
# the new canonical default. Explicit overrides always win.
if not os.environ.get("FLOSSWARE_AI_HOME") and not os.environ.get("FLOSSWARE_AI_ROOT") and not os.environ.get("FLOSSWARE_INSTALL_ROOT"):
    os.environ["FLOSSWARE_AI_ROOT"] = str((Path.home() / ".FlossWare" / "ai").resolve())

from flossware_setup.tui import main

__all__ = ["__version__", "main"]
__version__ = "0.1.0"
