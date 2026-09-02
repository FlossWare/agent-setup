"""Profile create/select/edit/validate persistence and safety."""

from __future__ import annotations

import sys
import types

import pytest

from flossware_setup import config_control
from flossware_setup.cli import main as cli_main


@pytest.fixture
def ai_root(tmp_path, monkeypatch):
    root = tmp_path / "ai"
    root.mkdir()
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", str(root))
    monkeypatch.delenv("FLOSSWARE_INSTALL_ROOT", raising=False)
    return root


def test_create_select_edit_roundtrip(ai_root):
    path = config_control.create_profile("worklab", template="default")
    assert path.is_file()
    assert "worklab" in config_control.available_profiles()

    config_control.save_active_profile("worklab")
    assert config_control.load_active_profile() == "worklab"
    assert config_control.profile_for_directory()[0] == "worklab"

    config_control.update_profile(
        "worklab",
        {
            "allowed_providers": ["*configured*"],
            "allow_local_models": False,
            "monthly_limit_usd": 25.0,
            "hard_limit": True,
        },
    )
    data = config_control.load_profile("worklab")
    assert data["model_policy"]["allow_local_models"] is False
    assert data["cost"]["monthly_limit_usd"] == 25.0
    assert data["cost"]["hard_limit"] is True


def test_invalid_profile_does_not_corrupt_existing(ai_root):
    config_control.create_profile("safe", template="default")
    before = config_control.profile_path("safe").read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="provider reference|secret|must"):
        config_control.update_profile(
            "safe",
            {"allowed_providers": ["not a valid provider!!!"]},
        )
    after = config_control.profile_path("safe").read_text(encoding="utf-8")
    assert after == before


def test_secret_values_rejected(ai_root):
    with pytest.raises(ValueError, match="secret|credential"):
        config_control.write_profile(
            "badsec",
            {
                "profile": "badsec",
                "model_policy": {
                    "allowed_providers": ["*configured*"],
                    "api_key": "sk-live-should-not-persist-abc123xyz",
                },
            },
        )
    assert not config_control.profile_path("badsec").exists()


def test_cli_profile_commands(ai_root, capsys):
    assert cli_main(["profile", "create", "cliwork"]) == 0
    assert cli_main(["profile", "select", "cliwork"]) == 0
    assert cli_main(["profile", "list"]) == 0
    out = capsys.readouterr().out
    assert "* cliwork" in out
    assert cli_main(["profile", "edit", "cliwork", "--monthly-limit", "10"]) == 0
    assert cli_main(["profile", "validate", "cliwork"]) == 0
    assert cli_main(["profile", "show", "cliwork"]) == 0


def test_unknown_select_fails_clearly(ai_root):
    with pytest.raises(ValueError, match="unknown profile"):
        config_control.save_active_profile("does-not-exist")


def test_active_profile_syncs_legacy_marker(ai_root):
    config_control.create_profile("synced", template="default")
    path = config_control.save_active_profile("synced")
    assert path.read_text(encoding="utf-8").strip() == "synced"
    legacy = config_control.state_dir() / "profile"
    assert legacy.read_text(encoding="utf-8").strip() == "synced"
    path.unlink()
    assert config_control.load_active_profile() == "synced"


def test_load_active_prefers_canonical_marker(ai_root):
    config_control.create_profile("alpha", template="default")
    config_control.create_profile("beta", template="default")
    legacy = config_control.state_dir() / "profile"
    legacy.write_text("alpha\n", encoding="utf-8")
    config_control.active_profile_path().write_text("beta\n", encoding="utf-8")
    assert config_control.load_active_profile() == "beta"


def test_parse_providers_field_supports_text_editing():
    from flossware_setup.tui.profile_editor import parse_providers_field

    assert parse_providers_field("openai, anthropic") == ["openai", "anthropic"]
    assert parse_providers_field("  ") == ["*configured*"]
    assert parse_providers_field("*configured*") == ["*configured*"]


def test_tui_provider_edit_persists_via_shared_api(ai_root, monkeypatch):
    """Text-field edit path produces values that update_profile persists."""
    from flossware_setup.tui import profile_editor as pe

    fake = types.ModuleType("curses")
    fake.echo = lambda: None
    fake.noecho = lambda: None
    monkeypatch.setitem(sys.modules, "curses", fake)

    config_control.create_profile("tuiwork", template="default")
    fields = pe.fields_from_profile(config_control.load_profile("tuiwork"))
    assert fields[0][2] == "text"

    class _Panel:
        def addnstr(self, *args, **kwargs):
            return None

        def refresh(self):
            return None

        def getstr(self, *args, **kwargs):
            return b"openai, anthropic"

    fields[0][1] = pe.edit_text_field(_Panel(), 12, 58, str(fields[0][1]))
    assert fields[0][1] == "openai, anthropic"
    values = pe.proposed_values_from_fields(fields)
    assert values["allowed_providers"] == ["openai", "anthropic"]
    config_control.update_profile("tuiwork", values)
    loaded = config_control.load_profile("tuiwork")
    assert loaded["model_policy"]["allowed_providers"] == ["openai", "anthropic"]


def test_tui_cancel_does_not_persist(ai_root):
    from flossware_setup.tui import profile_editor as pe

    config_control.create_profile("cancelme", template="default")
    original = config_control.profile_path("cancelme").read_text(encoding="utf-8")
    fields = pe.fields_from_profile(config_control.load_profile("cancelme"))
    fields[0][1] = "openai"
    after = config_control.profile_path("cancelme").read_text(encoding="utf-8")
    assert after == original


def test_tui_invalid_provider_does_not_corrupt(ai_root):
    from flossware_setup.tui import profile_editor as pe

    config_control.create_profile("badprov", template="default")
    original = config_control.profile_path("badprov").read_text(encoding="utf-8")
    fields = pe.fields_from_profile(config_control.load_profile("badprov"))
    fields[0][1] = "not a valid!!!"
    values = pe.proposed_values_from_fields(fields)
    with pytest.raises(ValueError):
        config_control.update_profile("badprov", values)
    assert config_control.profile_path("badprov").read_text(encoding="utf-8") == original


def test_apply_field_key_edits_text_slot():
    from flossware_setup.tui.profile_editor import apply_field_key

    fields = [["Allowed providers", "*configured*", "text"]]
    idx = apply_field_key(
        fields,
        0,
        10,
        key_up=259,
        key_down=258,
        key_enter=343,
        edit_text=lambda current: "openai",
    )
    assert idx == 0
    assert fields[0][1] == "openai"


def test_write_profile_rejects_path_escape(ai_root):
    with pytest.raises(ValueError, match="invalid profile name"):
        config_control.write_profile(
            "../escape",
            {"profile": "x", "model_policy": {"allowed_providers": ["*configured*"]}},
        )
