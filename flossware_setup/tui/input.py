"""Keyboard and mouse input helpers for the setup TUI."""

from __future__ import annotations

import curses


def enable_mouse() -> bool:
    """Enable terminal mouse reporting when supported."""
    try:
        mask = curses.ALL_MOUSE_EVENTS
        if hasattr(curses, "REPORT_MOUSE_POSITION"):
            mask |= curses.REPORT_MOUSE_POSITION
        curses.mousemask(mask)
        if hasattr(curses, "mouseinterval"):
            curses.mouseinterval(200)
        return True
    except (AttributeError, curses.error):
        return False


def mouse_event() -> tuple[int, int, int] | None:
    """Return ``(x, y, button_state)`` for the current mouse event."""
    try:
        _id, x, y, _z, bstate = curses.getmouse()
    except curses.error:
        return None
    return x, y, bstate


def primary_click() -> tuple[int, int] | None:
    """Return coordinates for a primary-button click/press."""
    event = mouse_event()
    if event is None:
        return None
    x, y, bstate = event
    clicked = getattr(curses, "BUTTON1_CLICKED", 0)
    pressed = getattr(curses, "BUTTON1_PRESSED", 0)
    if bstate & (clicked | pressed):
        return x, y
    return None


def mouse_position() -> tuple[int, int] | None:
    """Return coordinates for motion or any non-click mouse event."""
    event = mouse_event()
    if event is None:
        return None
    x, y, _bstate = event
    return x, y


def is_confirm(key: int) -> bool:
    return key in (10, 13, curses.KEY_ENTER)


def is_cancel(key: int) -> bool:
    return key in (ord("q"), 27)


def is_up(key: int) -> bool:
    return key in (curses.KEY_UP, ord("k"))


def is_down(key: int) -> bool:
    return key in (curses.KEY_DOWN, ord("j"))
