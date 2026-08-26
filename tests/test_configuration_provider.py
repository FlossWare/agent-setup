"""Shared ConfigurationProvider contract (#51)."""

from __future__ import annotations

import json

from flossware_setup.config_contract import (
    CONTRACT_ID,
    LAYER_ORDER,
    SCHEMA_VERSION,
    ConfigurationProvider,
    EffectiveConfiguration,
    LocalConfigurationProvider,
)
from flossware_setup.config_contract.provider import SAFE_VALUE_KEYS, _sanitize_values


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
    assert set(cfg.values.keys()) <= SAFE_VALUE_KEYS
    assert isinstance(cfg.credentials_present, dict)
    assert all(isinstance(v, bool) for v in cfg.credentials_present.values())
    blob = json.dumps(cfg.to_wire())
    assert "sk-should-not-appear" not in blob
    assert "sk-" not in blob or "sk-should" not in blob


def test_sanitize_drops_secret_keys_and_values() -> None:
    cleaned = _sanitize_values(
        {
            "provider": "anthropic",
            "openai_api_key": "sk-abcdefghijklmnopqrstuvwxyz",
            "budget.monthly": 50.0,
            "nested_secret": {"token": "ghp_" + "A" * 30},
        }
    )
    assert "openai_api_key" not in cleaned
    assert "nested_secret" not in cleaned
    assert cleaned["provider"] == "anthropic"
    assert cleaned["budget.monthly"] == 50.0


def test_resolve_never_raises_on_policy_failure(tmp_path, monkeypatch) -> None:
    """Contract: resolve returns policy_violations instead of raising."""
    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "ai"
    )
    profiles = tmp_path / "ai" / "profiles"
    profiles.mkdir(parents=True)
    # Minimal work-like profile that forbids personal accounts
    (profiles / "strict-work.toml").write_text(
        """
profile = "strict-work"
[model_policy]
allowed_providers = ["anthropic"]
allow_personal_accounts = false
allow_unconfigured_providers = false
allow_provider_fallback = false
[cost]
monthly_limit_usd = 50.0
hard_limit = true
""",
        encoding="utf-8",
    )
    # Force profile_for_directory to return our strict profile
    monkeypatch.setattr(
        "flossware_setup.config_control.profile_for_directory",
        lambda directory=None: ("strict-work", None),
    )
    # effective_config will still build from profile; allow personal may be false
    cfg = LocalConfigurationProvider().resolve(tmp_path)
    assert isinstance(cfg, EffectiveConfiguration)
    # Does not raise; policy_ok is a boolean
    assert isinstance(cfg.policy_ok, bool)
    assert isinstance(cfg.policy_violations, tuple)


def test_explain_returns_text(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "ai"
    )
    (tmp_path / "ai").mkdir(parents=True)
    text = LocalConfigurationProvider().explain("provider", tmp_path)
    assert isinstance(text, str)
    assert len(text) > 0


def test_wire_form_is_json_serializable(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "ai"
    )
    (tmp_path / "ai").mkdir(parents=True)
    wire = LocalConfigurationProvider().resolve(tmp_path).to_wire()
    encoded = json.dumps(wire)
    assert CONTRACT_ID in encoded
    assert "schema_version" in wire


def test_profile_budget_limit_enforced_as_is(tmp_path, monkeypatch) -> None:
    """A $50 profile limit must reject $200; must not be raised to $300."""
    from flossware_setup.config_contract.provider import _policy_violations_for

    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "ai"
    )
    profiles = tmp_path / "ai" / "profiles"
    profiles.mkdir(parents=True)
    (profiles / "tight.toml").write_text(
        """
profile = "tight"
[model_policy]
allowed_providers = ["anthropic"]
allow_personal_accounts = false
allow_unconfigured_providers = false
allow_provider_fallback = false
[cost]
monthly_limit_usd = 50.0
hard_limit = true
""",
        encoding="utf-8",
    )
    # Over profile limit but under 300 — must still violate
    violations = _policy_violations_for(
        "tight",
        {
            "provider": "anthropic",
            "budget.monthly": 200.0,
            "policy.allow_personal_accounts": False,
            "policy.allow_unknown_providers": False,
            "policy.allow_provider_fallback": False,
        },
    )
    assert violations
    assert any("50" in v or "profile limit" in v for v in violations)
    # Within profile limit is fine for budget (other flags ok)
    ok = _policy_violations_for(
        "tight",
        {
            "provider": "anthropic",
            "budget.monthly": 40.0,
            "policy.allow_personal_accounts": False,
            "policy.allow_unknown_providers": False,
            "policy.allow_provider_fallback": False,
        },
    )
    assert not any("budget" in v for v in ok)


def test_org_hard_limit_independent_of_profile_limit(tmp_path, monkeypatch) -> None:
    from flossware_setup.config_contract.provider import _policy_violations_for

    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "ai"
    )
    profiles = tmp_path / "ai" / "profiles"
    profiles.mkdir(parents=True)
    (profiles / "org.toml").write_text(
        """
profile = "org"
[model_policy]
allowed_providers = ["anthropic"]
allow_personal_accounts = false
allow_unconfigured_providers = false
allow_provider_fallback = false
[cost]
monthly_limit_usd = 500.0
org_hard_limit_usd = 300.0
hard_limit = true
""",
        encoding="utf-8",
    )
    violations = _policy_violations_for(
        "org",
        {
            "provider": "anthropic",
            "budget.monthly": 400.0,
            "policy.allow_personal_accounts": False,
            "policy.allow_unknown_providers": False,
            "policy.allow_provider_fallback": False,
        },
    )
    assert any("organizational hard limit" in v for v in violations)
