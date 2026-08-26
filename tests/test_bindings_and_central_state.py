"""Git-optional central state and directory binding provenance (#47, #48)."""

from __future__ import annotations

import json
from pathlib import Path

from flossware_setup.artifacts import generate_artifacts
from flossware_setup.config import (
    Config,
    git_status_label,
    is_git_repository,
    load_project_state,
    project_identity,
    project_state_path,
)
from flossware_setup.config_control import (
    bind_directory,
    binding_provenance,
    bindings_grouped_by_profile,
    profile_for_directory,
    unbind_directory,
)


def test_non_git_directory_is_supported(tmp_path, monkeypatch):
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(tmp_path / "ai"))
    project = tmp_path / "plain"
    project.mkdir()
    assert not is_git_repository(project)
    assert git_status_label(project) == "Git: not a repository"
    state = generate_artifacts(
        Config(agents=["claude-code"], capabilities=[], repo_dir=str(project)),
        write_agent_files=False,
    )
    assert state["credential_values_written"] is False
    assert project_state_path(project).is_file()
    # No FlossWare metadata in the project tree
    assert not (project / ".flossware-ai.json").exists()
    assert not (project / ".flossware").exists()
    assert not list(project.glob(".*")) or all(
        p.name.startswith(".git") for p in project.iterdir() if p.name.startswith(".")
    )


def test_central_state_uses_stable_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(tmp_path / "ai"))
    project = tmp_path / "work"
    project.mkdir()
    pid = project_identity(project)
    generate_artifacts(Config(repo_dir=str(project)), write_agent_files=False)
    path = project_state_path(project)
    assert pid in str(path)
    assert load_project_state(project)["repo_dir"] == str(project.resolve())


def test_longest_path_binding_wins(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "state"
    )
    monkeypatch.setattr(
        "flossware_setup.config_control.available_profiles",
        lambda: ("default", "personal", "work"),
    )
    parent = tmp_path / "code"
    child = parent / "app"
    child.mkdir(parents=True)
    bind_directory(parent, "personal")
    bind_directory(child, "default")
    profile, source = profile_for_directory(child)
    assert profile == "default"
    assert source is not None
    assert str(child.resolve()).lower() in source.lower() or source.endswith("app")
    prov = binding_provenance(child)
    assert prov["source_kind"] == "directory-binding"
    assert prov["effective_profile"] == "default"
    assert len(prov["parent_bindings"]) == 1
    assert prov["parent_bindings"][0][1] == "personal"
    # Parent directory itself still uses parent binding
    assert profile_for_directory(parent)[0] == "personal"


def test_bindings_grouped_and_unbind(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "state"
    )
    monkeypatch.setattr(
        "flossware_setup.config_control.available_profiles",
        lambda: ("default", "personal"),
    )
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir(); b.mkdir()
    bind_directory(a, "personal")
    bind_directory(b, "default")
    grouped = bindings_grouped_by_profile()
    assert "personal" in grouped and "default" in grouped
    unbind_directory(a)
    assert profile_for_directory(a)[1] is None
    assert profile_for_directory(a)[0] == "personal"  # fallback name


def test_git_repo_status_when_present(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    assert is_git_repository(repo)
    assert git_status_label(repo) == "Git: repository"
