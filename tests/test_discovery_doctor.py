"""Regression tests for discovery/doctor integration with model-router-ai."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_PATH = ROOT / "scripts" / "discovery.py"


def _load_discovery_module(monkeypatch, tmp_path, *, export_identities_at_root: bool):
    """Load scripts/discovery.py as a fresh module with a controlled model_router_ai."""
    # Isolate FLOSSWARE_AI_ROOT so doctor never touches the real home state.
    ai_root = tmp_path / "ai"
    ai_root.mkdir()
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(ai_root))

    # Build a minimal model_router_ai package that mirrors the real public surface.
    pkg = types.ModuleType("model_router_ai")
    discovery_mod = types.ModuleType("model_router_ai.discovery")

    def provider_definitions():
        return [{"id": "anthropic", "name": "Anthropic"}]

    def discover_accounts():
        return []

    def discover_all_models():
        return []

    def discover_identities(timeout: float = 8.0):
        return []

    discovery_mod.provider_definitions = provider_definitions
    discovery_mod.discover_accounts = discover_accounts
    discovery_mod.discover_all_models = discover_all_models
    discovery_mod.discover_identities = discover_identities

    # Package root always exposes the core discovery helpers used by doctor.
    pkg.provider_definitions = provider_definitions
    pkg.discover_accounts = discover_accounts
    pkg.discover_all_models = discover_all_models
    if export_identities_at_root:
        pkg.discover_identities = discover_identities

    monkeypatch.setitem(sys.modules, "model_router_ai", pkg)
    monkeypatch.setitem(sys.modules, "model_router_ai.discovery", discovery_mod)

    # Ensure a clean load of scripts/discovery.py under a unique module name.
    mod_name = (
        "agent_setup_discovery_with_root"
        if export_identities_at_root
        else "agent_setup_discovery_without_root"
    )
    sys.modules.pop(mod_name, None)
    spec = importlib.util.spec_from_file_location(mod_name, DISCOVERY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module, ai_root


@pytest.mark.parametrize("export_identities_at_root", [True, False])
def test_discovery_imports_discover_identities(monkeypatch, tmp_path, export_identities_at_root):
    """doctor/accounts must load even when package root omits discover_identities."""
    module, _ = _load_discovery_module(
        monkeypatch, tmp_path, export_identities_at_root=export_identities_at_root
    )
    assert callable(module.discover_identities)
    assert module.discover_identities() == []


@pytest.mark.parametrize("export_identities_at_root", [True, False])
def test_doctor_command_succeeds(monkeypatch, tmp_path, export_identities_at_root, capsys):
    """flossware-ai doctor (scripts/discovery.py doctor) must not raise ImportError."""
    module, _ = _load_discovery_module(
        monkeypatch, tmp_path, export_identities_at_root=export_identities_at_root
    )
    code = module.doctor()
    assert code == 0
    out = capsys.readouterr().out
    assert "FlossWare AI | Doctor" in out
    assert "Credential values:    not displayed" in out
    assert "Provider definitions:" in out


def test_accounts_verify_uses_identities_without_root_export(monkeypatch, tmp_path, capsys):
    module, _ = _load_discovery_module(
        monkeypatch, tmp_path, export_identities_at_root=False
    )
    module.accounts(verify=True)
    out = capsys.readouterr().out
    assert "FlossWare AI | Accounts" in out
    assert "No providers configured" in out


def test_main_doctor_cli_path(monkeypatch, tmp_path, capsys):
    module, _ = _load_discovery_module(
        monkeypatch, tmp_path, export_identities_at_root=False
    )
    monkeypatch.setattr(sys, "argv", ["discovery.py", "doctor"])
    code = module.main()
    assert code == 0
    assert "FlossWare AI | Doctor" in capsys.readouterr().out
