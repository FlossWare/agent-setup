"""Persistent user-facing configuration control helpers."""
from __future__ import annotations

import json
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
        if not isinstance(order, list) or set(order) != set(DEFAULT_ORDER):
            return list(DEFAULT_ORDER)
        resolve_order(order, DEFAULT_CONSTRAINTS)
        return [str(x) for x in order]
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return list(DEFAULT_ORDER)


def save_order(order: list[str]) -> Path:
    resolved = resolve_order(order, DEFAULT_CONSTRAINTS)
    path = order_path()
    path.write_text(json.dumps({"version": 1, "order": resolved}, indent=2) + "\n", encoding="utf-8")
    return path


def effective_config() -> ConfigResolver:
    resolver = ConfigResolver()
    resolver.add_layer(ConfigLayer("defaults", 0, {
        "provider": "anthropic",
        "budget.monthly": 300.0,
        "optimization.population": 30,
        "optimization.strategy": "hybrid",
    }))
    resolver.add_layer(ConfigLayer("profile:redhat-cost-conscious", 300, {
        "provider": "anthropic",
        "budget.monthly": 300.0,
        "policy.allow_personal_accounts": False,
        "policy.allow_unknown_providers": False,
        "policy.hard_budget": True,
    }))
    return resolver


def validate_effective_config() -> dict[str, Any]:
    config = effective_config().resolve()
    Policy(allowed={"provider": ["anthropic"]}).validate(config)
    if float(config.get("budget.monthly", 0)) > 300.0:
        raise ValueError("budget.monthly exceeds the configured $300 ceiling")
    return config
