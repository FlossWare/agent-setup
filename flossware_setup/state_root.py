"""Canonical FlossWare AI persistent-state root and safe legacy migration."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

ENV_VAR = "FLOSSWARE_AI_HOME"
DEFAULT_ROOT_NAME = ".FlossWare/ai"
LEGACY_ROOT = ".flossware/ai"

# Setup-managed, non-secret state paths. Credential material is deliberately
# excluded from automatic migration.
SAFE_LEGACY_PATHS = (
    "config", "profiles", "providers", "accounts", "models", "crush", "mcp",
    "state", "system.toml", "user.toml", "active-profile", "profile",
    "profile-bindings.toml", "menu-order.json", "theme",
)


def canonical_root() -> Path:
    """Return the canonical persistent AI state root."""
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


class MigrationResult:
    """Detailed result of a non-destructive legacy-state migration."""

    def __init__(self) -> None:
        self.migrated: list[str] = []
        self.conflicts: dict[str, tuple[str, Path, Path]] = {}

    def __bool__(self) -> bool:
        return bool(self.migrated or self.conflicts)

    def to_migrated_list(self) -> list[str]:
        """Return only newly migrated paths for backward compatibility."""
        return self.migrated


def migrate_legacy_state(*, source: Path | None = None, destination: Path | None = None) -> list[str]:
    """Safely copy supported legacy state into the canonical root.

    Existing destination entries are never overwritten. Existing entries are
    reported as conflicts because filesystem state alone cannot prove that an
    entry was created by an earlier migration. Credential stores are excluded.
    """
    return migrate_legacy_state_detailed(source=source, destination=destination).to_migrated_list()


def migrate_legacy_state_detailed(*, source: Path | None = None, destination: Path | None = None) -> MigrationResult:
    """Migrate legacy state recursively and report every pre-existing entry.

    The detailed API intentionally has no ``already_migrated`` category. A
    previous migration is not provable without explicit provenance, so an
    existing canonical entry is conservatively reported as a conflict and
    preserved unchanged.
    """
    src = (source or legacy_root()).expanduser().resolve()
    dest = (destination or canonical_root()).expanduser().resolve()
    result = MigrationResult()
    if not src.is_dir():
        return result
    try:
        if src == dest or src.samefile(dest):
            return result
    except OSError:
        if src == dest:
            return result

    dest.mkdir(parents=True, exist_ok=True)
    for relative in SAFE_LEGACY_PATHS:
        source_path = src / relative
        target_path = dest / relative
        if not source_path.exists():
            continue
        if _has_type_conflict(source_path, target_path):
            _record_conflict(result, relative, "type mismatch", source_path, target_path)
        elif source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            _migrate_directory_contents(source_path, target_path, result, relative)
        elif not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            result.migrated.append(relative)
        else:
            _record_conflict(result, relative, "destination already exists", source_path, target_path)
    return result


def _record_conflict(result: MigrationResult, relative: str, reason: str, source: Path, target: Path) -> None:
    result.conflicts[relative] = (reason, source, target)


def _has_type_conflict(source: Path, target: Path) -> bool:
    if not target.exists():
        return False
    return source.is_dir() != target.is_dir()


def _type_name(path: Path) -> str:
    return "directory" if path.is_dir() else "file"


def _migrate_directory_contents(source_dir: Path, dest_dir: Path, result: MigrationResult, prefix: str) -> None:
    """Recursively merge source_dir without overwriting canonical state."""
    for item in source_dir.iterdir():
        relative_path = f"{prefix}/{item.name}"
        dest_item = dest_dir / item.name
        if _has_type_conflict(item, dest_item):
            reason = f"type mismatch: {_type_name(item)} vs {_type_name(dest_item)}"
            _record_conflict(result, relative_path, reason, item, dest_item)
        elif item.is_dir():
            dest_item.mkdir(parents=True, exist_ok=True)
            _migrate_directory_contents(item, dest_item, result, relative_path)
        elif not dest_item.exists():
            dest_item.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest_item)
            result.migrated.append(relative_path)
        else:
            _record_conflict(result, relative_path, "destination already exists", item, dest_item)
