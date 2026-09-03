"""Mouse input helpers and list hit-testing (no interactive terminal)."""

from __future__ import annotations

import curses

from flossware_setup.tui import input as tui_input


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
    assert tui_input.resolve_list_mouse(
        (0, 6, 4), origin_y=5, count=20, scroll_offset=4, visible=3
    ) == ("activate", 5)
    assert tui_input.resolve_list_mouse(
        (0, 9, 4), origin_y=5, count=20, scroll_offset=4, visible=3
    ) is None


def test_resolve_list_mouse_pressed_as_activate(monkeypatch):
    """BUTTON1_PRESSED must activate (terminals often report press, not click)."""
    monkeypatch.setattr(curses, "BUTTON1_CLICKED", 4, raising=False)
    monkeypatch.setattr(curses, "BUTTON1_PRESSED", 2, raising=False)
    assert tui_input.resolve_list_mouse((0, 5, 2), origin_y=5, count=3) == ("activate", 0)


def test_enable_mouse_degrades_when_mousemask_fails(monkeypatch):
    def _boom(*_a, **_k):
        raise curses.error("no mouse")

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

    def _err():
        raise curses.error("x")

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
