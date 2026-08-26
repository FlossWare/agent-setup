"""Active project context for Review Current Configuration."""

from __future__ import annotations

from flossware_setup.artifacts import generate_artifacts
from flossware_setup.config import (
    Config,
    get_active_project,
    resolve_review_project,
    review_lines,
    set_active_project,
)


def test_set_and_get_active_project(tmp_path, monkeypatch):
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(tmp_path / "ai"))
    project = tmp_path / "proj-a"
    project.mkdir()
    set_active_project(project)
    assert get_active_project() == project.resolve()


def test_review_uses_active_project_not_cwd(tmp_path, monkeypatch):
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(tmp_path / "ai"))
    project = tmp_path / "proj-a"
    other = tmp_path / "other-cwd"
    project.mkdir()
    other.mkdir()
    cfg = Config(
        agents=["claude-code"],
        capabilities=["model-router-ai"],
        repo_dir=str(project),
        profile="default",
    )
    generate_artifacts(cfg)
    monkeypatch.chdir(other)
    resolved = resolve_review_project(None)
    assert resolved == project.resolve()
    joined = "\n".join(review_lines(resolved))
    assert "Claude Code" in joined


def test_active_project_file_has_no_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(tmp_path / "ai"))
    monkeypatch.setenv("GROQ_API_KEY", "sk-should-not-appear")
    project = tmp_path / "proj"
    project.mkdir()
    set_active_project(project)
    body = (tmp_path / "ai" / "state" / "active-project").read_text(encoding="utf-8")
    assert "sk-should-not-appear" not in body
