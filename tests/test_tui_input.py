"""Tests for TUI input helpers (no terminal required)."""

from __future__ import annotations

import curses

from flossware_setup.tui import input as tui_input


def test_key_helpers():
    assert tui_input.is_confirm(10)
    assert tui_input.is_confirm(13)
    assert tui_input.is_cancel(27)
    assert tui_input.is_cancel(ord("q"))
    assert tui_input.is_up(curses.KEY_UP)
    assert tui_input.is_up(ord("k"))
    assert tui_input.is_down(curses.KEY_DOWN)
    assert tui_input.is_down(ord("j"))


def test_primary_click_signature_has_no_unused_event_param():
    import inspect

    sig = inspect.signature(tui_input.primary_click)
    assert list(sig.parameters) == []
