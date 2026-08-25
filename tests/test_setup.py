"""Offline smoke tests for coding-agent-setup.

No provider credentials or network access are required.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("flossware_setup", ROOT / "scripts" / "setup.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
# dataclasses resolves the defining module through sys.modules while processing
# annotations. Register the dynamically loaded module before executing it so
# the test behaves like a normal import on every supported Python platform.
sys.modules[SPEC.name] = MODULE
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
        "windsurf",
        "amazon-q",
        "kiro",
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


def test_all_adapters_generate_their_declared_targets(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    cfg = MODULE.Config(agents=list(range(len(MODULE.AGENT_ADAPTERS))), capabilities=[0], repo_dir=str(tmp_path))

    MODULE.generate_artifacts(cfg)

    for adapter in MODULE.AGENT_ADAPTERS:
        for relative in adapter.files:
            assert (tmp_path / relative).exists(), f"missing target for {adapter.id}: {relative}"


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


def test_cursor_writes_modern_mdc_rules(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    cursor = next(i for i, a in enumerate(MODULE.AGENT_ADAPTERS) if a.id == "cursor")
    cfg = MODULE.Config(agents=[cursor], capabilities=[0], repo_dir=str(tmp_path))
    MODULE.generate_artifacts(cfg)
    mdc = tmp_path / ".cursor/rules/flossware-ai.mdc"
    legacy = tmp_path / ".cursorrules"
    assert mdc.exists()
    assert legacy.exists()
    text = mdc.read_text(encoding="utf-8")
    assert "alwaysApply: true" in text
    assert MODULE.SECTION_BEGIN in text
    assert "FlossWare AI Integration" in text


def test_marked_section_is_refreshed_without_duplication(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    agent = next(i for i, a in enumerate(MODULE.AGENT_ADAPTERS) if a.id == "claude-code")
    cfg = MODULE.Config(agents=[agent], capabilities=[0], repo_dir=str(tmp_path))
    MODULE.generate_artifacts(cfg)
    path = tmp_path / "CLAUDE.md"
    first = path.read_text(encoding="utf-8")
    MODULE.generate_artifacts(cfg)
    second = path.read_text(encoding="utf-8")
    assert first == second
    assert first.count(MODULE.SECTION_BEGIN) == 1
    assert first.count(MODULE.SECTION_END) == 1


def test_shared_agents_md_written_once_for_multiple_consumers(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    ids = {a.id: i for i, a in enumerate(MODULE.AGENT_ADAPTERS)}
    selected = [ids["opencode"], ids["crush"], ids["codex"], ids["github-copilot"]]
    cfg = MODULE.Config(agents=selected, capabilities=[0], repo_dir=str(tmp_path))
    MODULE.generate_artifacts(cfg)
    agents_md = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert agents_md.count(MODULE.SECTION_BEGIN) == 1
    assert (tmp_path / ".github/copilot-instructions.md").exists()


def test_tui_agent_list_matches_registry() -> None:
    import importlib.util
    from pathlib import Path as P
    root = P(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("flossware_tui_agents", root / "scripts" / "tui.py")
    tui = importlib.util.module_from_spec(spec)
    # tui loads setup at import
    import sys
    sys.modules[spec.name] = tui
    assert spec.loader is not None
    spec.loader.exec_module(tui)
    assert tui.AGENTS == [a.id for a in MODULE.AGENT_ADAPTERS]
