"""TUI theme selection and persistence (#50)."""

from __future__ import annotations

import pytest

from flossware_setup.config_control import THEMES, load_theme, save_theme
from flossware_setup.tui.themes import THEME_LABELS, normalize_theme, theme_definitions


def test_known_themes_and_labels() -> None:
    assert set(THEMES) == {"turbo", "dbase4", "classic", "monochrome"}
    for name in THEMES:
        assert name in THEME_LABELS
        assert theme_definitions()[name]


def test_normalize_aliases() -> None:
    assert normalize_theme("modern") == "monochrome"
    assert normalize_theme("default") == "turbo"
    assert normalize_theme(None) == "turbo"
    assert normalize_theme("dbase") == "dbase4"
    assert normalize_theme("unknown-xyz") == "turbo"
    assert normalize_theme("TURBO") == "turbo"


def test_theme_persists_under_state_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "ai"
    )
    (tmp_path / "ai").mkdir(parents=True)
    assert load_theme() == "turbo"
    save_theme("dbase4")
    assert load_theme() == "dbase4"
    save_theme("classic")
    assert load_theme() == "classic"
    path = tmp_path / "ai" / "theme"
    assert path.is_file()
    assert "classic" in path.read_text(encoding="utf-8")


def test_default_alias_persists_as_turbo(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "ai"
    )
    (tmp_path / "ai").mkdir(parents=True)
    save_theme("default")
    assert load_theme() == "turbo"
    assert (tmp_path / "ai" / "theme").read_text(encoding="utf-8") == "turbo\n"


def test_unknown_theme_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "flossware_setup.config_control.state_dir", lambda: tmp_path / "ai"
    )
    (tmp_path / "ai").mkdir(parents=True)
    with pytest.raises(ValueError, match="unknown theme"):
        save_theme("not-a-theme")
