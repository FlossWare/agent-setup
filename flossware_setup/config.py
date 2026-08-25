"""Configuration model and project-level persistence.

Persists only non-secret policy and selection state. Credential values are
never written to disk by this module.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from flossware_setup.catalog import AGENTS, BUDGET_POLICIES, CAPABILITIES, PROVIDERS
from flossware_setup.credentials import credential_status, environment_names


@dataclass
class Config:
    """In-memory setup selections used by the TUI and artifact generation."""

    agents: list[int] = field(default_factory=list)
    capabilities: list[int] = field(default_factory=list)
    budget_index: int = 2
    budget_amount: float = 50.0
    repo_dir: str = "."
    theme: str = "dark"
    profile: str = "default"


def project_state_path(repo_dir: str | Path) -> Path:
    return Path(repo_dir).resolve() / ".flossware-ai.json"


def load_project_state(repo_dir: str | Path = ".") -> dict[str, Any]:
    """Load persisted project configuration if present."""
    path = project_state_path(repo_dir)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def resolve_budget(config: Config) -> tuple[str, float]:
    """Return (policy_label, monthly_amount) for the current selection."""
    policy = BUDGET_POLICIES[config.budget_index]
    amount = config.budget_amount if policy[1] < 0 else policy[1]
    return policy[0], float(amount)


def build_state_dict(config: Config) -> dict[str, Any]:
    """Build the serializable project state. Never includes secret values."""
    policy_label, budget = resolve_budget(config)
    providers = credential_status()
    env_vars = environment_names()
    capability_names = [CAPABILITIES[i][0] for i in config.capabilities]
    agent_ids = [AGENTS[i].id for i in config.agents]
    return {
        "tool": "FlossWare/coding-agent-setup",
        "profile": config.profile,
        "budget_policy": policy_label,
        "monthly_budget": budget,
        "capabilities": capability_names,
        "providers": providers,
        "provider_env_vars": env_vars,
        "credential_values_written": False,
        "agents": agent_ids,
        "theme": config.theme,
    }


def review_lines(repo_dir: str | Path = ".") -> list[str]:
    """Human-readable summary lines for the Review Current Configuration screen."""
    state = load_project_state(repo_dir)
    if not state:
        return [
            "No persisted project configuration found.",
            "",
            "Use Configure / Change Setup to create one.",
            "Credential values are never stored in generated files.",
        ]

    agent_ids = set(state.get("agents") or [])
    lines = [
        "Current configuration",
        "",
        f"Profile: {state.get('profile', 'default')}",
        f"Supported integrations in catalog: {len(AGENTS)}",
        f"Configured in this project: {len(agent_ids)}",
        "",
        "Configured agents:",
    ]
    for agent in AGENTS:
        if agent.id in agent_ids:
            lines.append(f"  ✓ {agent.name}")
    if not agent_ids:
        lines.append("  (none)")

    lines.extend(["", "Capabilities:"])
    for name in state.get("capabilities") or []:
        lines.append(f"  ✓ {name}")
    if not state.get("capabilities"):
        lines.append("  (none)")

    lines.extend(["", "Providers:"])
    providers = state.get("providers") or {}
    for name, _env, _url in PROVIDERS:
        present = bool(providers.get(name))
        mark = "✓" if present else "·"
        status = "configured" if present else "not configured"
        lines.append(f"  {mark} {name}: {status}")

    policy = state.get("budget_policy", "unknown")
    monthly = state.get("monthly_budget", 0)
    try:
        monthly_text = f"${float(monthly):g}"
    except (TypeError, ValueError):
        monthly_text = str(monthly)
    lines.extend(
        [
            "",
            f"Budget: {policy}  {monthly_text}",
            "Credentials: values never displayed or stored",
            "Security: ✓ secret-free generated configuration",
        ]
    )
    return lines
