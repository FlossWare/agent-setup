"""Smoke tests for entry points and TUI import surface."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_setup_entry_imports_main():
    spec = importlib.util.spec_from_file_location(
        "setup_entry", ROOT / "scripts" / "setup.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert callable(module.main)


def test_flossware_setup_package_exports():
    import flossware_setup

    assert flossware_setup.__version__
    assert callable(flossware_setup.main)


def test_tui_helpers_exist():
    from flossware_setup import tui

    for name in (
        "palette",
        "enable_mouse",
        "mouse_click",
        "menu",
        "review_screen",
        "run",
        "main",
    ):
        assert hasattr(tui, name), name


def test_setup_help_non_tty(monkeypatch, capsys):
    from flossware_setup.tui import main

    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    code = main(["--help"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Usage:" in out
