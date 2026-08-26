"""Shared configuration provider interface for coding-agent-setup and Loom.

Contract id: ``flossware.config.v1``. The wire schema is documented in
``docs/configuration-contract.md`` and is independent of this Python binding.
Loom (or any other orchestrator) may implement the same contract without
importing ``coding-agent-setup``.

``resolve()`` **never raises for policy failure**. It always returns an
``EffectiveConfiguration``. When policy is violated, ``policy_violations`` is
non-empty and ``policy_ok`` is False. Callers that require a valid work profile
must check ``policy_ok`` (or ``policy_violations``) themselves.

Secret values must never appear in ``values`` or ``provenance``. Credentials are
represented only as presence booleans in ``credentials_present``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

SCHEMA_VERSION = 1
CONTRACT_ID = "flossware.config.v1"

# Canonical layer order (lowest → highest priority before policy).
LAYER_ORDER = (
    "defaults",
    "system",
    "user",
    "profile",
    "directory",
    "project",
    "environment",
    "cli",
)

# Keys allowed in EffectiveConfiguration.values (whitelist).
SAFE_VALUE_KEYS = frozenset(
    {
        "provider",
        "budget.monthly",
        "optimization.population",
        "optimization.strategy",
        "policy.allow_personal_accounts",
        "policy.allow_unknown_providers",
        "policy.allow_provider_fallback",
        "policy.hard_budget",
    }
)


@dataclass(frozen=True)
class EffectiveConfiguration:
    """Resolved configuration snapshot (secret-free)."""

    schema_version: int
    contract_id: str
    directory: str
    profile: str
    profile_source: str | None  # binding path or None for fallback
    values: dict[str, Any]
    provenance: dict[str, list[tuple[str, Any]]]
    credentials_present: dict[str, bool]
    theme: str
    policy_violations: tuple[str, ...] = ()
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def policy_ok(self) -> bool:
        return not self.policy_violations

    def to_wire(self) -> dict[str, Any]:
        """JSON-serializable representation (language-neutral wire form)."""
        data = asdict(self)
        # provenance tuples -> lists for JSON
        data["provenance"] = {
            k: [[layer, value] for layer, value in entries]
            for k, entries in self.provenance.items()
        }
        data["policy_violations"] = list(self.policy_violations)
        return data


@runtime_checkable
class ConfigurationProvider(Protocol):
    """Stable interface both coding-agent-setup and Loom can implement."""

    def resolve(self, directory: str | Path | None = None) -> EffectiveConfiguration:
        """Merge layers for *directory* and return effective configuration.

        Must not raise solely because policy failed; populate policy_violations.
        """

    def explain(self, key: str, directory: str | Path | None = None) -> str:
        """Human-readable provenance for a single key."""


def _sanitize_values(values: dict[str, Any]) -> dict[str, Any]:
    """Keep only safe keys and drop secret-like material."""
    from flossware_setup.credentials import (
        is_secret_key_name,
        text_contains_secret_material,
    )

    cleaned: dict[str, Any] = {}
    for key, value in values.items():
        if key not in SAFE_VALUE_KEYS:
            continue
        if is_secret_key_name(str(key)):
            continue
        if isinstance(value, str) and text_contains_secret_material(value):
            continue
        if isinstance(value, dict):
            # Nested maps are not part of the v1 wire values surface.
            continue
        cleaned[key] = value
    return cleaned


def _policy_violations_for(profile: str, values: dict[str, Any]) -> tuple[str, ...]:
    """Evaluate work-profile policy against already-merged *values*."""
    from flossware_setup.config_contract.policy import Policy, PolicyError
    from flossware_setup.config_control import load_profile

    try:
        profile_data = load_profile(profile)
    except ValueError as exc:
        return (str(exc),)

    model_policy = profile_data.get("model_policy", {})
    cost = profile_data.get("cost", {})
    allowed = list(model_policy.get("allowed_providers") or [])
    violations: list[str] = []

    # Permissive profiles (*configured* / empty allowlist) skip hard allowlist.
    if allowed and allowed != ["*configured*"]:
        try:
            Policy(allowed={"provider": allowed}).validate(values)
        except PolicyError as exc:
            violations.append(str(exc))
        ceiling = float(cost.get("monthly_limit_usd", 300.0) or 300.0)
        # Organizational templates use a hard $300 ceiling in validate_effective_config.
        if float(values.get("budget.monthly", 0) or 0) > max(ceiling, 300.0):
            violations.append("budget.monthly exceeds the configured $300 ceiling")
        if values.get("policy.allow_personal_accounts"):
            violations.append("personal accounts are forbidden by the selected work profile")
        if values.get("policy.allow_unknown_providers"):
            violations.append("unknown providers are forbidden by the selected work profile")
        if values.get("policy.allow_provider_fallback"):
            violations.append("provider fallback is forbidden by the selected work profile")
    return tuple(violations)


class LocalConfigurationProvider:
    """coding-agent-setup native provider (no Loom required)."""

    def resolve(self, directory: str | Path | None = None) -> EffectiveConfiguration:
        from flossware_setup.config_control import (
            effective_config,
            load_theme,
            profile_for_directory,
        )
        from flossware_setup.credentials import credential_status

        target = Path(directory or Path.cwd()).expanduser().resolve()
        profile, source = profile_for_directory(target)
        resolver = effective_config(profile)
        raw_values = resolver.resolve()
        values = _sanitize_values(raw_values)
        provenance = {
            key: resolver.provenance(key)
            for key in values
        }
        violations = _policy_violations_for(profile, values)
        return EffectiveConfiguration(
            schema_version=SCHEMA_VERSION,
            contract_id=CONTRACT_ID,
            directory=str(target),
            profile=profile,
            profile_source=source,
            values=values,
            provenance=provenance,
            credentials_present=credential_status(),
            theme=load_theme(),
            policy_violations=violations,
        )

    def explain(self, key: str, directory: str | Path | None = None) -> str:
        from flossware_setup.config_control import effective_config, profile_for_directory

        target = Path(directory or Path.cwd()).expanduser().resolve()
        profile, _ = profile_for_directory(target)
        return effective_config(profile).explain(key)
