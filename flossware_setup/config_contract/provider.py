"""Shared configuration provider interface for coding-agent-setup and Loom.

This module is intentionally small and dependency-light so Loom (or other
orchestrators) can implement the same contract without importing the TUI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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


@runtime_checkable
class ConfigurationProvider(Protocol):
    """Stable interface both coding-agent-setup and Loom can implement."""

    def resolve(self, directory: str | Path | None = None) -> EffectiveConfiguration:
        """Merge layers for *directory* and return effective configuration."""

    def explain(self, key: str, directory: str | Path | None = None) -> str:
        """Human-readable provenance for a single key."""


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
        values = resolver.resolve()
        provenance = {
            key: resolver.provenance(key)
            for key in values
        }
        violations: list[str] = []
        try:
            from flossware_setup.config_control import validate_effective_config

            validate_effective_config(profile)
        except ValueError as exc:
            violations.append(str(exc))
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
            policy_violations=tuple(violations),
        )

    def explain(self, key: str, directory: str | Path | None = None) -> str:
        from flossware_setup.config_control import effective_config, profile_for_directory

        target = Path(directory or Path.cwd()).expanduser().resolve()
        profile, _ = profile_for_directory(target)
        return effective_config(profile).explain(key)
