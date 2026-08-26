"""Persistent user-facing configuration control helpers."""
from __future__ import annotations

import json
import tomllib
from importlib import resources
from pathlib import Path
from typing import Any

from flossware_setup.config_contract import ConfigLayer, ConfigResolver, Policy, resolve_order

DEFAULT_ORDER = ["agents", "providers", "models", "optimization", "validation"]
DEFAULT_CONSTRAINTS = [{"item": "optimization", "after": ["models"], "before": ["validation"]}]
BUILTIN_PROFILES = ("default", "personal")
ORGANIZATION_PROFILES = ("redhat", "redhat-cost-conscious")


def state_dir() -> Path:
    path = Path.home() / ".flossware" / "ai"
    path.mkdir(parents=True, exist_ok=True)
    return path


def profiles_dir() -> Path:
    path = state_dir() / "profiles"
    path.mkdir(parents=True, exist_ok=True)
    return path


def available_profiles() -> tuple[str, ...]:
    """Public profiles plus organization profiles explicitly provisioned locally."""
    local = {p.stem for p in profiles_dir().glob("*.toml") if p.is_file()}
    extra = tuple(name for name in ORGANIZATION_PROFILES if name in local)
    custom = tuple(sorted(local - set(BUILTIN_PROFILES) - set(ORGANIZATION_PROFILES)))
    return BUILTIN_PROFILES + extra + custom


def profile_path(name: str) -> Path:
    return profiles_dir() / f"{name}.toml"


def load_profile(name: str = "personal") -> dict[str, Any]:
    if name not in available_profiles():
        raise ValueError(f"unknown profile: {name}")
    local = profile_path(name)
    if local.is_file():
        try:
            return tomllib.loads(local.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ValueError(f"invalid profile: {name}") from exc
    if name == "default":
        resource = resources.files("flossware_setup.profiles").joinpath("default.toml")
        with resource.open("rb") as stream:
            return tomllib.load(stream)
    if name == "personal":
        return {
            "profile": "personal",
            "model_policy": {"allowed_providers": ["*configured*"], "allow_local_models": True,
                              "allow_unconfigured_providers": False, "allow_personal_accounts": True,
                              "allow_provider_fallback": True},
            "optimization": {"enabled": True, "strategy": "hybrid"},
            "cost": {"monthly_limit_usd": 0.0, "hard_limit": False},
        }
    raise ValueError(f"unknown profile: {name}")


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
        return resolve_order([str(x) for x in order], DEFAULT_CONSTRAINTS)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return list(DEFAULT_ORDER)


def save_order(order: list[str]) -> Path:
    resolved = resolve_order([str(x) for x in order], DEFAULT_CONSTRAINTS)
    path = order_path()
    path.write_text(json.dumps({"version": 1, "order": resolved}, indent=2) + "\n", encoding="utf-8")
    return path


def effective_config(profile_name: str = "personal") -> ConfigResolver:
    profile = load_profile(profile_name)
    model_policy = profile.get("model_policy", {})
    cost = profile.get("cost", {})
    optimization = profile.get("optimization", {})
    allowed = list(model_policy.get("allowed_providers") or [])
    provider = allowed[0] if allowed and allowed[0] != "*configured*" else "auto"
    resolver = ConfigResolver()
    resolver.add_layer(ConfigLayer("defaults", 0, {
        "provider": provider,
        "budget.monthly": float(cost.get("monthly_limit_usd", 0.0)),
        "optimization.population": int(optimization.get("genetic", {}).get("population_size", 30)),
        "optimization.strategy": str(optimization.get("strategy", "hybrid")),
    }))
    resolver.add_layer(ConfigLayer(f"profile:{profile_name}", 300, {
        "provider": provider,
        "budget.monthly": float(cost.get("monthly_limit_usd", 0.0)),
        "policy.allow_personal_accounts": bool(model_policy.get("allow_personal_accounts", profile_name == "personal")),
        "policy.allow_unknown_providers": bool(model_policy.get("allow_unconfigured_providers", False)),
        "policy.allow_provider_fallback": bool(model_policy.get("allow_provider_fallback", False)),
        "policy.hard_budget": bool(cost.get("hard_limit", False)),
        "optimization.strategy": str(optimization.get("strategy", "hybrid")),
    }))
    return resolver


def validate_effective_config(profile_name: str = "personal") -> dict[str, Any]:
    config = effective_config(profile_name).resolve()
    profile = load_profile(profile_name)
    allowed = list(profile.get("model_policy", {}).get("allowed_providers") or [])
    if allowed and allowed != ["*configured*"]:
        Policy(allowed={"provider": allowed}).validate(config)
        if float(config.get("budget.monthly", 0)) > 300.0:
            raise ValueError("budget.monthly exceeds the configured $300 ceiling")
        if config.get("policy.allow_personal_accounts"):
            raise ValueError("personal accounts are forbidden by the selected work profile")
        if config.get("policy.allow_unknown_providers"):
            raise ValueError("unknown providers are forbidden by the selected work profile")
        if config.get("policy.allow_provider_fallback"):
            raise ValueError("provider fallback is forbidden by the selected work profile")
    return config
