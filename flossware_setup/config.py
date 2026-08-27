"""Configuration model and project-level persistence.

Persists only non-secret policy and selection state. Credential values are
never written to disk by this module.

Selections use stable catalog IDs (agent id, capability id, budget policy id),
not positional indexes, so catalog order can change without invalidating state.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from flossware_setup.catalog import (
    AGENT_BY_ID,
    AGENTS,
    BUDGET_BY_ID,
    BUDGET_POLICIES,
    CAPABILITIES,
    CAPABILITY_BY_ID,
    PROVIDERS,
)
from flossware_setup.credentials import (
    ALLOWED_STATE_KEYS,
    credential_status,
    environment_names,
    filter_state_keys,
    scan_mapping_for_secrets,
)


@dataclass
class Config:
    """In-memory setup selections used by the TUI and artifact generation."""

    agents: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    budget_policy: str = "medium"
    budget_amount: float = 50.0
    repo_dir: str = "."
    # Turbo is the provider-neutral public default. Named profiles may override
    # policy, while the UI remains immediately useful with zero configuration.
    theme: str = "turbo"
    profile: str = "default"


def managed_root() -> Path:
    """Managed install/runtime root (non-project state lives here).

    Delegates to ``config_control.flossware_root`` so install and state roots stay unified.
    """
    from flossware_setup.config_control import flossware_root

    return flossware_root().resolve()



def active_project_path() -> Path:
    return managed_root() / "state" / "active-project"


def _sanitize_path_chars(value: str) -> str | None:
    """Rebuild *value* from an allowlist so path characters are explicit.

    Returns None if any character is outside the portable path alphabet.
    """
    if not value or chr(0) in value:
        return None
    allowed = frozenset(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        + "/\\._-~: "
    )
    out: list[str] = []
    for ch in value:
        if ch not in allowed:
            return None
        out.append(ch)
    return "".join(out)



def _existing_absolute_dir(raw: str | Path) -> Path | None:
    """Return *raw* as a resolved absolute directory, or None if unsafe/missing.

    Rejects relative paths, null bytes, disallowed characters, and non-directories.
    Used for operator-local active-project state (not network input).
    """
    if raw is None:
        return None
    if isinstance(raw, Path):
        try:
            text = os.fspath(raw)
        except (TypeError, ValueError):
            return None
    elif isinstance(raw, str):
        text = raw.strip()
    else:
        return None
    text = _sanitize_path_chars(text)
    if text is None:
        return None
    if not os.path.isabs(text):
        return None
    try:
        normalized = os.path.normpath(text)
    except (TypeError, ValueError, OSError):
        return None
    if not os.path.isabs(normalized):
        return None
    try:
        real = os.path.realpath(normalized)
    except OSError:
        return None
    if not os.path.isabs(real) or not os.path.isdir(real):
        return None
    # Path construction is safe: allowlist + isabs + isdir + realpath (local state only).
    return Path(real)  # NOSONAR



def set_active_project(repo_dir: str | Path) -> None:
    """Remember the last configured project path (no secrets)."""
    try:
        preliminary = Path(repo_dir).resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        return
    if not preliminary.is_dir():
        return
    resolved = _existing_absolute_dir(str(preliminary))
    if resolved is None:
        return
    path = active_project_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(resolved) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def get_active_project() -> Path | None:
    """Return the last configured project directory, if still present."""
    path = active_project_path()
    if not path.is_file():
        return None
    try:
        stored = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return _existing_absolute_dir(stored)


def resolve_review_project(explicit: str | Path | None = None) -> Path:
    """Project path for Review Current Configuration.

    Prefer explicit path, then active-project state, then cwd.
    """
    if explicit is not None:
        try:
            preliminary = Path(explicit).resolve(strict=True)
        except (OSError, RuntimeError, ValueError):
            return Path(".").resolve()
        validated = _existing_absolute_dir(str(preliminary))
        if validated is not None:
            return validated
        return Path(".").resolve()
    active = get_active_project()
    if active is not None:
        return active
    return Path(".").resolve()


def is_git_repository(path: str | Path) -> bool:
    """True when *path* is inside a Git working tree (including subdirs/worktrees).

    Walks parents for a ``.git`` directory or file (worktree gitfile).
    """
    try:
        root = Path(path).expanduser().resolve()
    except (OSError, RuntimeError, ValueError):
        return False
    current = root
    while True:
        git_entry = current / ".git"
        if git_entry.exists():
            return True
        if current.parent == current:
            break
        current = current.parent
    return False


def git_status_label(path: str | Path) -> str:
    """Human-readable Git status for review screens (never an error)."""
    return "Git: repository" if is_git_repository(path) else "Git: not a repository"


def project_identity(repo_dir: str | Path) -> str:
    """Stable, collision-resistant id for a directory under the central state root.

    Based on the normalized absolute path. Renamed/moved directories receive a new
    identity; callers may migrate state explicitly if needed.
    """
    try:
        normalized = os.path.normcase(str(Path(repo_dir).expanduser().resolve()))
    except (OSError, RuntimeError, ValueError):
        normalized = os.path.normcase(str(repo_dir))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest[:16]


STATE_JSON_NAME = "state.json"
AI_CONFIG_NAME = "ai_config.py"
PATH_TXT_NAME = "path.txt"


def central_project_dir(repo_dir: str | Path) -> Path:
    """Per-directory FlossWare state folder (never inside the user project)."""
    path = managed_root() / "projects" / project_identity(repo_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_state_path(repo_dir: str | Path) -> Path:
    """Path to centralized project state JSON (not written into the project tree)."""
    return central_project_dir(repo_dir) / STATE_JSON_NAME


def migrate_project_state(old_dir: str | Path, new_dir: str | Path) -> Path:
    """Copy central project state from *old_dir* identity to *new_dir* identity.

    Path-derived ids mean a rename/move creates a new empty identity. Call this
    explicitly after moving a project so prior configuration follows the new path.
    Existing destination state is not overwritten.
    """
    src = central_project_dir(old_dir)
    dest = central_project_dir(new_dir)
    if not (src / STATE_JSON_NAME).is_file():
        raise FileNotFoundError(f"no central state for {old_dir!s}")
    if (dest / STATE_JSON_NAME).is_file():
        return dest
    for name in (STATE_JSON_NAME, AI_CONFIG_NAME, PATH_TXT_NAME):
        item = src / name
        if item.is_file():
            shutil.copy2(item, dest / name)
    try:
        dest.joinpath("path.txt").write_text(
            str(Path(new_dir).expanduser().resolve()) + "\n", encoding="utf-8"
        )
    except OSError:
        pass
    return dest



def load_project_state(repo_dir: str | Path = ".") -> dict[str, Any]:
    """Load persisted project configuration if present.

    Only whitelist keys are returned. Secret-like keys/values are dropped so a
    compromised or hand-edited ``.flossware-ai.json`` cannot leak into the TUI.
    """
    path = project_state_path(repo_dir)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    cleaned = filter_state_keys(data)
    findings = scan_mapping_for_secrets(cleaned)
    if findings:
        # Drop any remaining secret-like string fields rather than failing open.
        for key in list(cleaned.keys()):
            val = cleaned[key]
            if isinstance(val, str) and key not in {"tool", "profile", "budget_policy", "theme", "repo_dir", "budget_policy_id"}:
                cleaned.pop(key, None)
    return cleaned


def resolve_budget(config: Config) -> tuple[str, float]:
    """Return (policy_label, monthly_amount) for the current selection."""
    policy = BUDGET_BY_ID.get(config.budget_policy) or BUDGET_BY_ID["medium"]
    _pid, label, amount, _desc = policy
    resolved = config.budget_amount if amount < 0 else amount
    return label, float(resolved)


def build_state_dict(config: Config) -> dict[str, Any]:
    """Build the serializable project state. Never includes secret values.

    Output keys are restricted to :data:`ALLOWED_STATE_KEYS`. Provider entries
    are presence booleans and env-var *names* only.
    """
    policy_label, budget = resolve_budget(config)
    providers = credential_status()
    env_vars = environment_names()
    agent_ids = [a for a in config.agents if a in AGENT_BY_ID]
    capability_ids = [c for c in config.capabilities if c in CAPABILITY_BY_ID]
    state = {
        "schema_version": 1,
        "tool": "FlossWare/coding-agent-setup",
        "profile": config.profile,
        "budget_policy_id": config.budget_policy,
        "budget_policy": policy_label,
        "monthly_budget": budget,
        "capabilities": capability_ids,
        "providers": providers,
        "provider_env_vars": env_vars,
        "credential_values_written": False,
        "agents": agent_ids,
        "theme": config.theme,
        "repo_dir": str(Path(config.repo_dir).resolve()),
    }
    # Defense in depth: refuse to emit anything outside the whitelist.
    state = filter_state_keys(state)
    findings = scan_mapping_for_secrets(state)
    if findings:
        raise ValueError(
            "refusing to persist project state with secret-like material: "
            + "; ".join(findings)
            + ". Use environment variables or an OS/agent credential store."
        )
    return state


def _format_agent_lines(agent_ids: set[str]) -> list[str]:
    lines = ["Configured agents:"]
    for agent in AGENTS:
        mark = "yes" if agent.id in agent_ids else "no"
        lines.append(f"  [{mark}] {agent.name} ({agent.id})")
    return lines


def review_lines(repo_dir: str | Path = ".") -> list[str]:
    """Human-readable review of persisted project state (no secret values)."""
    state = load_project_state(repo_dir)
    if not state:
        return [
            "No persisted FlossWare project configuration found.",
            f"Project: {Path(repo_dir).resolve()}",
            git_status_label(repo_dir),
            f"Looked for: {project_state_path(repo_dir)}",
            "Run Configure / Change Setup to generate configuration.",
            f"Supported integrations in catalog: {len(AGENTS)}",
        ]
    agent_ids = set(state.get("agents") or [])
    caps = state.get("capabilities") or []
    lines = [
        f"Project: {Path(repo_dir).resolve()}",
        git_status_label(repo_dir),
        f"Central state: {project_state_path(repo_dir)}",
        f"Profile: {state.get('profile', 'default')}",
        f"Budget policy: {state.get('budget_policy', '?')} "
        f"(id={state.get('budget_policy_id', '?')})",
        f"Monthly ceiling: ${state.get('monthly_budget', '?')}",
        f"Theme: {state.get('theme', 'turbo')}",
        "",
        *_format_agent_lines(agent_ids),
        "",
        "Capabilities:",
        *([f"  - {name}" for name in caps] if caps else ["  (none)"]),
        "",
        "Providers (presence only):",
    ]
    providers = state.get("providers") or {}
    for name, _env, _url in PROVIDERS:
        present = bool(providers.get(name))
        lines.append(f"  [{'SET' if present else '---'}] {name}")
    lines.extend(
        [
            "",
            f"credential_values_written: {state.get('credential_values_written', False)}",
            "All persisted state is secret-free (env names / presence only).",
        ]
    )
    return lines
