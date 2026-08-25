"""Entry-point unification: setup and tui share flossware_setup.tui."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_setup_and_tui_scripts_share_package_main():
    setup = _load("setup_script", ROOT / "scripts" / "setup.py")
    tui = _load("tui_script", ROOT / "scripts" / "tui.py")
    assert setup.main is tui.main


def test_setup_tui_legacy_removed():
    assert not (ROOT / "scripts" / "setup_tui.py").exists()
