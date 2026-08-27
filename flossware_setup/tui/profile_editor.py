"""Interactive profile editor for the curses TUI."""
from __future__ import annotations

from pathlib import Path

from flossware_setup.config_control import available_profiles, profiles_dir

FIELDS = (
    ("allow_local_models", "Allow local models", True),
    ("allow_personal_accounts", "Allow personal accounts", True),
    ("allow_provider_fallback", "Allow provider fallback", True),
    ("allow_unconfigured_providers", "Allow unconfigured providers", False),
    ("optimization_enabled", "Enable optimization", True),
    ("monthly_limit_usd", "Monthly limit (USD)", 0.0),
)


def profile_path(name: str) -> Path:
    return profiles_dir() / f"{name}.toml"


def edit_profile(name: str, values: dict[str, object] | None = None) -> Path:
    """Persist editable profile values and return its TOML path.

    The TUI supplies validated values. Existing unknown TOML keys are preserved
    by the TUI's config layer rather than being silently discarded here.
    """
    if name not in available_profiles():
        raise ValueError(f"unknown profile: {name}")
    path = profile_path(name)
    if values is None:
        return path
    lines = [f"profile = {name!r}", "", "[model_policy]"]
    for key in ("allow_local_models", "allow_personal_accounts", "allow_provider_fallback", "allow_unconfigured_providers"):
        if key in values:
            lines.append(f"{key} = {str(bool(values[key])).lower()}")
    if "optimization_enabled" in values:
        lines += ["", "[optimization]", f"enabled = {str(bool(values['optimization_enabled'])).lower()}"]
    if "monthly_limit_usd" in values:
        lines += ["", "[cost]", f"monthly_limit_usd = {float(values['monthly_limit_usd']):.2f}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
