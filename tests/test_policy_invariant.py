"""Policy is applied after resolve; lower layers cannot escape constraints (#38/#42)."""

from __future__ import annotations

import pytest

from flossware_setup.config_contract import ConfigLayer, ConfigResolver, Policy, PolicyError


def test_policy_rejects_provider_outside_allowlist_after_merge() -> None:
    resolver = ConfigResolver()
    resolver.add_layer(ConfigLayer("system", 0, {"provider": "anthropic", "budget.monthly": 100.0}))
    # Higher-priority project layer tries to switch provider.
    resolver.add_layer(ConfigLayer("project", 400, {"provider": "openai"}))
    merged = resolver.resolve()
    assert merged["provider"] == "openai"  # merge alone allows it
    policy = Policy(allowed={"provider": ["anthropic"]})
    with pytest.raises(PolicyError, match="not permitted"):
        policy.validate(merged)
    with pytest.raises(PolicyError):
        resolver.resolve_with_policy(policy)


def test_policy_max_budget_blocks_lower_layer_override() -> None:
    resolver = ConfigResolver()
    resolver.add_layer(ConfigLayer("profile", 300, {"budget.monthly": 100.0}))
    resolver.add_layer(ConfigLayer("project", 400, {"budget.monthly": 50000.0}))
    assert resolver.resolve()["budget.monthly"] == 50000.0
    policy = Policy(max_values={"budget.monthly": 100.0})
    with pytest.raises(PolicyError, match="exceeds policy maximum"):
        resolver.resolve_with_policy(policy)


def test_policy_required_false_flags() -> None:
    resolver = ConfigResolver()
    resolver.add_layer(ConfigLayer("defaults", 0, {"policy.allow_personal_accounts": False}))
    resolver.add_layer(ConfigLayer("project", 400, {"policy.allow_personal_accounts": True}))
    policy = Policy(required_false=["policy.allow_personal_accounts"])
    with pytest.raises(PolicyError, match="must be false"):
        resolver.resolve_with_policy(policy)


def test_compliant_config_passes_policy() -> None:
    resolver = ConfigResolver()
    resolver.add_layer(ConfigLayer("profile", 300, {"provider": "anthropic", "budget.monthly": 50.0}))
    resolver.add_layer(ConfigLayer("project", 400, {"budget.monthly": 40.0}))
    policy = Policy(
        allowed={"provider": ["anthropic"]},
        max_values={"budget.monthly": 100.0},
        required_false=["policy.allow_personal_accounts"],
    )
    result = resolver.resolve_with_policy(policy)
    assert result["provider"] == "anthropic"
    assert result["budget.monthly"] == 40.0
