import pytest

from flossware_setup import config_control


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


def test_effective_profile_is_policy_safe():
    config = config_control.validate_effective_config()
    assert config["provider"] == "anthropic"
    assert config["budget.monthly"] <= 300.0
    assert config["policy.allow_personal_accounts"] is False


def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError, match="unknown profile"):
        config_control.load_profile("does-not-exist")
