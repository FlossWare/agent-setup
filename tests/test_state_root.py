from pathlib import Path

import pytest

from flossware_setup.state_root import canonical_root, migrate_legacy_state


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
    legacy = tmp_path / ".flossware" / "ai"
    current = tmp_path / ".FlossWare" / "ai"
    (legacy / "profiles").mkdir(parents=True)
    (legacy / "profiles" / "personal.toml").write_text('profile = "personal"\n', encoding="utf-8")
    (legacy / "active-profile").write_text("personal\n", encoding="utf-8")
    (legacy / "credentials").mkdir()
    (legacy / "credentials" / "secret.txt").write_text("SECRET\n", encoding="utf-8")

    migrated = migrate_legacy_state(source=legacy, destination=current)
    assert "profiles" in migrated
    assert "active-profile" in migrated
    assert (current / "profiles" / "personal.toml").exists()
    assert not (current / "credentials").exists()
    assert (legacy / "credentials" / "secret.txt").read_text(encoding="utf-8") == "SECRET\n"

    (current / "active-profile").write_text("default\n", encoding="utf-8")
    assert migrate_legacy_state(source=legacy, destination=current) == []
    assert (current / "active-profile").read_text(encoding="utf-8") == "default\n"
