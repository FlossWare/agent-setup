"""Catalog integrity for all registered coding-agent integrations."""

from __future__ import annotations

from flossware_setup.catalog import AGENTS, CAPABILITIES, CAPABILITY_REFS, PROVIDERS


def test_exactly_thirteen_agents():
    assert len(AGENTS) == 13


def test_agent_ids_unique():
    ids = [a.id for a in AGENTS]
    assert len(ids) == len(set(ids))


def test_agent_fields_complete():
    for agent in AGENTS:
        assert agent.id
        assert agent.name.strip()
        assert agent.description.strip()
        assert agent.files
        for rel in agent.files:
            assert isinstance(rel, str) and rel
            assert not rel.startswith("/")


def test_expected_agent_ids():
    assert [a.id for a in AGENTS] == [
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
    ]


def test_capability_refs_pinned():
    for name, _desc, _default in CAPABILITIES:
        assert name in CAPABILITY_REFS
        assert len(CAPABILITY_REFS[name]) == 40


def test_providers_have_env_and_url():
    for name, env, url in PROVIDERS:
        assert name and env and url.startswith("https://")
