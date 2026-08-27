import shutil
from pathlib import Path

import pytest

from flossware_setup import config_control

ROOT = Path(__file__).resolve().parents[1]
WORK_PROFILE = ROOT / "profiles" / "examples" / "redhat-cost-conscious.toml"


def test_default_order_is_constraint_safe():
    assert config_control.load_order() == config_control.DEFAULT_ORDER


def test_save_and_load_order(tmp_path, monkeypatch):
    monkeypatch.setattr(config_control, "state_dir", lambda: tmp_path)
    order = ["providers", "agents", "models", "optimization", "validation"]
    config_control.save_order(order)
    assert config_control.load_order() == order


def test_invalid_persisted_order_falls_back(tmp_path, monkeypatch):
    monkeypatch.setattr(config_control, "state_dir", lambda: tmp_path)
    config_control.order_path().write_text('{"order":["agents"]}', encoding="utf-8")
    assert config_control.load_order() == config_control.DEFAULT_ORDER


def test_effective_personal_profile_is_permissive():
    config = config_control.validate_effective_config("personal")
    assert config["provider"] == "auto"
    assert config["policy.allow_personal_accounts"] is True


def test_effective_work_profile_is_policy_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(config_control, "state_dir", lambda: tmp_path)
    profiles = tmp_path / "profiles"
    profiles.mkdir(parents=True)
    assert WORK_PROFILE.is_file(), f"missing work profile template: {WORK_PROFILE}"
    shutil.copy(WORK_PROFILE, profiles / "redhat-cost-conscious.toml")
    config = config_control.validate_effective_config("redhat-cost-conscious")
    assert config["provider"] == "anthropic"
    assert config["budget.monthly"] <= 300.0
    assert config["policy.allow_personal_accounts"] is False


def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError, match="unknown profile"):
        config_control.load_profile("does-not-exist")


def test_invalid_root_environment_is_ignored(monkeypatch, tmp_path):
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", "relative/path")
    monkeypatch.setenv("FLOSSWARE_INSTALL_ROOT", str(tmp_path / "install"))
    assert config_control.flossware_root() == (tmp_path / "install").resolve()


def test_null_byte_root_environment_is_ignored(monkeypatch, tmp_path):
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", "/tmp/invalid\x00root")
    monkeypatch.setenv("FLOSSWARE_INSTALL_ROOT", str(tmp_path / "install"))
    assert config_control.flossware_root() == (tmp_path / "install").resolve()
