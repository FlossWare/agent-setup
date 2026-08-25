"""Unit tests for the modular flossware_setup package."""

from __future__ import annotations

import json

import pytest

from flossware_setup.artifacts import generate_artifacts, pip_packages
from flossware_setup.catalog import AGENTS, CAPABILITIES, CAPABILITY_REFS, PROVIDERS
from flossware_setup.config import (
    Config,
    build_state_dict,
    load_project_state,
    review_lines,
)
from flossware_setup.credentials import credential_status, environment_names


def test_thirteen_agent_adapters():
    assert len(AGENTS) == 13
    ids = [a.id for a in AGENTS]
    assert "claude-code" in ids
    assert "crush" in ids
    assert "kiro" in ids
    assert len(set(ids)) == 13


def test_capability_refs_cover_catalog():
    for name, _desc, _default in CAPABILITIES:
        assert name in CAPABILITY_REFS
        assert len(CAPABILITY_REFS[name]) == 40


def test_credential_status_is_boolean_only(monkeypatch):
    monkeypatch.setenv("COHERE_API_KEY", "super-secret-value")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    status = credential_status()
    assert status["Cohere"] is True
    assert status["OpenRouter"] is False
    assert "super-secret-value" not in str(status)


def test_environment_names_match_providers():
    names = environment_names()
    assert names == {name: env for name, env, _ in PROVIDERS}


def test_pip_packages_pinned():
    packages = pip_packages([0, 1])
    assert len(packages) == 2
    assert packages[0].startswith("git+https://github.com/FlossWare/model-router-ai.git@")
    assert CAPABILITY_REFS["model-router-ai"] in packages[0]


def test_generate_artifacts_writes_state_without_secrets(tmp_path, monkeypatch):
    repo = tmp_path / "project"
    repo.mkdir()
    (repo / ".git").mkdir()
    secret = "sk-live-should-never-appear"
    monkeypatch.setenv("GROQ_API_KEY", secret)

    cfg = Config(
        agents=[0, 3],
        capabilities=[0, 1, 2],
        budget_index=2,
        budget_amount=50.0,
        repo_dir=str(repo),
        profile="default",
    )
    state = generate_artifacts(cfg)

    assert state["credential_values_written"] is False
    assert state["profile"] == "default"
    assert "claude-code" in state["agents"]
    assert "crush" in state["agents"]
    assert secret not in json.dumps(state)

    marker = repo / ".flossware-ai.json"
    assert marker.is_file()
    body = marker.read_text(encoding="utf-8")
    assert secret not in body

    ai_config = (repo / "ai_config.py").read_text(encoding="utf-8")
    assert secret not in ai_config
    assert "MONTHLY_BUDGET" in ai_config

    assert (repo / "CLAUDE.md").is_file()
    assert (repo / "AGENTS.md").is_file()
    assert secret not in (repo / "CLAUDE.md").read_text(encoding="utf-8")


def test_generate_artifacts_does_not_overwrite_existing(tmp_path):
    repo = tmp_path / "project"
    repo.mkdir()
    (repo / ".git").mkdir()
    existing = repo / "CLAUDE.md"
    existing.write_text("user owned content\n", encoding="utf-8")

    cfg = Config(agents=[0], capabilities=[0], repo_dir=str(repo))
    generate_artifacts(cfg)
    assert existing.read_text(encoding="utf-8") == "user owned content\n"


def test_generate_artifacts_requires_git_repo(tmp_path):
    cfg = Config(agents=[0], capabilities=[0], repo_dir=str(tmp_path))
    with pytest.raises(ValueError, match="Not a git repository"):
        generate_artifacts(cfg)


def test_review_lines_empty_and_populated(tmp_path):
    empty = review_lines(tmp_path)
    assert any("No persisted" in line for line in empty)

    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / ".git").mkdir()
    cfg = Config(agents=[0], capabilities=[0], repo_dir=str(repo), profile="default")
    generate_artifacts(cfg)
    lines = review_lines(repo)
    joined = "\n".join(lines)
    assert "Claude Code" in joined
    assert "model-router-ai" in joined
    assert "secret-free" in joined


def test_build_state_dict_never_embeds_secrets(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "should-not-leak")
    cfg = Config(agents=[1], capabilities=[0], profile="default")
    state = build_state_dict(cfg)
    assert state["providers"]["Gemini"] is True
    assert "should-not-leak" not in json.dumps(state)
    assert state["credential_values_written"] is False


def test_default_profile_is_neutral():
    cfg = Config()
    assert cfg.profile == "default"
    state = build_state_dict(cfg)
    assert state["profile"] == "default"
    assert "redhat" not in json.dumps(state).lower()
    assert "personal" not in state["profile"]


def test_load_project_state_missing(tmp_path):
    assert load_project_state(tmp_path) == {}


def _aider_agent_index() -> int:
    return next(i for i, a in enumerate(AGENTS) if a.id == "aider")


def test_aider_conf_created_when_missing(tmp_path):
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / ".git").mkdir()
    cfg = Config(agents=[_aider_agent_index()], capabilities=[0], repo_dir=str(repo))
    generate_artifacts(cfg)
    conf = (repo / ".aider.conf.yml").read_text(encoding="utf-8")
    assert "read: CONVENTIONS.md" in conf
    assert (repo / "CONVENTIONS.md").is_file()


def test_aider_conf_appends_read_when_missing_key(tmp_path):
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / ".git").mkdir()
    existing = "# user settings\nauto-commits: false\nmodel: gpt-4o\n"
    (repo / ".aider.conf.yml").write_text(existing, encoding="utf-8")
    cfg = Config(agents=[_aider_agent_index()], capabilities=[0], repo_dir=str(repo))
    generate_artifacts(cfg)
    conf = (repo / ".aider.conf.yml").read_text(encoding="utf-8")
    assert "auto-commits: false" in conf
    assert "model: gpt-4o" in conf
    assert conf.count("read: CONVENTIONS.md") == 1


def test_aider_conf_untouched_when_read_key_exists(tmp_path):
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / ".git").mkdir()
    original = "read: MY_RULES.md\nother: value\n"
    path = repo / ".aider.conf.yml"
    path.write_text(original, encoding="utf-8")
    cfg = Config(agents=[_aider_agent_index()], capabilities=[0], repo_dir=str(repo))
    generate_artifacts(cfg)
    assert path.read_text(encoding="utf-8") == original


def test_windsurf_generates_devin_rules_path(tmp_path):
    """Preferred Devin Desktop path is .devin/rules/ (not legacy .windsurfrules)."""
    windsurf_idx = next(i for i, a in enumerate(AGENTS) if a.id == "windsurf")
    adapter = AGENTS[windsurf_idx]
    assert adapter.name == "Devin Desktop"
    assert adapter.files == (".devin/rules/FlossWare.md",)
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / ".git").mkdir()
    cfg = Config(agents=[windsurf_idx], capabilities=[0], repo_dir=str(repo))
    generate_artifacts(cfg)
    path = repo / ".devin" / "rules" / "FlossWare.md"
    assert path.is_file()
    body = path.read_text(encoding="utf-8")
    assert "trigger: always_on" in body
    assert not (repo / ".windsurfrules").exists()
