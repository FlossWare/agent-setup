from pathlib import Path

import pytest

from flossware_setup.state_root import (
    MigrationResult,
    canonical_root,
    migrate_legacy_state,
    migrate_legacy_state_detailed,
)


def test_default_root_is_canonical(monkeypatch, tmp_path):
    monkeypatch.delenv("FLOSSWARE_AI_HOME", raising=False)
    monkeypatch.delenv("FLOSSWARE_AI_ROOT", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert canonical_root() == (tmp_path / ".FlossWare" / "ai").resolve()


def test_environment_override_must_be_absolute(monkeypatch):
    monkeypatch.setenv("FLOSSWARE_AI_HOME", "relative/path")
    with pytest.raises(ValueError):
        canonical_root()


def test_environment_override_is_used(monkeypatch, tmp_path):
    target = tmp_path / "isolated-ai"
    monkeypatch.setenv("FLOSSWARE_AI_HOME", str(target))
    assert canonical_root() == target.resolve()


def test_legacy_migration_is_non_destructive_and_idempotent(tmp_path):
    legacy = tmp_path / "legacy-state" / "ai"
    current = tmp_path / "canonical-state" / "ai"
    (legacy / "profiles").mkdir(parents=True)
    (legacy / "profiles" / "personal.toml").write_text("personal\n", encoding="utf-8")
    (legacy / "active-profile").write_text("personal\n", encoding="utf-8")
    (legacy / "credentials").mkdir()
    (legacy / "credentials" / "secret.txt").write_text("SECRET\n", encoding="utf-8")

    first = migrate_legacy_state_detailed(source=legacy, destination=current)
    assert isinstance(first, MigrationResult)
    assert {"profiles/personal.toml", "active-profile"} <= set(first.migrated)
    assert not first.conflicts
    assert not (current / "credentials").exists()

    second = migrate_legacy_state_detailed(source=legacy, destination=current)
    assert not second.migrated
    assert {"profiles/personal.toml", "active-profile"} <= set(second.conflicts)
    assert (current / "active-profile").read_text(encoding="utf-8") == "personal\n"


def test_backward_compatible_wrapper_returns_only_new_migrations(tmp_path):
    legacy = tmp_path / "legacy" / "ai"
    current = tmp_path / "current" / "ai"
    (legacy / "profiles").mkdir(parents=True)
    (legacy / "profiles" / "personal.toml").write_text("personal\n", encoding="utf-8")
    migrated = migrate_legacy_state(source=legacy, destination=current)
    assert migrated == ["profiles/personal.toml"]
    assert migrate_legacy_state(source=legacy, destination=current) == []


def test_migration_skips_when_source_is_destination(tmp_path):
    root = tmp_path / "same" / "ai"
    (root / "profiles").mkdir(parents=True)
    (root / "profiles" / "x.toml").write_text('profile = "x"\n', encoding="utf-8")
    assert migrate_legacy_state(source=root, destination=root) == []


def test_migrate_legacy_install_entrypoint():
    from flossware_setup.config_control import migrate_legacy_install
    assert callable(migrate_legacy_install)


def test_merge_directories_with_unrelated_files(tmp_path):
    legacy = tmp_path / "legacy" / "ai"
    current = tmp_path / "current" / "ai"
    (legacy / "profiles").mkdir(parents=True)
    (legacy / "profiles" / "personal.toml").write_text("personal\n", encoding="utf-8")
    (current / "profiles").mkdir(parents=True)
    (current / "profiles" / "default.toml").write_text("default\n", encoding="utf-8")
    result = migrate_legacy_state_detailed(source=legacy, destination=current)
    assert result.migrated == ["profiles/personal.toml"]
    assert (current / "profiles" / "default.toml").exists()
    assert (current / "profiles" / "personal.toml").exists()


def test_preexisting_file_is_reported_as_conflict_even_if_content_matches(tmp_path):
    legacy = tmp_path / "legacy" / "ai"
    current = tmp_path / "current" / "ai"
    (legacy / "profiles").mkdir(parents=True)
    (legacy / "profiles" / "config.toml").write_text("legacy\n", encoding="utf-8")
    (current / "profiles").mkdir(parents=True)
    (current / "profiles" / "config.toml").write_text("legacy\n", encoding="utf-8")
    result = migrate_legacy_state_detailed(source=legacy, destination=current)
    assert "profiles/config.toml" in result.conflicts
    assert not result.migrated


def test_preexisting_different_file_is_conflict_and_preserved(tmp_path):
    legacy = tmp_path / "legacy" / "ai"
    current = tmp_path / "current" / "ai"
    (legacy / "profiles").mkdir(parents=True)
    (legacy / "profiles" / "config.toml").write_text("legacy\n", encoding="utf-8")
    (current / "profiles").mkdir(parents=True)
    (current / "profiles" / "config.toml").write_text("canonical\n", encoding="utf-8")
    result = migrate_legacy_state_detailed(source=legacy, destination=current)
    assert "profiles/config.toml" in result.conflicts
    assert (current / "profiles" / "config.toml").read_text(encoding="utf-8") == "canonical\n"


def test_mixed_tree_preserves_new_files_and_reports_conflicts(tmp_path):
    legacy = tmp_path / "legacy" / "ai"
    current = tmp_path / "current" / "ai"
    (legacy / "profiles").mkdir(parents=True)
    (legacy / "profiles" / "personal.toml").write_text("personal\n", encoding="utf-8")
    (legacy / "profiles" / "shared.toml").write_text("legacy\n", encoding="utf-8")
    (current / "profiles").mkdir(parents=True)
    (current / "profiles" / "default.toml").write_text("default\n", encoding="utf-8")
    (current / "profiles" / "shared.toml").write_text("canonical\n", encoding="utf-8")
    result = migrate_legacy_state_detailed(source=legacy, destination=current)
    assert "profiles/personal.toml" in result.migrated
    assert "profiles/shared.toml" in result.conflicts


def test_nested_directories_are_merged_recursively(tmp_path):
    legacy = tmp_path / "legacy" / "ai"
    current = tmp_path / "current" / "ai"
    (legacy / "config" / "nested" / "deep").mkdir(parents=True)
    (legacy / "config" / "nested" / "deep" / "settings.toml").write_text("legacy\n", encoding="utf-8")
    (current / "config" / "nested").mkdir(parents=True)
    (current / "config" / "nested" / "canonical.toml").write_text("canonical\n", encoding="utf-8")
    result = migrate_legacy_state_detailed(source=legacy, destination=current)
    assert "config/nested/deep/settings.toml" in result.migrated
    assert (current / "config" / "nested" / "canonical.toml").exists()


def test_type_conflicts_are_reported_and_not_overwritten(tmp_path):
    legacy = tmp_path / "legacy" / "ai"
    current = tmp_path / "current" / "ai"
    (legacy / "profiles").mkdir(parents=True)
    (legacy / "profiles" / "dev.toml").write_text("dev\n", encoding="utf-8")
    current.mkdir(parents=True)
    (current / "profiles").write_text("not-a-directory\n", encoding="utf-8")
    result = migrate_legacy_state_detailed(source=legacy, destination=current)
    assert "profiles" in result.conflicts
    assert (current / "profiles").read_text(encoding="utf-8") == "not-a-directory\n"


def test_credentials_excluded_from_migration(tmp_path):
    legacy = tmp_path / "legacy" / "ai"
    current = tmp_path / "current" / "ai"
    (legacy / "profiles").mkdir(parents=True)
    (legacy / "profiles" / "default.toml").write_text("profile\n", encoding="utf-8")
    (legacy / "credentials").mkdir(parents=True)
    (legacy / "credentials" / "api.txt").write_text("SECRET\n", encoding="utf-8")
    result = migrate_legacy_state_detailed(source=legacy, destination=current)
    assert "profiles/default.toml" in result.migrated
    assert not (current / "credentials").exists()
