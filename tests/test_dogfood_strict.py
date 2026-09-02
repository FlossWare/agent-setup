"""Regression tests for strict dogfood behavioral checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dogfood  # noqa: E402


def _make_invokable_cli(directory: Path, name: str) -> Path:
    """Create a minimal CLI stub that works on POSIX and Windows.

    Windows resolves commands via PATHEXT (.cmd/.bat/.exe). A shebang-only
    script without an extension is not a valid invokable agent CLI there.
    """
    if os.name == "nt":
        path = directory / f"{name}.cmd"
        path.write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
    else:
        path = directory / name
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)
    return path


def test_agent_on_path_missing(monkeypatch):
    monkeypatch.setattr(dogfood.shutil, "which", lambda _cmd: None)
    assert dogfood.agent_on_path("claude") is None


def test_agent_executable_usable_requires_invokable_binary(tmp_path, monkeypatch):
    missing_ok, missing_detail = dogfood.agent_executable_usable("definitely-not-an-agent-cli")
    assert missing_ok is False
    assert "not on PATH" in missing_detail

    _make_invokable_cli(tmp_path, "claude")
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ.get("PATH", ""))
    ok, detail = dogfood.agent_executable_usable("claude")
    assert ok is True, detail
    assert "invokable" in detail


def test_agent_executable_usable_rejects_non_executable_path(tmp_path, monkeypatch):
    """A path entry that cannot be invoked must fail the usability check."""
    if os.name == "nt":
        decoy = tmp_path / "claude.txt"
        decoy.write_text("not a cli\n", encoding="utf-8")
    else:
        decoy = tmp_path / "claude"
        decoy.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        decoy.chmod(0o644)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ.get("PATH", ""))
    resolved = dogfood.agent_on_path("claude")
    if resolved is None:
        ok, detail = dogfood.agent_executable_usable("claude")
        assert ok is False
        assert "not on PATH" in detail
    else:
        ok, detail = dogfood.agent_executable_usable("claude")
        assert ok is False, detail


def test_discovery_doctor_ok_smoke(monkeypatch, tmp_path):
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(tmp_path / "ai"))
    try:
        import model_router_ai  # noqa: F401
    except ImportError:
        pytest.skip("model_router_ai not installed")
    ok, detail = dogfood.discovery_doctor_ok()
    assert ok is True, detail
    assert "Doctor" in detail or "completed" in detail
