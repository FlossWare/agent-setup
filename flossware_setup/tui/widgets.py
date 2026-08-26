"""Reusable curses rendering helpers."""

from __future__ import annotations

import curses

from flossware_setup.tui.input import is_cancel, is_confirm, is_down, is_up, mouse_position, primary_click
from flossware_setup.tui.status import item_status


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
            win.addnstr(y, max(0, x), text, max(0, w - max(0, x) - 1), curses.color_pair(pair) | attr)
        except curses.error:
            pass


def header(win, title: str, step: int | None = None) -> int:
    win.erase()
    _, w = win.getmaxyx()
    label = f" FlossWare AI  |  {title} " if step is None else f" FlossWare AI  |  {step}/5  {title} "
    add(win, 1, 2, "=" * min(max(10, w - 4), 72), 1)
    add(win, 2, 2, label, 1, curses.A_BOLD)
    add(win, 3, 2, "=" * min(max(10, w - 4), 72), 1)
    return 5


def _toggle(selected_set: set[int], index: int) -> None:
    if index in selected_set:
        selected_set.remove(index)
    else:
        selected_set.add(index)


def _handle_mouse_row(click_y: int, content_y: int, visible: int, multi: bool, selected_set: set[int], cursor: int) -> tuple[int, set[int], bool]:
    clicked_index = click_y - content_y
    if not (0 <= clicked_index < visible):
        return cursor, selected_set, False
    cursor = clicked_index
    if multi:
        _toggle(selected_set, cursor)
        return cursor, selected_set, False
    return cursor, selected_set, True


def _dispatch_menu_key(key: int, multi: bool, selected_set: set[int], cursor: int, item_count: int) -> tuple[int, set[int], str]:
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


def _hover_cursor(y: int, content_y: int, visible: int, current: int) -> int:
    index = y - content_y
    return index if 0 <= index < visible else current


def _render_menu_frame(win, title: str, items: list[tuple[str, str]], multi: bool, selected_set: set[int], cursor: int) -> tuple[int, int]:
    y = header(win, title)
    h, _ = win.getmaxyx()
    visible = min(len(items), max(0, h - y - 4))
    for i, (name, desc) in enumerate(items[:visible]):
        active = i == cursor
        chosen = i in selected_set or (not multi and active)
        add(win, y + i, 2, "> " if active else "  ", 1 if active else 5, curses.A_BOLD)
        add(win, y + i, 5, _item_mark(multi, i, cursor, selected_set), 2 if chosen else 3)
        add(win, y + i, 10, name, 1 if active else 5, curses.A_BOLD if active else 0)
        add(win, y + i, 10 + len(name) + 3, desc, 5)
    status = item_status(*items[cursor]) if items and 0 <= cursor < len(items) else "STATUS: ready"
    add(win, h - 3, 2, status, 1, curses.A_BOLD)
    add(win, h - 2, 2, "↑/↓/mouse move  Space/click toggle  Enter confirm  a all  n none  q quit", 6)
    win.refresh()
    return y, visible


def _menu_result(multi: bool, selected_set: set[int], cursor: int) -> list[int] | int:
    return sorted(selected_set) if multi else cursor


def menu(win, title: str, items: list[tuple[str, str]], selected: list[int] | None = None, multi: bool = True) -> list[int] | int | None:
    """Interactive menu with keyboard, click, and hover status support."""
    selected_set = set(selected or [])
    cursor = 0
    while True:
        content_y, visible = _render_menu_frame(win, title, items, multi, selected_set, cursor)
        key = win.getch()
        if key == curses.KEY_MOUSE:
            click = primary_click()
            if click is not None:
                cursor, selected_set, done = _handle_mouse_row(click[1], content_y, visible, multi, selected_set, cursor)
                if done:
                    return cursor
                continue
            position = mouse_position()
            if position is not None:
                new_cursor = _hover_cursor(position[1], content_y, visible, cursor)
                if new_cursor != cursor:
                    cursor = new_cursor
                continue
        cursor, selected_set, action = _dispatch_menu_key(key, multi, selected_set, cursor, len(items))
        if action == "confirm":
            return _menu_result(multi, selected_set, cursor)
        if action == "cancel":
            return None


def _redraw_input_line(win, row: int, buffer: str, cursor: int) -> None:
    _, w = win.getmaxyx()
    max_width = max(1, w - 3)
    display = buffer[:max_width]
    try:
        win.move(row, 2)
        win.clrtoeol()
    except curses.error:
        pass
    add(win, row, 2, display, 5)
    cursor_x = 2 + min(max(0, cursor), len(display))
    try:
        win.move(row, min(cursor_x, w - 2))
    except curses.error:
        pass
    win.refresh()


def _apply_text_input_key(key: int, buffer: list[str], cursor: int) -> tuple[list[str], int, str]:
    if key in (10, 13, curses.KEY_ENTER):
        return buffer, cursor, "confirm"
    if key == 27:
        return buffer, cursor, "cancel"
    if key in (curses.KEY_BACKSPACE, 127, 8):
        if cursor > 0:
            del buffer[cursor - 1]
            cursor -= 1
        return buffer, cursor, "continue"
    if key == curses.KEY_DC:
        if cursor < len(buffer):
            del buffer[cursor]
        return buffer, cursor, "continue"
    if key == curses.KEY_LEFT:
        return buffer, max(0, cursor - 1), "continue"
    if key == curses.KEY_RIGHT:
        return buffer, min(len(buffer), cursor + 1), "continue"
    if key == curses.KEY_HOME:
        return buffer, 0, "continue"
    if key == curses.KEY_END:
        return buffer, len(buffer), "continue"
    if 32 <= key <= 126 and len(buffer) < 200:
        buffer.insert(cursor, chr(key))
        return buffer, cursor + 1, "continue"
    return buffer, cursor, "continue"


def text_input(win, prompt: str, default: str = "") -> str:
    curses.noecho()
    curses.curs_set(1)
    y = header(win, "Input")
    add(win, y, 2, prompt, 1)
    add(win, y + 1, 2, "Enter confirm  Esc keep default / cancel edit", 6)
    row = y + 3
    buffer = list(default)
    cursor = len(buffer)
    _redraw_input_line(win, row, "".join(buffer), cursor)
    try:
        while True:
            buffer, cursor, action = _apply_text_input_key(win.getch(), buffer, cursor)
            if action == "confirm":
                text = "".join(buffer).strip()
                return text if text else default
            if action == "cancel":
                return default
            _redraw_input_line(win, row, "".join(buffer), cursor)
    except curses.error:
        return default
    finally:
        curses.curs_set(0)
