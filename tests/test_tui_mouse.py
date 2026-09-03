"""Mouse input helpers and list hit-testing (no interactive terminal)."""

from __future__ import annotations

import curses

import flossware_setup.tui as tui_package
from flossware_setup.tui import config_screen
from flossware_setup.tui import input as tui_input
from flossware_setup.tui import ux


def test_list_index_at_bounds():
    assert tui_input.list_index_at(5, 5, 3) == 0
    assert tui_input.list_index_at(7, 5, 3) == 2
    assert tui_input.list_index_at(4, 5, 3) is None
    assert tui_input.list_index_at(8, 5, 3) is None
    assert tui_input.list_index_at(5, 5, 0) is None


def test_list_index_at_with_scroll_offset():
    assert tui_input.list_index_at(5, 5, 10, scroll_offset=3, visible=3) == 3
    assert tui_input.list_index_at(7, 5, 10, scroll_offset=3, visible=3) == 5
    assert tui_input.list_index_at(8, 5, 10, scroll_offset=3, visible=3) is None
    assert tui_input.list_index_at(4, 5, 10, scroll_offset=3, visible=3) is None


def test_is_primary_click_uses_button_masks(monkeypatch):
    monkeypatch.setattr(curses, "BUTTON1_CLICKED", 4, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_PRESSED", 2, raising=False)
    assert tui_input.is_primary_click(4) is True
    assert tui_input.is_primary_click(2) is True
    assert tui_input.is_primary_click(1) is False
    assert tui_input.is_primary_click(0) is False


def test_resolve_list_mouse_activate_and_focus(monkeypatch):
    monkeypatch.setattr(curses, "BUTTON1_CLICKED", 4, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_PRESSED", 2, raising=False)
    assert tui_input.resolve_list_mouse((0, 6, 4), origin_y=5, count=4) == ("activate", 1)
    assert tui_input.resolve_list_mouse((0, 6, 0), origin_y=5, count=4) == ("focus", 1)
    assert tui_input.resolve_list_mouse(None, origin_y=5, count=4) is None
    assert tui_input.resolve_list_mouse((0, 1, 4), origin_y=5, count=4) is None


def test_resolve_list_mouse_scroll_and_visible(monkeypatch):
    monkeypatch.setattr(curses, "BUTTON1_CLICKED", 4, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_PRESSED", 2, raising=False)
    assert tui_input.resolve_list_mouse((0, 6, 4), origin_y=5, count=20, scroll_offset=4, visible=3) == ("activate", 5)
    assert tui_input.resolve_list_mouse((0, 9, 4), origin_y=5, count=20, scroll_offset=4, visible=3) is None


def test_resolve_list_mouse_pressed_as_activate(monkeypatch):
    monkeypatch.setattr(curses, "BUTTON1_CLICKED", 4, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_PRESSED", 2, raising=False)
    assert tui_input.resolve_list_mouse((0, 5, 2), origin_y=5, count=3) == ("activate", 0)


def _install_fake_profile_selector(monkeypatch, mouse_event):
    class FakePanel:
        def __init__(self):
            self.keys = [curses.KEY_MOUSE]

        def getch(self):
            return self.keys.pop(0) if self.keys else 27

        def refresh(self): return None
        def addnstr(self, *args): return None
        def addstr(self, *args): return None
        def bkgd(self, *args): return None
        def erase(self): return None
        def noutrefresh(self): return None
        def border(self): return None

    class FakeWin:
        def getmaxyx(self): return (30, 100)
        def erase(self): return None
        def refresh(self): return None
        def touchwin(self): return None
        def noutrefresh(self): return None

    class FakeIde:
        ITEMS = {"Config": ("Profiles",)}
        _ux_fixes_installed = False
        available_profiles = staticmethod(lambda: ["default", "free"])
        add = staticmethod(lambda *args: None)
        palette = staticmethod(lambda *args: 0)

    ide = FakeIde()
    panel = FakePanel()
    saved = []
    closed = []
    monkeypatch.setattr(tui_package, "ide", ide, raising=False)

    # install_tui_fixes uses local imports from these modules, so patch the
    # actual provider modules rather than adding attributes to ux.py.
    import flossware_setup.config_control as config_control
    import flossware_setup.tui.input as tui_input_module
    import flossware_setup.tui.profile_editor as profile_editor
    import flossware_setup.tui.validation as validation

    monkeypatch.setattr(config_control, "available_profiles", lambda: ("default", "free"))
    monkeypatch.setattr(config_control, "load_active_profile", lambda: "default")
    monkeypatch.setattr(config_control, "save_active_profile", saved.append)
    monkeypatch.setattr(tui_input_module, "is_mouse", lambda key: key == curses.KEY_MOUSE)
    monkeypatch.setattr(tui_input_module, "mouse_event", lambda: mouse_event)
    monkeypatch.setattr(profile_editor, "edit_profile_tui", lambda *args: None)
    monkeypatch.setattr(validation, "validate_popup", lambda *args: None)

    ide._popup = lambda *args: panel
    ide._close = lambda p: closed.append(p)
    ux.install_tui_fixes()
    return ide, panel, saved, closed, FakeWin


def test_profile_selector_mouse_activation_uses_real_install(monkeypatch):
    monkeypatch.setattr(curses, "BUTTON1_CLICKED", 4, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_PRESSED", 2, raising=False)
    ide, panel, saved, closed, FakeWin = _install_fake_profile_selector(monkeypatch, (0, 14, curses.BUTTON1_PRESSED))
    assert ide.profile_selector(FakeWin()) == "free"
    assert saved == ["free"]
    assert closed == [panel]


def test_profile_selector_mouse_outside_list_does_not_activate(monkeypatch):
    monkeypatch.setattr(curses, "BUTTON1_CLICKED", 4, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_PRESSED", 2, raising=False)
    ide, panel, saved, closed, FakeWin = _install_fake_profile_selector(monkeypatch, (0, 20, curses.BUTTON1_CLICKED))
    assert ide.profile_selector(FakeWin()) is None
    assert saved == []
    assert closed == [panel]


def test_profile_selector_mouse_clicked_also_activates(monkeypatch):
    monkeypatch.setattr(curses, "BUTTON1_CLICKED", 4, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_PRESSED", 2, raising=False)
    ide, panel, saved, closed, FakeWin = _install_fake_profile_selector(monkeypatch, (0, 14, curses.BUTTON1_CLICKED))
    assert ide.profile_selector(FakeWin()) == "free"
    assert saved == ["free"]
    assert closed == [panel]


def test_enable_mouse_degrades_when_mousemask_fails(monkeypatch):
    def _boom(*_a, **_k): raise curses.error("no mouse")
    monkeypatch.setattr(curses, "mousemask", _boom, raising=False)
    assert tui_input.enable_mouse() is False


def test_enable_mouse_returns_false_when_mask_unavailable(monkeypatch):
    monkeypatch.setattr(curses, "mousemask", lambda mask: (0, 0), raising=False)
    monkeypatch.setattr(curses, "ALL_MOUSE_EVENTS", 0, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_CLICKED", 0, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_PRESSED", 0, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_RELEASED", 0, raising=False)
    assert tui_input.enable_mouse() is False


def test_primary_click_reads_getmouse(monkeypatch):
    monkeypatch.setattr(curses, "BUTTON1_CLICKED", 4, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_PRESSED", 2, raising=False)
    monkeypatch.setattr(curses, "getmouse", lambda: (0, 3, 9, 0, 4), raising=False)
    assert tui_input.primary_click() == (3, 9)
    def _err(): raise curses.error("x")
    monkeypatch.setattr(curses, "getmouse", _err, raising=False)
    assert tui_input.primary_click() is None


def test_is_mouse_token():
    assert tui_input.is_mouse(getattr(curses, "KEY_MOUSE", -2)) is True
    assert tui_input.is_mouse(ord("a")) is False


def test_keyboard_helpers_unaffected():
    assert tui_input.is_confirm(10)
    assert tui_input.is_cancel(27)
    assert tui_input.is_up(curses.KEY_UP)
    assert tui_input.is_down(curses.KEY_DOWN)
