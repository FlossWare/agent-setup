"""Keyboard and mouse input helpers for the setup TUI.

Screens should use these helpers instead of interpreting raw curses
mouse events directly.
"""

from __future__ import annotations

import curses
from typing import Optional


def enable_mouse() -> bool:
    """Enable terminal mouse reporting when supported. Returns True if enabled."""
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


def primary_click() -> Optional[tuple[int, int]]:
    """Return (x, y) for a primary-button click/press, otherwise None.

    Call only after getch() returned KEY_MOUSE.
    """
    try:
        _id, x, y, _z, bstate = curses.getmouse()
    except curses.error:
        return None
    clicked = getattr(curses, "BUTTON1_CLICKED", 0)
    pressed = getattr(curses, "BUTTON1_PRESSED", 0)
    if bstate & (clicked | pressed):
        return x, y
    return None


def is_confirm(key: int) -> bool:
    return key in (10, 13, curses.KEY_ENTER)


def is_cancel(key: int) -> bool:
    return key in (ord("q"), 27)


def is_up(key: int) -> bool:
    return key in (curses.KEY_UP, ord("k"))


def is_down(key: int) -> bool:
    return key in (curses.KEY_DOWN, ord("j"))
