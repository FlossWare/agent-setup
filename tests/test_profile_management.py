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


def test_edit_profile_tui_loop_persists_providers(ai_root, monkeypatch):
    """Drive the real edit_profile_tui event loop: Enter, edit providers, save."""
    import types

    from flossware_setup.tui import profile_editor as pe

    fake_curses = types.ModuleType("curses")
    fake_curses.KEY_UP = 259
    fake_curses.KEY_DOWN = 258
    fake_curses.KEY_ENTER = 343
    fake_curses.A_BOLD = 0
    fake_curses.echo = lambda: None
    fake_curses.noecho = lambda: None
    monkeypatch.setitem(sys.modules, "curses", fake_curses)

    config_control.create_profile("loopwork", template="default")
    original = config_control.load_profile("loopwork")
    assert original["model_policy"]["allowed_providers"] == ["*configured*"]

    keys = [10, ord("s")]  # Enter on Allowed providers, then save
    getstr_values = [b"openai, anthropic"]

    class _Panel:
        def __init__(self):
            self._keys = list(keys)
            self._gets = list(getstr_values)

        def erase(self):
            return None

        def border(self):
            return None

        def addnstr(self, *args, **kwargs):
            return None

        def refresh(self):
            return None

        def getch(self):
            if not self._keys:
                return 27
            return self._keys.pop(0)

        def getstr(self, *args, **kwargs):
            if not self._gets:
                return b""
            return self._gets.pop(0)

    panel = _Panel()

    def popup(win, top, left, height, width, title):
        return panel

    closed = {"n": 0}

    def close(p):
        closed["n"] += 1

    pe.edit_profile_tui(object(), "loopwork", popup, close)
    assert closed["n"] == 1
    loaded = config_control.load_profile("loopwork")
    assert loaded["model_policy"]["allowed_providers"] == ["openai", "anthropic"]


def test_edit_profile_tui_loop_cancel_leaves_profile_unchanged(ai_root, monkeypatch):
    """Esc in the real editor loop must not call update_profile."""
    import types

    from flossware_setup.tui import profile_editor as pe

    fake_curses = types.ModuleType("curses")
    fake_curses.KEY_UP = 259
    fake_curses.KEY_DOWN = 258
    fake_curses.KEY_ENTER = 343
    fake_curses.A_BOLD = 0
    fake_curses.echo = lambda: None
    fake_curses.noecho = lambda: None
    monkeypatch.setitem(sys.modules, "curses", fake_curses)

    config_control.create_profile("loopcancel", template="default")
    before = config_control.profile_path("loopcancel").read_text(encoding="utf-8")

    class _Panel:
        def erase(self):
            return None

        def border(self):
            return None

        def addnstr(self, *args, **kwargs):
            return None

        def refresh(self):
            return None

        def getch(self):
            return 27  # Esc immediately

        def getstr(self, *args, **kwargs):
            raise AssertionError("cancel path must not request text input")

    def popup(win, top, left, height, width, title):
        return _Panel()

    pe.edit_profile_tui(object(), "loopcancel", popup, lambda p: None)
    after = config_control.profile_path("loopcancel").read_text(encoding="utf-8")
    assert after == before


def test_edit_profile_tui_loop_invalid_provider_does_not_corrupt(ai_root, monkeypatch):
    """Invalid provider text on save keeps the editor open and leaves disk unchanged."""
    import types

    from flossware_setup.tui import profile_editor as pe

    fake_curses = types.ModuleType("curses")
    fake_curses.KEY_UP = 259
    fake_curses.KEY_DOWN = 258
    fake_curses.KEY_ENTER = 343
    fake_curses.A_BOLD = 0
    fake_curses.echo = lambda: None
    fake_curses.noecho = lambda: None
    monkeypatch.setitem(sys.modules, "curses", fake_curses)

    config_control.create_profile("loopbad", template="default")
    before = config_control.profile_path("loopbad").read_text(encoding="utf-8")

    # Enter -> invalid text -> save (rejected) -> Esc
    keys = [10, ord("s"), 27]
    gets = [b"not a valid!!!"]

    class _Panel:
        def __init__(self):
            self._keys = list(keys)
            self._gets = list(gets)

        def erase(self):
            return None

        def border(self):
            return None

        def addnstr(self, *args, **kwargs):
            return None

        def refresh(self):
            return None

        def getch(self):
            return self._keys.pop(0)

        def getstr(self, *args, **kwargs):
            return self._gets.pop(0)

    def popup(win, top, left, height, width, title):
        return _Panel()

    pe.edit_profile_tui(object(), "loopbad", popup, lambda p: None)
    after = config_control.profile_path("loopbad").read_text(encoding="utf-8")
    assert after == before
