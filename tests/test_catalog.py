"""Catalog integrity for all registered coding-agent integrations."""

from __future__ import annotations

from flossware_setup.catalog import AGENTS, CAPABILITIES, CAPABILITY_REFS, PROVIDERS


def test_exactly_thirteen_agents():
    assert len(AGENTS) == 13


def test_agent_ids_unique():
    ids = [a.id for a in AGENTS]
    assert len(ids) == len(set(ids))


def test_agent_ids_nonempty():
    for agent in AGENTS:
        assert agent.id


def test_agent_names_nonempty():
    for agent in AGENTS:
        assert agent.name.strip()


def test_agent_descriptions_nonempty():
    for agent in AGENTS:
        assert agent.description.strip()


def test_agent_files_are_relative_paths():
    for agent in AGENTS:
        assert agent.files
        for rel in agent.files:
            assert isinstance(rel, str)
            assert rel
            assert not rel.startswith("/")


def test_expected_agent_ids():
    assert [a.id for a in AGENTS] == [
        "claude-code", "cursor", "opencode", "crush", "codex", "aider",
        "cline", "roo-code", "gemini-cli", "github-copilot", "windsurf",
        "amazon-q", "kiro",
    ]


def test_capability_refs_pinned():
    for name, _desc, _default in CAPABILITIES:
        assert name in CAPABILITY_REFS
        assert len(CAPABILITY_REFS[name]) == 40


def test_providers_have_names():
    for name, env, url in PROVIDERS:
        assert name


def test_providers_have_env_vars():
    for name, env, url in PROVIDERS:
        assert env


def test_providers_have_https_urls():
    for name, env, url in PROVIDERS:
        assert url.startswith("https://")


def test_anthropic_provider_is_cataloged():
    assert ("Anthropic", "ANTHROPIC_API_KEY", "https://console.anthropic.com/settings/keys") in PROVIDERS


def test_no_duplicate_provider_env_vars():
    envs = [env for _name, env, _url in PROVIDERS]
    assert len(envs) == len(set(envs))


def test_no_agent_adapters_alias():
    """AGENTS is the single public catalog name; no migration alias."""
    from flossware_setup import catalog

    assert hasattr(catalog, "AGENTS")
    assert not hasattr(catalog, "AGENT_ADAPTERS")
