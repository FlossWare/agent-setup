"""FlossWare coding-agent setup application.

Public package layout:

- catalog: domain/catalog data (agents, capabilities, providers, budgets)
- config: configuration model and project persistence (no secrets)
- credentials: presence checks only; never stores secret values
- artifacts: generated project files and pip package refs
- installer: capability package installation
- tui: curses control-center UI (keyboard + mouse)
"""

from flossware_setup.tui import main

__all__ = ["__version__", "main"]
__version__ = "0.1.0"
