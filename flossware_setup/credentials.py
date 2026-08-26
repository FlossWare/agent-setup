"""Credential presence checks without reading or storing secret values."""

from __future__ import annotations

import os
import re
from typing import Any, Iterable

from flossware_setup.catalog import PROVIDERS

# Key-name substrings that must never appear as persisted values or artifact content.
_SECRET_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "auth_token",
    "authorization",
    "password",
    "passwd",
    "secret",
    "private_key",
    "client_secret",
    "session_token",
    "cookie",
)

# Value patterns treated as credential/PII leakage in generated text.
_SECRET_VALUE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"sk-proj-[A-Za-z0-9_-]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"gho_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\s\"]{8,}"),
)

# Rough email / personal-identifier patterns for account-label hygiene.
_IDENTITY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
)

# Keys allowed in `.flossware-ai.json` project state (whitelist).
ALLOWED_STATE_KEYS: frozenset[str] = frozenset(
    {
        "tool",
        "profile",
        "budget_policy_id",
        "budget_policy",
        "monthly_budget",
        "capabilities",
        "providers",
        "provider_env_vars",
        "credential_values_written",
        "agents",
        "theme",
        "repo_dir",
        "schema_version",
    }
)


def credential_status() -> dict[str, bool]:
    """Return whether each known provider env var is set (true/false only)."""
    return {name: bool(os.environ.get(env)) for name, env, _ in PROVIDERS}


def environment_names() -> dict[str, str]:
    """Map provider display names to environment variable names."""
    return {name: env for name, env, _ in PROVIDERS}


def is_secret_key_name(name: str) -> bool:
    """True if *name* looks like a credential-bearing config key."""
    lowered = name.lower().replace("-", "_")
    return any(frag in lowered for frag in _SECRET_KEY_FRAGMENTS)


def text_contains_secret_material(text: str) -> bool:
    """True if *text* appears to embed credential or token material."""
    if not text:
        return False
    return any(p.search(text) for p in _SECRET_VALUE_PATTERNS)


def text_contains_identity_material(text: str) -> bool:
    """True if *text* contains obvious personal identifiers (e.g. email)."""
    if not text:
        return False
    return any(p.search(text) for p in _IDENTITY_PATTERNS)


def _scan_value(value: Any, loc: str) -> list[str]:
    """Scan a single value (recursive for nested structures)."""
    if isinstance(value, dict):
        return scan_mapping_for_secrets(value, path=loc)
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for i, item in enumerate(value):
            out.extend(_scan_value(item, f"{loc}[{i}]"))
        return out
    if isinstance(value, str):
        findings: list[str] = []
        if text_contains_secret_material(value):
            findings.append(f"secret-like value at {loc}")
        if text_contains_identity_material(value) and "@" in value:
            findings.append(f"identity-like value at {loc}")
        return findings
    return []


def scan_mapping_for_secrets(data: dict[str, Any], *, path: str = "") -> list[str]:
    """Return human-readable findings for secret-like keys or values in *data*."""
    findings: list[str] = []
    for key, value in data.items():
        loc = f"{path}.{key}" if path else str(key)
        if is_secret_key_name(str(key)):
            findings.append(f"forbidden key name: {loc}")
        findings.extend(_scan_value(value, loc))
    return findings


def assert_no_secret_material(text: str, *, label: str = "content") -> None:
    """Raise ValueError if *text* embeds credential-like material."""
    if text_contains_secret_material(text):
        raise ValueError(
            f"{label} must not contain credential material; "
            "use environment variables or an OS/agent credential store instead"
        )


def filter_state_keys(data: dict[str, Any]) -> dict[str, Any]:
    """Keep only whitelist keys for project state persistence."""
    return {k: v for k, v in data.items() if k in ALLOWED_STATE_KEYS}
