"""Configuration-control behavior and safety invariants."""

from __future__ import annotations

import pytest

from flossware_setup import config_control


def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError, match="unknown profile"):
        config_control.load_profile("does-not-exist")


def test_invalid_root_environment_is_ignored(monkeypatch, tmp_path):
    monkeypatch.setenv("FLOSSWARE_AI_ROOT", "relative/path")
    monkeypatch.setenv("FLOSSWARE_INSTALL_ROOT", str(tmp_path / "install"))
    assert config_control.flossware_root() == (tmp_path / "install").resolve()


def test_null_byte_root_environment_is_ignored(monkeypatch, tmp_path):
    # os.environ itself rejects embedded NULs before application code can inspect
    # them. Exercise the application-level validation with a controlled mapping.
    monkeypatch.setattr(
        config_control.os,
        "environ",
        {
            "FLOSSWARE_AI_ROOT": "/tmp/invalid\x00root",
            "FLOSSWARE_INSTALL_ROOT": str(tmp_path / "install"),
        },
    )
    assert config_control.flossware_root() == (tmp_path / "install").resolve()
