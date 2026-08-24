"""Offline smoke tests for coding-agent-setup.

No provider credentials or network access are required.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("flossware_setup", ROOT / "scripts" / "setup.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_setup_module_compiles() -> None:
    assert MODULE.BUDGET_POLICIES[0][0] == "Strict budget"
    assert all("free" not in name.lower() for name, _, _ in MODULE.BUDGET_POLICIES)


def test_agent_registry_contains_expected_agents() -> None:
    ids = {agent.id for agent in MODULE.AGENT_ADAPTERS}
    assert {
        "claude-code",
        "cursor",
        "opencode",
        "crush",
        "codex",
        "aider",
        "cline",
        "roo-code",
        "gemini-cli",
        "github-copilot",
    } <= ids
    assert len(ids) == len(MODULE.AGENT_ADAPTERS)


def test_shared_agents_file_is_used_by_shared_agents() -> None:
    for agent_id in ("opencode", "crush", "codex"):
        agent = next(a for a in MODULE.AGENT_ADAPTERS if a.id == agent_id)
        assert agent.files == ("AGENTS.md",)


def test_generated_configuration_never_contains_credential_value(tmp_path, monkeypatch) -> None:
    (tmp_path / ".git").mkdir()
    secret = "TEST-SHOULD-NEVER-APPEAR-IN-GENERATED-FILES"
    monkeypatch.setenv("COHERE_API_KEY", secret)
    cfg = MODULE.Config(agents=[0, 3, 5], capabilities=[0], repo_dir=str(tmp_path))

    MODULE.generate_artifacts(cfg)

    for relative in (
        "CLAUDE.md",
        "AGENTS.md",
        "CONVENTIONS.md",
        ".aider.conf.yml",
        "ai_config.py",
        ".flossware-ai.json",
    ):
        path = tmp_path / relative
        assert path.exists()
        assert secret not in path.read_text(encoding="utf-8")


def test_generated_configuration_contains_environment_name_only(tmp_path, monkeypatch) -> None:
    (tmp_path / ".git").mkdir()
    monkeypatch.setenv("COHERE_API_KEY", "secret-value")
    cfg = MODULE.Config(agents=[0], capabilities=[0], repo_dir=str(tmp_path))

    MODULE.generate_artifacts(cfg)

    config = (tmp_path / "ai_config.py").read_text(encoding="utf-8")
    assert "COHERE_API_KEY" in config
    assert "secret-value" not in config


def test_generation_is_idempotent_and_preserves_existing_files(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    existing = tmp_path / "AGENTS.md"
    existing.write_text("user-owned instructions\n", encoding="utf-8")
    cfg = MODULE.Config(agents=[3], capabilities=[0], repo_dir=str(tmp_path))

    MODULE.generate_artifacts(cfg)
    MODULE.generate_artifacts(cfg)

    assert existing.read_text(encoding="utf-8") == "user-owned instructions\n"
