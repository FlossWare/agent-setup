"""Profile create/select/edit/validate persistence and safety."""

from __future__ import annotations

import pytest

from flossware_setup import config_control
from flossware_setup.cli import main as cli_main


@pytest.fixture()
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
