"""Reusable curses rendering helpers."""

from __future__ import annotations

import curses

from flossware_setup.tui.input import (
    is_cancel,
    is_confirm,
    is_down,
    is_up,
    primary_click,
)


def palette() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)


def add(win, y: int, x: int, text: str, pair: int = 5, attr: int = 0) -> None:
    h, w = win.getmaxyx()
    if 0 <= y < h and x < w - 1:
        try:
            win.addnstr(
                y,
                max(0, x),
                text,
                max(0, w - max(0, x) - 1),
                curses.color_pair(pair) | attr,
            )
        except curses.error:
            pass


def header(win, title: str, step: int | None = None) -> int:
    """Draw the standard header and return the first content row."""
    win.erase()
    _, w = win.getmaxyx()
    label = (
        f" FlossWare AI  |  {title} "
        if step is None
        else f" FlossWare AI  |  {step}/5  {title} "
    )
    add(win, 1, 2, "=" * min(max(10, w - 4), 72), 1)
    add(win, 2, 2, label, 1, curses.A_BOLD)
    add(win, 3, 2, "=" * min(max(10, w - 4), 72), 1)
    return 5


def _toggle(selected_set: set[int], index: int) -> None:
    if index in selected_set:
        selected_set.remove(index)
    else:
        selected_set.add(index)


def _handle_mouse_row(
    click_y: int,
    content_y: int,
    visible: int,
    multi: bool,
    selected_set: set[int],
    cursor: int,
) -> tuple[int, set[int], bool]:
    """Update selection from a mouse row click. Returns (cursor, selected, done)."""
    clicked_index = click_y - content_y
    if not (0 <= clicked_index < visible):
        return cursor, selected_set, False
    cursor = clicked_index
    if multi:
        _toggle(selected_set, cursor)
        return cursor, selected_set, False
    return cursor, selected_set, True


def _dispatch_menu_key(
    key: int,
    multi: bool,
    selected_set: set[int],
    cursor: int,
    item_count: int,
) -> tuple[int, set[int], str]:
    """Handle a non-mouse key. Returns (cursor, selected, action)."""
    if is_up(key):
        return max(0, cursor - 1), selected_set, "continue"
    if is_down(key):
        return min(max(0, item_count - 1), cursor + 1), selected_set, "continue"
    if multi and key == ord(" "):
        _toggle(selected_set, cursor)
        return cursor, selected_set, "continue"
    if multi and key == ord("a"):
        return cursor, set(range(item_count)), "continue"
    if multi and key == ord("n"):
        return cursor, set(), "continue"
    if is_confirm(key):
        return cursor, selected_set, "confirm"
    if is_cancel(key):
        return cursor, selected_set, "cancel"
    return cursor, selected_set, "continue"


def _item_mark(multi: bool, index: int, cursor: int, selected_set: set[int]) -> str:
    if multi:
        return "[x]" if index in selected_set else "[ ]"
    return "(o)" if index == cursor else "( )"


def _render_menu_frame(
    win,
    title: str,
    items: list[tuple[str, str]],
    multi: bool,
    selected_set: set[int],
    cursor: int,
) -> tuple[int, int]:
    """Draw the menu and return (content_y, visible_count)."""
    y = header(win, title)
    h, _ = win.getmaxyx()
    visible = min(len(items), max(0, h - y - 3))
    for i, (name, desc) in enumerate(items[:visible]):
        active = i == cursor
        chosen = i in selected_set or (not multi and active)
        add(win, y + i, 2, "> " if active else "  ", 1 if active else 5, curses.A_BOLD)
        add(win, y + i, 5, _item_mark(multi, i, cursor, selected_set), 2 if chosen else 3)
        add(win, y + i, 10, name, 1 if active else 5, curses.A_BOLD if active else 0)
        add(win, y + i, 10 + len(name) + 3, desc, 5)
    add(
        win,
        h - 2,
        2,
        "↑/↓ navigate  Space/click toggle  Enter confirm  a all  n none  q quit",
        6,
    )
    win.refresh()
    return y, visible


def _menu_result(multi: bool, selected_set: set[int], cursor: int) -> list[int] | int:
    return sorted(selected_set) if multi else cursor


def menu(
    win,
    title: str,
    items: list[tuple[str, str]],
    selected: list[int] | None = None,
    multi: bool = True,
) -> list[int] | int | None:
    """Interactive single- or multi-select menu with keyboard and mouse support.

    Returns sorted selected indexes (multi), a single index (single), or None on cancel.
    """
    selected_set = set(selected or [])
    cursor = 0
    while True:
        content_y, visible = _render_menu_frame(
            win, title, items, multi, selected_set, cursor
        )
        key = win.getch()
        if key == curses.KEY_MOUSE:
            click = primary_click()
            if click is None:
                continue
            cursor, selected_set, done = _handle_mouse_row(
                click[1], content_y, visible, multi, selected_set, cursor
            )
            if done:
                return cursor
            continue
        cursor, selected_set, action = _dispatch_menu_key(
            key, multi, selected_set, cursor, len(items)
        )
        if action == "confirm":
            return _menu_result(multi, selected_set, cursor)
        if action == "cancel":
            return None


def text_input(win, prompt: str, default: str = "") -> str:
    """Prompt for a single line of text."""
    curses.echo()
    curses.curs_set(1)
    y = header(win, "Input")
    add(win, y, 2, prompt, 1)
    add(win, y + 2, 2, default, 5)
    win.move(y + 2, 2 + len(default))
    win.refresh()
    try:
        raw = win.getstr(y + 2, 2, 200)
        text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        text = text.strip() or default
    except (curses.error, UnicodeDecodeError, OSError):
        text = default
    finally:
        curses.noecho()
        curses.curs_set(0)
    return text
