"""Secret-free credential references stored in agent-setup profiles.

Profiles may record where a credential comes from, but never the secret itself.
The actual value is resolved by a credential provider at execution time.
"""

from __future__ import annotations

from typing import Any

from flossware_setup.config_control import load_profile, validate_profile_name, write_profile

DEFAULT_SOURCE = "environment"
SUPPORTED_SOURCES = frozenset(
    {
        "environment",
        "keychain",
        "encrypted_file",
        "vault",
        "cloud_secret_manager",
        "external",
    }
)


def _validate_ref(value: str, label: str) -> str:
    value = value.strip()
    if not value or any(ch in value for ch in "\r\n\x00"):
        raise ValueError(f"{label} must be a non-empty single-line reference")
    return value


def _validate_source(source: str) -> str:
    source = source.strip().lower()
    if source not in SUPPORTED_SOURCES:
        raise ValueError(f"unsupported credential source: {source}")
    return source


def credential_references(profile: str = "default") -> dict[str, dict[str, str]]:
    """Return secret-free credential references configured for *profile*."""
    safe = validate_profile_name(profile)
    data = load_profile(safe)
    raw = data.get("credentials", {})
    if not isinstance(raw, dict):
        raise ValueError("profile credentials must be a table")
    result: dict[str, dict[str, str]] = {}
    for name, value in raw.items():
        if not isinstance(value, dict):
            continue
        ref = value.get("ref")
        source = value.get("source", DEFAULT_SOURCE)
        if isinstance(ref, str) and isinstance(source, str):
            result[str(name)] = {
                "ref": _validate_ref(ref, "credential ref"),
                "source": _validate_source(source),
            }
    return result


def set_credential_reference(
    profile: str,
    name: str,
    ref: str,
    *,
    source: str = DEFAULT_SOURCE,
) -> Any:
    """Persist a secret-free credential reference in a profile."""
    safe = validate_profile_name(profile)
    name = _validate_ref(name, "credential name")
    ref = _validate_ref(ref, "credential ref")
    source = _validate_source(source)
    data = load_profile(safe)
    credentials = data.setdefault("credentials", {})
    if not isinstance(credentials, dict):
        raise ValueError("profile credentials must be a table")
    credentials[name] = {"ref": ref, "source": source}
    return write_profile(safe, data)


def remove_credential_reference(profile: str, name: str) -> Any:
    """Remove a credential reference without touching the underlying secret."""
    safe = validate_profile_name(profile)
    data = load_profile(safe)
    credentials = data.get("credentials", {})
    if not isinstance(credentials, dict):
        return write_profile(safe, data)
    credentials.pop(name, None)
    return write_profile(safe, data)
