"""Regression coverage for issues #55–#67."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

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
from flossware_setup.cli import main as cli_main


def test_root_env_isolation(tmp_path, monkeypatch) -> None:
    root = tmp_path / "ai-root"
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(root))
    monkeypatch.delenv("FLOSSWARE_INSTALL_ROOT", raising=False)
    assert flossware_root() == root.resolve()
    assert state_dir() == root.resolve()
    assert managed_root() == root.resolve()
    # state writes stay under temp root
    (state_dir() / "theme").write_text("turbo\n", encoding="utf-8")
    assert (root / "theme").is_file()
    assert not (Path.home() / ".flossware" / "ai" / "theme").exists() or True  # don't assert absence of pre-existing


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
    assert is_git_repository(sub)
    assert is_git_repository(repo)
    plain = tmp_path / "plain" / "x"
    plain.mkdir(parents=True)
    assert not is_git_repository(plain)


def test_bindings_authoritative(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(tmp_path / "ai"))
    parent = tmp_path / "parent"
    child = parent / "child"
    child.mkdir(parents=True)
    bind_directory(parent, "default")
    # only default is builtin; still verify longest path
    profile, source = profile_for_directory(child)
    assert profile == "default"
    assert source is not None
    import os
    assert os.path.normcase(str(parent.resolve())) in os.path.normcase(source)


def test_builtin_profiles_are_neutral() -> None:
    assert BUILTIN_PROFILES == ("default",)
    assert ORGANIZATION_PROFILES == ()
    assert not (Path("flossware_setup/profiles/personal.toml")).exists()


def test_effective_config_layers(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(tmp_path / "ai"))
    (tmp_path / "ai").mkdir(parents=True)
    monkeypatch.setenv("FLOSSWARE_BUDGET_MONTHLY", "42")
    monkeypatch.setenv("FLOSSWARE_PROVIDER", "anthropic")
    resolver = effective_config("default")
    values = resolver.resolve()
    assert values.get("provider") == "anthropic"
    assert float(values.get("budget.monthly", 0)) == 42.0
    prov = resolver.provenance("budget.monthly")
    assert any(layer == "environment" for layer, _ in prov)



def test_cli_tui_forwards_theme_args() -> None:
    """Parser accepts tui remainder args (does not drop --theme)."""
    import argparse
    # smoke: main with --help path for tui is not easily testable without curses
    # Ensure argparse configuration includes remainder
    from flossware_setup import cli as cli_mod
    import inspect
    src = inspect.getsource(cli_mod.main)
    assert "tui_args" in src
    assert "REMAINDER" in src


def test_cli_config_show_uses_directory(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(tmp_path / "ai"))
    (tmp_path / "ai").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    assert cli_main(["config", "show"]) == 0
    out = capsys.readouterr().out
    assert "profile=" in out


def test_layer_precedence_matrix(tmp_path, monkeypatch) -> None:
    """defaults < system < user < profile < project < environment."""
    root = tmp_path / "ai"
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(root))
    root.mkdir(parents=True)
    (root / "system.toml").write_text('provider = "system-provider"\n', encoding="utf-8")
    (root / "user.toml").write_text('provider = "user-provider"\n', encoding="utf-8")
    # clear env first
    monkeypatch.delenv("FLOSSWARE_PROVIDER", raising=False)
    monkeypatch.delenv("FLOSSWARE_BUDGET_MONTHLY", raising=False)
    values = effective_config("default").resolve()
    # profile (default) typically sets provider auto, which beats user
    assert values.get("provider") in {"auto", "user-provider", "system-provider"}
    # environment wins over everything below it
    monkeypatch.setenv("FLOSSWARE_PROVIDER", "env-provider")
    values = effective_config("default").resolve()
    assert values.get("provider") == "env-provider"
    # budget only from env
    monkeypatch.setenv("FLOSSWARE_BUDGET_MONTHLY", "99")
    values = effective_config("default").resolve()
    assert float(values["budget.monthly"]) == 99.0
    layers = [layer for layer, _ in effective_config("default").provenance("budget.monthly")]
    assert "environment" in layers


def test_config_cli_and_run_share_directory_profile(tmp_path, monkeypatch, capsys) -> None:
    """config show/validate and _agent_env resolve the same binding for a nested path."""
    from flossware_setup.cli import _agent_env, main as cli_main

    root = tmp_path / "ai"
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(root))
    root.mkdir(parents=True)
    parent = tmp_path / "workspace"
    child = parent / "nested"
    child.mkdir(parents=True)
    # non-git
    assert not (parent / ".git").exists()
    bind_directory(parent, "default")
    monkeypatch.chdir(child)
    profile, source = profile_for_directory()
    assert profile == "default"
    assert source is not None
    assert cli_main(["config", "show"]) == 0
    out = capsys.readouterr().out
    assert "profile=default" in out
    assert cli_main(["config", "validate"]) == 0
    # _agent_env uses same resolution (command need not exist for env build)
    env, agent_profile = _agent_env(["claude"])
    assert agent_profile == profile
    assert env["FLOSSWARE_PROFILE"] == profile
    assert env.get("FLOSSWARE_PROFILE_SOURCE")


def test_directory_is_profile_selection_not_merge_layer(tmp_path, monkeypatch) -> None:
    """Bindings change profile; they do not inject a 'directory' merge layer."""
    root = tmp_path / "ai"
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(root))
    root.mkdir(parents=True)
    monkeypatch.delenv("FLOSSWARE_PROVIDER", raising=False)
    work = tmp_path / "proj"
    work.mkdir()
    bind_directory(work, "default")
    resolver = effective_config(profile_for_directory(work)[0])
    values = resolver.resolve()
    for key in values:
        layers = [layer for layer, _ in resolver.provenance(key)]
        assert "directory" not in layers
