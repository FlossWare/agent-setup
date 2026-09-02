"""Secret-scanning and privacy regression tests (issues #40/#44, #37/#41, #39/#43)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from flossware_setup.artifacts import generate_artifacts
from flossware_setup.config import Config, build_state_dict, load_project_state, project_state_path
from flossware_setup.credentials import (
    ALLOWED_STATE_KEYS,
    assert_no_secret_material,
    filter_state_keys,
    is_secret_key_name,
    scan_mapping_for_secrets,
    text_contains_identity_material,
    text_contains_secret_material,
)


def test_secret_key_names_detected() -> None:
    assert is_secret_key_name("openai_api_key")
    assert is_secret_key_name("API-KEY")
    assert is_secret_key_name("client_secret")
    assert not is_secret_key_name("provider")
    assert not is_secret_key_name("monthly_budget")


def test_secret_value_patterns() -> None:
    assert text_contains_secret_material("key=sk-abcdefghijklmnopqrstuvwxyz")
    assert text_contains_secret_material("Authorization: Bearer " + "x" * 24)
    assert text_contains_secret_material("ghp_" + "A" * 36)
    assert not text_contains_secret_material("use OPENAI_API_KEY from the environment")


def test_identity_patterns() -> None:
    assert text_contains_identity_material("user@example.com")
    assert not text_contains_identity_material("openai-personal-1")


def test_scan_mapping_flags_forbidden_keys() -> None:
    findings = scan_mapping_for_secrets({"openai_api_key": "present", "profile": "default"})
    assert any("forbidden key" in f for f in findings)


def test_filter_state_keys_whitelist() -> None:
    raw = {"profile": "default", "openai_api_key": "sk-leak", "extra": 1}
    cleaned = filter_state_keys(raw)
    assert "openai_api_key" not in cleaned
    assert "extra" not in cleaned
    assert cleaned["profile"] == "default"
    assert cleaned.keys() <= ALLOWED_STATE_KEYS


def test_build_state_dict_only_whitelist_keys() -> None:
    state = build_state_dict(Config())
    assert set(state.keys()) <= ALLOWED_STATE_KEYS
    assert state["credential_values_written"] is False
    assert all(isinstance(v, bool) for v in state["providers"].values())


def test_build_state_dict_no_env_secret_values(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-" + "live" + "x" * 20)
    monkeypatch.setenv("GROQ_API_KEY", "should-not-appear-xyz")
    state = build_state_dict(Config())
    blob = json.dumps(state)
    assert "should-not-appear-xyz" not in blob
    assert "sk-live" not in blob


def test_load_project_state_strips_unknown_and_secret_keys(tmp_path) -> None:
    path = project_state_path(tmp_path)
    path.write_text(
        json.dumps(
            {
                "profile": "default",
                "openai_api_key": "sk-abcdefghijklmnopqrstuvwxyz0123",
                "rogue": True,
                "credential_values_written": False,
                "agents": [],
                "capabilities": [],
                "providers": {},
                "provider_env_vars": {},
                "budget_policy": "medium",
                "budget_policy_id": "medium",
                "monthly_budget": 50,
                "theme": "dark",
                "tool": "FlossWare/agent-setup",
            }
        ),
        encoding="utf-8",
    )
    loaded = load_project_state(tmp_path)
    assert "openai_api_key" not in loaded
    assert "rogue" not in loaded
    assert loaded.get("profile") == "default"


def test_assert_no_secret_material_raises() -> None:
    with pytest.raises(ValueError, match="credential material"):
        assert_no_secret_material("token=sk-" + "abc" * 10, label="unit")


def test_generate_artifacts_never_embeds_env_secrets(tmp_path, monkeypatch) -> None:
    repo = tmp_path / "proj"
    repo.mkdir()
    secret = "sk-" + "live" + "Z" * 24
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "should-never-land-in-files")
    cfg = Config(
        agents=["claude-code", "cursor"],
        capabilities=["coding-agent-ai"],
        budget_policy="medium",
        repo_dir=str(repo),
    )
    state = generate_artifacts(cfg)
    assert state["credential_values_written"] is False
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8", errors="replace")
        assert secret not in body
        assert "should-never-land-in-files" not in body


def test_templates_contain_no_live_secret_patterns() -> None:
    root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    for path in list((root / "templates").rglob("*")) + list((root / "profiles").rglob("*.toml")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if text_contains_secret_material(text):
            offenders.append(str(path.relative_to(root)))
    assert offenders == []
