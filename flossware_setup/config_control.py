"""Persistent user-facing configuration control helpers."""
from __future__ import annotations

import json
import tomllib
from importlib import resources
from pathlib import Path
from typing import Any

from flossware_setup.config_contract import ConfigLayer, ConfigResolver, Policy, resolve_order

DEFAULT_ORDER = ["agents", "providers", "models", "optimization", "validation"]
DEFAULT_CONSTRAINTS = [
    {"item": "optimization", "after": ["models"], "before": ["validation"]},
]


def state_dir() -> Path:
    path = Path.home() / ".flossware" / "ai"
    path.mkdir(parents=True, exist_ok=True)
    return path


def order_path() -> Path:
    return state_dir() / "menu-order.json"


def load_order() -> list[str]:
    path = order_path()
    if not path.is_file():
        return list(DEFAULT_ORDER)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        order = data.get("order")
        if not isinstance(order, list) or set(order) != set(DEFAULT_ORDER) or len(order) != len(DEFAULT_ORDER):
            return list(DEFAULT_ORDER)
        # Return the constraint-resolved order, never a persisted order that
        # merely happened to contain all the right names.
        return resolve_order([str(x) for x in order], DEFAULT_CONSTRAINTS)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return list(DEFAULT_ORDER)


def save_order(order: list[str]) -> Path:
    resolved = resolve_order([str(x) for x in order], DEFAULT_CONSTRAINTS)
    path = order_path()
    path.write_text(json.dumps({"version": 1, "order": resolved}, indent=2) + "\n", encoding="utf-8")
    return path


def load_profile(name: str = "redhat-cost-conscious") -> dict[str, Any]:
    """Load a packaged TOML profile without network access or credentials."""
    resource = resources.files("flossware_setup.profiles").joinpath(f"{name}.toml")
    try:
        with resource.open("rb") as stream:
            return tomllib.load(stream)
    except FileNotFoundError as exc:
        raise ValueError(f"unknown profile: {name}") from exc


def effective_config(profile_name: str = "redhat-cost-conscious") -> ConfigResolver:
    profile = load_profile(profile_name)
    model_policy = profile.get("model_policy", {})
    cost = profile.get("cost", {})
    optimization = profile.get("optimization", {})
    resolver = ConfigResolver()
    resolver.add_layer(ConfigLayer("defaults", 0, {
        "provider": "anthropic",
        "budget.monthly": 300.0,
        "optimization.population": 30,
        "optimization.strategy": "hybrid",
    }))
    resolver.add_layer(ConfigLayer(f"profile:{profile_name}", 300, {
        "provider": (model_policy.get("allowed_providers") or ["anthropic"])[0],
        "budget.monthly": float(cost.get("monthly_limit_usd", 300.0)),
        "policy.allow_personal_accounts": bool(model_policy.get("allow_personal_accounts", False)),
        "policy.allow_unknown_providers": bool(model_policy.get("allow_unconfigured_providers", False)),
        "policy.allow_provider_fallback": bool(model_policy.get("allow_provider_fallback", False)),
        "policy.hard_budget": bool(cost.get("hard_limit", True)),
        "optimization.strategy": str(optimization.get("strategy", "hybrid")),
    }))
    return resolver


def validate_effective_config(profile_name: str = "redhat-cost-conscious") -> dict[str, Any]:
    config = effective_config(profile_name).resolve()
    Policy(allowed={"provider": ["anthropic"]}).validate(config)
    if float(config.get("budget.monthly", 0)) > 300.0:
        raise ValueError("budget.monthly exceeds the configured $300 ceiling")
    if config.get("policy.allow_personal_accounts"):
        raise ValueError("personal accounts are forbidden by the selected work profile")
    if config.get("policy.allow_unknown_providers"):
        raise ValueError("unknown providers are forbidden by the selected work profile")
    if config.get("policy.allow_provider_fallback"):
        raise ValueError("provider fallback is forbidden by the selected work profile")
    return config
