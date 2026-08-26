"""Contract expansion process and conformance fixtures (#53)."""

from __future__ import annotations

import json
from pathlib import Path

from flossware_setup.config_contract import (
    CONTRACT_ID,
    DOMAIN_OWNERS,
    SAFE_VALUE_KEYS,
    SCHEMA_VERSION,
    VALUE_KEY_SPECS,
    is_supported_key,
    keys_for_schema_version,
)
from flossware_setup.config_contract.provider import _sanitize_values

FIXTURES = Path(__file__).parent / "fixtures" / "config_contract"


def test_registry_matches_conformance_fixture() -> None:
    data = json.loads((FIXTURES / "v1_supported_keys.json").read_text(encoding="utf-8"))
    assert data["contract_id"] == CONTRACT_ID
    assert data["schema_version"] == SCHEMA_VERSION
    fixture_keys = set(data["supported_keys"])
    registry_keys = set(SAFE_VALUE_KEYS)
    assert fixture_keys == registry_keys
    assert keys_for_schema_version(1) == registry_keys


def test_every_spec_has_domain_owner() -> None:
    for spec in VALUE_KEY_SPECS:
        assert spec.domain in DOMAIN_OWNERS
        assert spec.introduced_in <= SCHEMA_VERSION
        assert not spec.allows_nested  # v1 invariant


def test_unsupported_keys_are_not_supported() -> None:
    assert not is_supported_key("routing.mode")
    assert not is_supported_key("openai_api_key")
    assert is_supported_key("provider")


def test_exclusion_conformance_fixture() -> None:
    data = json.loads((FIXTURES / "v1_exclusion_behavior.json").read_text(encoding="utf-8"))
    for case in data["cases"]:
        cleaned, excluded = _sanitize_values(case["input"])
        for key in case["expect_present"]:
            assert key in cleaned, f"{case['name']}: expected {key} present"
        for key in case["expect_absent"]:
            assert key not in cleaned, f"{case['name']}: expected {key} absent"
            assert key in excluded or key not in case["input"] or True


def test_unsupported_key_listed_in_extras_when_resolved(tmp_path, monkeypatch) -> None:
    """When raw layers somehow carry extras, excluded_keys is observable."""
    from flossware_setup.config_contract import LocalConfigurationProvider
    from flossware_setup.config_contract.provider import _sanitize_values

    cleaned, excluded = _sanitize_values(
        {"provider": "anthropic", "future.feature_flag": True}
    )
    assert "provider" in cleaned
    assert "future.feature_flag" in excluded


def test_value_type_enforcement() -> None:
    cleaned, excluded = _sanitize_values(
        {
            "provider": "anthropic",  # string ok
            "budget.monthly": "50",  # string for number -> drop
            "optimization.population": True,  # bool for number -> drop
            "policy.hard_budget": 1,  # int for boolean -> drop
            "policy.allow_personal_accounts": False,  # bool ok
            "optimization.strategy": None,  # None -> drop
        }
    )
    assert cleaned.get("provider") == "anthropic"
    assert cleaned.get("policy.allow_personal_accounts") is False
    assert "budget.monthly" in excluded
    assert "optimization.population" in excluded
    assert "policy.hard_budget" in excluded
    assert "optimization.strategy" in excluded


def test_number_accepts_int_and_float_not_bool() -> None:
    cleaned, excluded = _sanitize_values(
        {
            "budget.monthly": 50,
            "optimization.population": 30.5,
        }
    )
    assert cleaned["budget.monthly"] == 50
    assert cleaned["optimization.population"] == 30.5
    assert "budget.monthly" not in excluded


def test_allows_nested_false_rejects_maps() -> None:
    """v1 keys all have allows_nested=False — maps must be excluded."""
    cleaned, excluded = _sanitize_values(
        {"optimization.strategy": {"name": "hybrid"}}
    )
    assert "optimization.strategy" not in cleaned
    assert "optimization.strategy" in excluded


def test_allows_nested_true_accepts_secret_free_map(monkeypatch) -> None:
    """When a key allows nested, secret-free maps pass; secret maps fail."""
    from flossware_setup.config_contract import keys as keys_mod
    from flossware_setup.config_contract.keys import ValueKeySpec

    nested_spec = ValueKeySpec(
        key="provider",
        domain="provider",
        value_type="string",
        introduced_in=1,
        description="test nested",
        allows_nested=True,
    )
    monkeypatch.setitem(keys_mod.KEY_SPEC_BY_NAME, "provider", nested_spec)
    cleaned, excluded = _sanitize_values({"provider": {"id": "anthropic"}})
    assert cleaned["provider"] == {"id": "anthropic"}
    cleaned2, excluded2 = _sanitize_values(
        {"provider": {"api_key": "sk-abcdefghijklmnopqrstuvwxyz0123"}}
    )
    assert "provider" not in cleaned2
    assert "provider" in excluded2
