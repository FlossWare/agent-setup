import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("flossware_setup_tui", ROOT / "scripts" / "setup_tui.py")
tui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tui)


def test_config_round_trip_is_profile_scoped(tmp_path, monkeypatch):
    monkeypatch.setattr(tui, "ROOT", tmp_path / "ai")
    monkeypatch.setattr(tui, "STATE", tmp_path / "ai" / "state")
    monkeypatch.setattr(tui, "ACTIVE_PROFILE", tmp_path / "ai" / "state" / "active-profile")

    config = tui.default_config("personal")
    config["agents"] = ["crush", "claude-code"]
    config["components"] = ["model-router-ai", "rag-ai"]
    config["runtime"] = "podman"
    tui.save_config(config)

    loaded = tui.load_config("personal")
    assert loaded["agents"] == ["crush", "claude-code"]
    assert loaded["components"] == ["model-router-ai", "rag-ai"]
    assert loaded["runtime"] == "podman"
    assert loaded["updated_at"]
    assert tui.ACTIVE_PROFILE.read_text().strip() == "personal"

    assert tui.profile_file("personal").exists()
    assert not tui.profile_file("redhat").exists()


def test_profiles_do_not_share_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(tui, "ROOT", tmp_path / "ai")
    monkeypatch.setattr(tui, "STATE", tmp_path / "ai" / "state")
    monkeypatch.setattr(tui, "ACTIVE_PROFILE", tmp_path / "ai" / "state" / "active-profile")

    personal = tui.default_config("personal")
    personal["agents"] = ["crush"]
    tui.save_config(personal)

    redhat = tui.default_config("redhat")
    redhat["agents"] = ["claude-code"]
    tui.save_config(redhat)

    assert tui.load_config("personal")["agents"] == ["crush"]
    assert tui.load_config("redhat")["agents"] == ["claude-code"]


def test_saved_state_never_contains_credential_values(tmp_path, monkeypatch):
    monkeypatch.setattr(tui, "ROOT", tmp_path / "ai")
    monkeypatch.setattr(tui, "STATE", tmp_path / "ai" / "state")
    monkeypatch.setattr(tui, "ACTIVE_PROFILE", tmp_path / "ai" / "state" / "active-profile")

    secret = "sk-test-not-for-storage"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    config = tui.default_config("personal")
    tui.save_config(config)

    body = tui.profile_file("personal").read_text()
    assert secret not in body
    assert "OPENAI_API_KEY" not in body


def test_default_config_has_persistable_control_plane_sections():
    config = tui.default_config("personal")
    assert config["profile"] == "personal"
    assert "agents" in config
    assert "components" in config
    assert "runtime" in config
    assert "decorators" in config
    assert "updated_at" in config
