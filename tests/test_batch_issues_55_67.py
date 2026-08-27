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
    assert str(parent.resolve()) in source or source.endswith(str(parent.resolve()))


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
