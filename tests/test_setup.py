"""Offline smoke tests for coding-agent-setup.

No provider credentials or network access are required.
"""

from __future__ import annotations

from flossware_setup.catalog import (
    AGENTS,
    BUDGET_POLICIES,
    CAPABILITIES,
    PROVIDERS,
)
from flossware_setup.config import Config
from flossware_setup.credentials import credential_status


def test_budget_policies_are_pricing_neutral() -> None:
    assert BUDGET_POLICIES[0][0] == "Strict budget"
    assert all("free" not in name.lower() for name, _, _ in BUDGET_POLICIES)


def test_agent_registry_contains_expected_agents() -> None:
    ids = {agent.id for agent in AGENTS}
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
        "windsurf",
        "amazon-q",
        "kiro",
    } <= ids
    assert len(AGENTS) == 13


def test_default_capabilities_include_core_stack() -> None:
    defaults = [name for name, _, selected in CAPABILITIES if selected]
    assert defaults == [
        "model-router-ai",
        "resilience-ai",
        "structured-output-ai",
    ]


def test_providers_do_not_embed_secret_values() -> None:
    for name, env, url in PROVIDERS:
        assert name
        assert env.endswith("_API_KEY") or "KEY" in env
        assert url.startswith("https://")


def test_config_defaults_are_neutral() -> None:
    cfg = Config()
    assert cfg.profile == "default"
    assert cfg.theme == "dark"
    assert cfg.budget_index == 2


def test_credential_status_boolean_only(monkeypatch) -> None:
    monkeypatch.setenv("COHERE_API_KEY", "secret-value")
    status = credential_status()
    assert status["Cohere"] is True
    assert "secret-value" not in repr(status)
