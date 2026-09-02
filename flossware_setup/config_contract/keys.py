"""Versioned registry of keys exposed on EffectiveConfiguration.values.

This is the single source of truth for the wire ``values`` surface. Unknown
keys are excluded from the wire form (not preserved). Expanding the set is an
explicit, reviewed change governed by the rules in
``docs/configuration-contract.md``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValueKeySpec:
    """One allowed configuration key on the shared wire contract."""

    key: str
    domain: str
    value_type: str  # "string" | "number" | "boolean"
    introduced_in: int
    description: str
    allows_nested: bool = False


# --- flossware.config.v1 (schema_version = 1) ---------------------------------
# Domains: provider, budget, optimization, policy
# Nested maps are forbidden on every v1 key (allows_nested=False).

V1_VALUE_KEYS: tuple[ValueKeySpec, ...] = (
    ValueKeySpec(
        key="provider",
        domain="provider",
        value_type="string",
        introduced_in=1,
        description="Selected or default model provider id (never a secret).",
    ),
    ValueKeySpec(
        key="budget.monthly",
        domain="budget",
        value_type="number",
        introduced_in=1,
        description="Effective monthly budget ceiling in USD.",
    ),
    ValueKeySpec(
        key="optimization.population",
        domain="optimization",
        value_type="number",
        introduced_in=1,
        description="Optimizer population size when applicable.",
    ),
    ValueKeySpec(
        key="optimization.strategy",
        domain="optimization",
        value_type="string",
        introduced_in=1,
        description="Optimizer strategy identifier (e.g. hybrid).",
    ),
    ValueKeySpec(
        key="policy.allow_personal_accounts",
        domain="policy",
        value_type="boolean",
        introduced_in=1,
        description="Whether personal provider accounts are permitted.",
    ),
    ValueKeySpec(
        key="policy.allow_unknown_providers",
        domain="policy",
        value_type="boolean",
        introduced_in=1,
        description="Whether unlisted providers may be used.",
    ),
    ValueKeySpec(
        key="policy.allow_provider_fallback",
        domain="policy",
        value_type="boolean",
        introduced_in=1,
        description="Whether falling back across providers is permitted.",
    ),
    ValueKeySpec(
        key="policy.hard_budget",
        domain="policy",
        value_type="boolean",
        introduced_in=1,
        description="Whether the budget ceiling is a hard limit.",
    ),
)

VALUE_KEY_SPECS: tuple[ValueKeySpec, ...] = V1_VALUE_KEYS
SAFE_VALUE_KEYS: frozenset[str] = frozenset(spec.key for spec in VALUE_KEY_SPECS)
KEY_SPEC_BY_NAME: dict[str, ValueKeySpec] = {spec.key: spec for spec in VALUE_KEY_SPECS}

_OWNER_SETUP_PROFILES = "agent-setup profiles + shared contract"
_OWNER_CONTRACT_POLICY = "config_contract (shared) — enforced after merge"
_OWNER_SETUP_FUTURE = "agent-setup (future v1 additive or v2)"
_OWNER_LOOM_FUTURE = "Loom orchestration (future; must not own secrets)"
_OWNER_SHARED_FUTURE = "shared / Loom (future)"

DOMAIN_OWNERS: dict[str, str] = {
    "provider": _OWNER_SETUP_PROFILES,
    "budget": _OWNER_SETUP_PROFILES,
    "optimization": _OWNER_SETUP_PROFILES,
    "policy": _OWNER_CONTRACT_POLICY,
    "agent": _OWNER_SETUP_FUTURE,
    "routing": _OWNER_LOOM_FUTURE,
    "context": _OWNER_SHARED_FUTURE,
}


def keys_for_schema_version(version: int) -> frozenset[str]:
    """Keys introduced at or before *version*."""
    return frozenset(s.key for s in VALUE_KEY_SPECS if s.introduced_in <= version)


def is_supported_key(key: str, schema_version: int = 1) -> bool:
    spec = KEY_SPEC_BY_NAME.get(key)
    return spec is not None and spec.introduced_in <= schema_version
