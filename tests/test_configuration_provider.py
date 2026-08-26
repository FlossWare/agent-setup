"""Shared ConfigurationProvider contract (#51)."""

from __future__ import annotations

from flossware_setup.config_contract import (
    CONTRACT_ID,
    LAYER_ORDER,
    SCHEMA_VERSION,
    ConfigurationProvider,
    EffectiveConfiguration,
    LocalConfigurationProvider,
)


def test_contract_constants() -> None:
    assert SCHEMA_VERSION >= 1
    assert CONTRACT_ID.startswith("flossware.config")
    assert "defaults" in LAYER_ORDER
    assert LAYER_ORDER[-1] == "cli"
    assert "profile" in LAYER_ORDER


def test_local_provider_is_protocol() -> None:
    provider = LocalConfigurationProvider()
    assert isinstance(provider, ConfigurationProvider)


def test_resolve_returns_secret_free_snapshot(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "ai"
    )
    (tmp_path / "ai").mkdir(parents=True)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-not-appear-in-snapshot")
    project = tmp_path / "proj"
    project.mkdir()
    provider = LocalConfigurationProvider()
    cfg = provider.resolve(project)
    assert isinstance(cfg, EffectiveConfiguration)
    assert cfg.schema_version == SCHEMA_VERSION
    assert cfg.contract_id == CONTRACT_ID
    assert cfg.directory == str(project.resolve())
    assert cfg.profile
    assert isinstance(cfg.values, dict)
    assert isinstance(cfg.credentials_present, dict)
    assert all(isinstance(v, bool) for v in cfg.credentials_present.values())
    blob = str(cfg)
    assert "sk-should-not-appear" not in blob


def test_explain_returns_text(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "ai"
    )
    (tmp_path / "ai").mkdir(parents=True)
    text = LocalConfigurationProvider().explain("provider", tmp_path)
    assert isinstance(text, str)
    assert len(text) > 0
