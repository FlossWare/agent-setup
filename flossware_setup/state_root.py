"""Canonical FlossWare AI persistent-state root and safe legacy migration."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

ENV_VAR = "FLOSSWARE_AI_HOME"
DEFAULT_ROOT_NAME = ".FlossWare/ai"
LEGACY_ROOT = ".flossware/ai"

# These are setup-managed, non-secret state paths. Credential material is
# intentionally excluded from automatic migration.
SAFE_LEGACY_PATHS = (
    "config",
    "profiles",
    "providers",
    "accounts",
    "models",
    "crush",
    "mcp",
    "state",
    "system.toml",
    "user.toml",
    "active-profile",
    "profile",
    "profile-bindings.toml",
    "menu-order.json",
    "theme",
)


def canonical_root() -> Path:
    """Return the canonical persistent AI state root.

    ``FLOSSWARE_AI_HOME`` is an explicit test/CI/container override. The
    default is intentionally ``~/.FlossWare/ai``.
    """
    raw = os.environ.get(ENV_VAR)
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            raise ValueError(f"{ENV_VAR} must be an absolute path")
        return candidate.resolve()
    return (Path.home() / DEFAULT_ROOT_NAME).resolve()


def legacy_root() -> Path:
    """Return the previous default state root."""
    return (Path.home() / LEGACY_ROOT).resolve()


def migrate_legacy_state(*, source: Path | None = None, destination: Path | None = None) -> list[str]:
    """Safely copy supported legacy state into the canonical root.

    Existing destination entries are never overwritten. Only known
    configuration/state paths are copied; credential stores are deliberately
    excluded. The operation is therefore idempotent and non-destructive.
    """
    src = (source or legacy_root()).expanduser().resolve()
    dest = (destination or canonical_root()).expanduser().resolve()
    if not src.is_dir():
        return []
    try:
        if src == dest or src.samefile(dest):
            return []
    except OSError:
        if src == dest:
            return []

    dest.mkdir(parents=True, exist_ok=True)
    migrated: list[str] = []
    for relative in SAFE_LEGACY_PATHS:
        source_path = src / relative
        target_path = dest / relative
        if not source_path.exists() or target_path.exists():
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.is_dir():
            shutil.copytree(source_path, target_path)
        else:
            shutil.copy2(source_path, target_path)
        migrated.append(relative)
    return migrated
