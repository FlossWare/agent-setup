"""Regression coverage for issues #55–#67."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from flossware_setup.cli import main as cli_main
from flossware_setup.cli import _agent_env
from flossware_setup.config import is_git_repository, managed_root
from flossware_setup.config_control import (
    BUILTIN_PROFILES,
    ORGANIZATION_PROFILES,
    bind_directory,
    effective_config,
    flossware_root,
    profile_for_directory,
    state_dir,
)


@pytest.fixture
def ai_root(tmp_path, monkeypatch):
    root = tmp_path / "ai"
    root.mkdir(parents=True)
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(root))
    monkeypatch.delenv("FLOSSWARE_INSTALL_ROOT", raising=False)
    return root


def test_root_env_isolation(ai_root) -> None:
    assert flossware_root() == ai_root.resolve()
    assert state_dir() == ai_root.resolve()
    assert managed_root() == ai_root.resolve()
    (state_dir() / "theme").write_text("turbo\n", encoding="utf-8")
    assert (ai_root / "theme").is_file()


def test_install_root_alias(tmp_path, monkeypatch) -> None:
    root = tmp_path / "install"
    monkeypatch.delenv("FLOSSWARE_AI_ROOT", raising=False)
    monkeypatch.setenv("FLOSSWARE_INSTALL_ROOT", str(root))
    assert flossware_root() == root.resolve()


def test_git_detection_walks_parents(tmp_path) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    sub = repo / "a" / "b"
    sub.mkdir(parents=True)
    assert is_git_repository(sub) and is_git_repository(repo)
    plain = tmp_path / "plain" / "x"
    plain.mkdir(parents=True)
    assert not is_git_repository(plain)


def test_bindings_authoritative(ai_root, tmp_path) -> None:
    parent = tmp_path / "parent"
    child = parent / "child"
    child.mkdir(parents=True)
    bind_directory(parent, "default")
    profile, source = profile_for_directory(child)
    assert profile == "default" and source is not None
    assert os.path.normcase(str(parent.resolve())) in os.path.normcase(source)


def test_builtin_profiles_are_neutral() -> None:
    assert BUILTIN_PROFILES == ("default",)
    assert ORGANIZATION_PROFILES == ()
    assert not Path("flossware_setup/profiles/personal.toml").exists()


def test_effective_config_layers(ai_root, monkeypatch) -> None:
    monkeypatch.setenv("FLOSSWARE_BUDGET_MONTHLY", "42")
    monkeypatch.setenv("FLOSSWARE_PROVIDER", "anthropic")
    resolver = effective_config("default")
    values = resolver.resolve()
    assert values.get("provider") == "anthropic"
    assert float(values.get("budget.monthly", 0)) == 42.0
    assert any(layer == "environment" for layer, _ in resolver.provenance("budget.monthly"))


def test_cli_tui_forwards_theme_args() -> None:
    import inspect
    from flossware_setup import cli as cli_mod
    src = inspect.getsource(cli_mod.main)
    assert "tui_args" in src and "REMAINDER" in src


def test_cli_config_show_uses_directory(ai_root, tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    assert cli_main(["config", "show"]) == 0
    assert "profile=" in capsys.readouterr().out


def test_layer_precedence_matrix(ai_root, monkeypatch) -> None:
    (ai_root / "system.toml").write_text('provider = "system-provider"\n', encoding="utf-8")
    (ai_root / "user.toml").write_text('provider = "user-provider"\n', encoding="utf-8")
    monkeypatch.delenv("FLOSSWARE_PROVIDER", raising=False)
    monkeypatch.delenv("FLOSSWARE_BUDGET_MONTHLY", raising=False)
    monkeypatch.setenv("FLOSSWARE_PROVIDER", "env-provider")
    values = effective_config("default").resolve()
    assert values.get("provider") == "env-provider"
    monkeypatch.setenv("FLOSSWARE_BUDGET_MONTHLY", "99")
    values = effective_config("default").resolve()
    assert float(values["budget.monthly"]) == 99.0
    layers = [layer for layer, _ in effective_config("default").provenance("budget.monthly")]
    assert "environment" in layers


def test_config_cli_and_run_share_directory_profile(ai_root, tmp_path, monkeypatch, capsys) -> None:
    parent = tmp_path / "workspace"
    child = parent / "nested"
    child.mkdir(parents=True)
    assert not (parent / ".git").exists()
    bind_directory(parent, "default")
    monkeypatch.chdir(child)
    profile, source = profile_for_directory()
    assert profile == "default" and source is not None
    assert cli_main(["config", "show"]) == 0
    assert "profile=default" in capsys.readouterr().out
    assert cli_main(["config", "validate"]) == 0
    env, agent_profile = _agent_env(["claude"])
    assert agent_profile == profile
    assert env["FLOSSWARE_PROFILE"] == profile
    assert env.get("FLOSSWARE_PROFILE_SOURCE")


def test_directory_is_profile_selection_not_merge_layer(ai_root, tmp_path) -> None:
    work = tmp_path / "proj"
    work.mkdir()
    bind_directory(work, "default")
    resolver = effective_config(profile_for_directory(work)[0])
    for key in resolver.resolve():
        layers = [layer for layer, _ in resolver.provenance(key)]
        assert "directory" not in layers
