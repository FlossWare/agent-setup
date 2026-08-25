"""Non-interactive agent_setup helper uses package AGENTS."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_agent_setup_module_loads_agents():
    spec = importlib.util.spec_from_file_location(
        "agent_setup_under_test", ROOT / "scripts" / "agent_setup.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "AGENTS")
    assert len(mod.AGENTS) == 13
    assert not hasattr(mod, "AGENT_ADAPTERS")
