"""Persistent user-facing configuration control helpers."""
from __future__ import annotations

import json
import os
import tomllib
from importlib import resources
from pathlib import Path
from typing import Any

from flossware_setup.config_contract import ConfigLayer, ConfigResolver, Policy, resolve_order
from flossware_setup.tui.themes import THEME_NAMES as THEMES

KEY_PROVIDER = "provider"
KEY_BUDGET_MONTHLY = "budget.monthly"
KEY_OPT_STRATEGY = "optimization.strategy"
KEY_OPT_POPULATION = "optimization.population"
KEY_POLICY_PERSONAL = "policy.allow_personal_accounts"
KEY_POLICY_UNKNOWN = "policy.allow_unknown_providers"
KEY_POLICY_FALLBACK = "policy.allow_provider_fallback"
KEY_POLICY_HARD_BUDGET = "policy.hard_budget"
PROVIDER_CONFIGURED = "*configured*"
DEFAULT_ORDER = ["agents", "providers", "models", "optimization", "validation"]
DEFAULT_CONSTRAINTS = [{"item": "optimization", "after": ["models"], "before": ["validation"]}]
BUILTIN_PROFILES = ("default",)
ORGANIZATION_PROFILES: tuple[str, ...] = ()


def flossware_root() -> Path:
    """Return the canonical install/state root."""
    for key in ("FLOSSWARE_AI_ROOT", "FLOSSWARE_INSTALL_ROOT"):
        raw = os.environ.get(key)
        if not raw:
            continue
        text = raw.strip()
        if not text or "\0" in text or not os.path.isabs(text):
            continue
        try:
            path = Path(text).expanduser().resolve()
            path.mkdir(parents=True, exist_ok=True)
            return path
        except (OSError, RuntimeError, ValueError):
            continue
    path = (Path.home() / ".flossware" / "ai").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_dir() -> Path: return flossware_root()
def profiles_dir() -> Path:
    path = state_dir() / "profiles"; path.mkdir(parents=True, exist_ok=True); return path
def available_profiles() -> tuple[str, ...]:
    local = {p.stem for p in profiles_dir().glob("*.toml") if p.is_file()}
    extra = tuple(name for name in ORGANIZATION_PROFILES if name in local)
    custom = tuple(sorted(local - set(BUILTIN_PROFILES) - set(ORGANIZATION_PROFILES)))
    return BUILTIN_PROFILES + extra + custom
def profile_path(name: str) -> Path: return profiles_dir() / f"{name}.toml"

def load_profile(name: str = "default") -> dict[str, Any]:
    """Load an explicitly selected profile."""
    local = profile_path(name)
    if local.is_file():
        try: return tomllib.loads(local.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc: raise ValueError(f"invalid profile: {name}") from exc
    if name == "default":
        resource = resources.files("flossware_setup.profiles").joinpath("default.toml")
        with resource.open("rb") as stream: return tomllib.load(stream)
    if name == "personal":
        return {"profile": "personal", "model_policy": {"allowed_providers": [PROVIDER_CONFIGURED], "allow_local_models": True, "allow_unconfigured_providers": False, "allow_personal_accounts": True, "allow_provider_fallback": True}, "optimization": {"enabled": True, "strategy": "hybrid"}, "cost": {"monthly_limit_usd": 0.0, "hard_limit": False}}
    raise ValueError(f"unknown profile: {name}")

def order_path() -> Path: return state_dir() / "menu-order.json"
def load_order() -> list[str]:
    path = order_path()
    if not path.is_file(): return list(DEFAULT_ORDER)
    try:
        data = json.loads(path.read_text(encoding="utf-8")); order = data.get("order")
        if not isinstance(order, list) or set(order) != set(DEFAULT_ORDER) or len(order) != len(DEFAULT_ORDER): return list(DEFAULT_ORDER)
        return resolve_order([str(x) for x in order], DEFAULT_CONSTRAINTS)
    except (OSError, ValueError, TypeError, json.JSONDecodeError): return list(DEFAULT_ORDER)
def save_order(order: list[str]) -> Path:
    resolved = resolve_order([str(x) for x in order], DEFAULT_CONSTRAINTS)
    path = order_path(); path.write_text(json.dumps({"version": 1, "order": resolved}, indent=2) + "\n", encoding="utf-8"); return path

def bindings_path() -> Path: return state_dir() / "profile-bindings.toml"
def _norm(path: str | Path) -> str: return os.path.normcase(str(Path(path).expanduser().resolve()))
def load_bindings() -> dict[str, str]:
    path = bindings_path()
    if not path.is_file(): return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8")); raw = data.get("bindings", {})
        return {_norm(k): str(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, str) and v in available_profiles()}
    except (OSError, tomllib.TOMLDecodeError): return {}
def save_bindings(bindings: dict[str, str]) -> Path:
    path = bindings_path(); path.parent.mkdir(parents=True, exist_ok=True); lines = ["# FlossWare directory-to-profile bindings", "[bindings]"]
    for directory, profile in sorted((_norm(k), v) for k, v in bindings.items()):
        if profile in available_profiles(): lines.append(f'{directory!r} = "{profile}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8"); return path
def bind_directory(directory: str | Path, profile: str) -> Path:
    if profile not in available_profiles(): raise ValueError(f"unknown profile: {profile}")
    bindings = load_bindings(); bindings[_norm(directory)] = profile; return save_bindings(bindings)
def unbind_directory(directory: str | Path) -> Path:
    bindings = load_bindings(); bindings.pop(_norm(directory), None); return save_bindings(bindings)
def matching_bindings(directory: str | Path | None = None) -> list[tuple[str, str]]:
    target = Path(directory or Path.cwd()).expanduser().resolve(); normalized = _norm(target); matches = []
    for root, profile in load_bindings().items():
        try: Path(normalized).relative_to(root)
        except ValueError: continue
        matches.append((root, profile))
    matches.sort(key=lambda item: len(item[0]), reverse=True); return matches
def profile_for_directory(directory: str | Path | None = None) -> tuple[str, str | None]:
    matches = matching_bindings(directory); return (matches[0][1], matches[0][0]) if matches else ("default", None)
def binding_provenance(directory: str | Path | None = None) -> dict[str, object]:
    target = Path(directory or Path.cwd()).expanduser().resolve(); matches = matching_bindings(target); profile, source = profile_for_directory(target)
    return {"directory": _norm(target), "effective_profile": profile, "source": source, "source_kind": "directory-binding" if source else "default-profile", "winning_binding": matches[0] if matches else None, "parent_bindings": matches[1:] if len(matches) > 1 else [], "all_matches": matches}
def bindings_grouped_by_profile() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for directory, profile in load_bindings().items(): grouped.setdefault(profile, []).append(directory)
    for dirs in grouped.values(): dirs.sort()
    return grouped

def theme_path() -> Path: return state_dir() / "theme"
_THEME_ALIASES = {"dbase": "dbase4", "dbase-iv": "dbase4", "modern": "monochrome", "default": "monochrome"}
def load_theme() -> str:
    try: value = theme_path().read_text(encoding="utf-8").strip().lower()
    except OSError: value = "turbo"
    value = _THEME_ALIASES.get(value, value); return value if value in THEMES else "turbo"
def save_theme(theme: str) -> Path:
    theme = _THEME_ALIASES.get(theme.strip().lower(), theme.strip().lower())
    if theme not in THEMES: raise ValueError(f"unknown theme: {theme}")
    path = theme_path(); path.write_text(theme + "\n", encoding="utf-8"); return path

def _load_toml_map(path: Path) -> dict:
    if not path.is_file(): return {}
    try: data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError): return {}
    flat: dict = {}
    for key, value in data.items():
        if isinstance(value, dict):
            for sub, subval in value.items():
                if isinstance(subval, (str, int, float, bool)): flat[f"{key}.{sub}"] = subval
        elif isinstance(value, (str, int, float, bool)): flat[key] = value
    return flat

def _env_config_layer() -> dict:
    mapping = {"FLOSSWARE_PROVIDER": KEY_PROVIDER, "FLOSSWARE_BUDGET_MONTHLY": KEY_BUDGET_MONTHLY, "FLOSSWARE_OPTIMIZATION_STRATEGY": KEY_OPT_STRATEGY}; layer: dict = {}
    for env_key, conf_key in mapping.items():
        raw = os.environ.get(env_key)
        if raw is None or raw == "": continue
        if conf_key == KEY_BUDGET_MONTHLY:
            try: layer[conf_key] = float(raw)
            except ValueError: continue
        else: layer[conf_key] = raw
    return layer

def _value_layer(*, provider: str, budget: float, population: int, strategy: str, allow_personal: bool, allow_unknown: bool, allow_fallback: bool, hard_budget: bool) -> dict[str, Any]:
    return {KEY_PROVIDER: provider, KEY_BUDGET_MONTHLY: budget, KEY_OPT_POPULATION: population, KEY_OPT_STRATEGY: strategy, KEY_POLICY_PERSONAL: allow_personal, KEY_POLICY_UNKNOWN: allow_unknown, KEY_POLICY_FALLBACK: allow_fallback, KEY_POLICY_HARD_BUDGET: hard_budget}

def effective_config(profile_name: str = "default") -> ConfigResolver:
    profile = load_profile(profile_name); model_policy = profile.get("model_policy", {}); cost = profile.get("cost", {}); optimization = profile.get("optimization", {}); allowed = list(model_policy.get("allowed_providers") or [])
    provider = allowed[0] if allowed and allowed[0] != PROVIDER_CONFIGURED else "auto"
    defaults = _value_layer(provider="auto", budget=0.0, population=30, strategy="hybrid", allow_personal=True, allow_unknown=True, allow_fallback=True, hard_budget=False)
    profile_layer = _value_layer(provider=provider, budget=float(cost.get("monthly_limit_usd", 0.0) or 0.0), population=int(optimization.get("genetic", {}).get("population_size", 30) or 30), strategy=str(optimization.get("strategy", "hybrid")), allow_personal=bool(model_policy.get("allow_personal_accounts", profile_name == "personal")), allow_unknown=bool(model_policy.get("allow_unconfigured_providers", False)), allow_fallback=bool(model_policy.get("allow_provider_fallback", False)), hard_budget=bool(cost.get("hard_limit", False)))
    resolver = ConfigResolver(); resolver.add_layer(ConfigLayer("defaults", 0, defaults)); resolver.add_layer(ConfigLayer("system", 100, _load_toml_map(state_dir() / "system.toml"))); resolver.add_layer(ConfigLayer("user", 200, _load_toml_map(state_dir() / "user.toml"))); resolver.add_layer(ConfigLayer(f"profile:{profile_name}", 300, profile_layer))
    try:
        from flossware_setup.config import project_state_path
        project_map = _load_toml_map(project_state_path(Path.cwd()).parent / "config.toml")
    except Exception: project_map = {}
    if project_map: resolver.add_layer(ConfigLayer("project", 500, project_map))
    resolver.add_layer(ConfigLayer("environment", 600, _env_config_layer())); return resolver

def validate_effective_config(profile_name: str = "default") -> dict[str, Any]:
    config = effective_config(profile_name).resolve(); profile = load_profile(profile_name); allowed = list(profile.get("model_policy", {}).get("allowed_providers") or [])
    if allowed and allowed != [PROVIDER_CONFIGURED]:
        Policy(allowed={KEY_PROVIDER: allowed}).validate(config)
        if float(config.get(KEY_BUDGET_MONTHLY, 0)) > 300.0: raise ValueError("budget.monthly exceeds the configured $300 ceiling")
        if config.get(KEY_POLICY_PERSONAL): raise ValueError("personal accounts are forbidden by the selected work profile")
        if config.get(KEY_POLICY_UNKNOWN): raise ValueError("unknown providers are forbidden by the selected work profile")
        if config.get(KEY_POLICY_FALLBACK): raise ValueError("provider fallback is forbidden by the selected work profile")
    return config
