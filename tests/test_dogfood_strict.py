"""Regression tests for strict dogfood behavioral checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dogfood  # noqa: E402


def test_agent_on_path_missing(monkeypatch):
    monkeypatch.setattr(dogfood.shutil, "which", lambda _cmd: None)
    assert dogfood.agent_on_path("claude") is None


def test_agent_executable_usable_requires_invokable_binary(tmp_path, monkeypatch):
    missing_ok, missing_detail = dogfood.agent_executable_usable("definitely-not-an-agent-cli")
    assert missing_ok is False
    assert "not on PATH" in missing_detail

    stub = tmp_path / "claude"
    stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ.get("PATH", ""))
    ok, detail = dogfood.agent_executable_usable("claude")
    assert ok is True
    assert "invokable" in detail


def test_discovery_doctor_ok_smoke(monkeypatch, tmp_path):
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(tmp_path / "ai"))
    # discovery imports model_router_ai; skip if unavailable in unit env
    try:
        import model_router_ai  # noqa: F401
    except ImportError:
        pytest.skip("model_router_ai not installed")
    ok, detail = dogfood.discovery_doctor_ok()
    assert ok is True, detail
    assert "Doctor" in detail or "completed" in detail
