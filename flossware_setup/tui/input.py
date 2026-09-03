"""Keyboard and mouse input helpers for the setup TUI."""

from __future__ import annotations

import curses
from typing import Any


def enable_mouse() -> bool:
    """Enable terminal mouse reporting when supported.

    Returns False when the terminal or curses build cannot report mouse
    events so callers can continue in keyboard-only mode.
    """
    try:
        mask = getattr(curses, "ALL_MOUSE_EVENTS", 0)
        if hasattr(curses, "REPORT_MOUSE_POSITION"):
            mask |= curses.REPORT_MOUSE_POSITION
        if not mask:
            # Minimal portable fallback: primary button press/click.
            mask = (
                getattr(curses, "BUTTON1_PRESSED", 0)
                | getattr(curses, "BUTTON1_CLICKED", 0)
                | getattr(curses, "BUTTON1_RELEASED", 0)
            )
        if not mask:
            return False
        result = curses.mousemask(mask)
        # mousemask returns (available, old) on success in ncurses.
        available = result[0] if isinstance(result, tuple) else result
        if not available:
            return False
        if hasattr(curses, "mouseinterval"):
            try:
                curses.mouseinterval(200)
            except curses.error:
                pass
        return True
    except (AttributeError, curses.error, TypeError, ValueError):
        return False


def mouse_event() -> tuple[int, int, int] | None:
    """Return ``(x, y, button_state)`` for the current mouse event."""
    try:
        _id, x, y, _z, bstate = curses.getmouse()
    except (curses.error, AttributeError, TypeError, ValueError):
        return None
    return int(x), int(y), int(bstate)


def primary_button_mask() -> int:
    """Bitmask for primary button press/click events."""
    return int(
        getattr(curses, "BUTTON1_CLICKED", 0)
        | getattr(curses, "BUTTON1_PRESSED", 0)
    )


def is_primary_click(bstate: int) -> bool:
    """True when *bstate* includes a primary-button press or click."""
    mask = primary_button_mask()
    return bool(mask and (int(bstate) & mask))


def primary_click() -> tuple[int, int] | None:
    """Return coordinates for a primary-button click/press."""
    event = mouse_event()
    if event is None:
        return None
    x, y, bstate = event
    if is_primary_click(bstate):
        return x, y
    return None


def mouse_position() -> tuple[int, int] | None:
    """Return coordinates for motion or any non-click mouse event."""
    event = mouse_event()
    if event is None:
        return None
    x, y, _bstate = event
    return x, y


def list_index_at(
    y: int,
    origin_y: int,
    count: int,
    *,
    scroll_offset: int = 0,
    visible: int | None = None,
) -> int | None:
    """Map a screen row to a list index, accounting for scroll.

    *origin_y* is the screen row of the first *visible* item.
    *scroll_offset* is the index of the first visible item in the full list.
    *visible* limits the hit region height (defaults to *count* when omitted).
    """
    if count <= 0:
        return None
    row = int(y) - int(origin_y)
    limit = int(count) if visible is None else max(0, int(visible))
    if not (0 <= row < limit):
        return None
    index = row + int(scroll_offset)
    if 0 <= index < int(count):
        return index
    return None


def resolve_list_mouse(
    event: tuple[int, int, int] | None,
    *,
    origin_y: int,
    count: int,
    scroll_offset: int = 0,
    visible: int | None = None,
) -> tuple[str, int] | None:
    """Interpret a mouse event against a vertical list.

    Returns:
        ("activate", index) for primary click on a row
        ("focus", index) for non-click motion/hover on a row
        None when the event is absent or outside the list

    *index* is the absolute list index (scroll-aware).
    """
    if event is None or count <= 0:
        return None
    _x, y, bstate = event
    index = list_index_at(
        y,
        origin_y,
        count,
        scroll_offset=scroll_offset,
        visible=visible,
    )
    if index is None:
        return None
    if is_primary_click(bstate):
        return "activate", index
    return "focus", index


def is_confirm(key: int) -> bool:
    return key in (10, 13, curses.KEY_ENTER)


def is_cancel(key: int) -> bool:
    return key in (ord("q"), 27)


def is_up(key: int) -> bool:
    return key in (curses.KEY_UP, ord("k"))


def is_down(key: int) -> bool:
    return key in (curses.KEY_DOWN, ord("j"))


def is_mouse(key: int) -> bool:
    """True when *key* is the curses mouse event token."""
    return key == getattr(curses, "KEY_MOUSE", -1)
