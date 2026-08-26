"""Interactive configuration-contract screen."""
from __future__ import annotations

import curses

from flossware_setup.config_control import DEFAULT_CONSTRAINTS, load_order, save_order
from flossware_setup.config_contract import OrderingError, reorder
from flossware_setup.tui.input import is_cancel, is_down, is_up, mouse_event
from flossware_setup.tui.widgets import add, header


def configuration_contract_screen(win) -> None:
    """Show effective policy and allow safe menu reordering with keyboard/mouse."""
    order = load_order()
    cursor = 0
    while True:
        y = header(win, "Configuration Contract")
        h, _ = win.getmaxyx()
        add(win, y, 2, "Layer precedence: defaults -> system -> user -> profile -> project -> environment -> CLI", 5)
        add(win, y + 1, 2, "Profile: redhat-cost-conscious | Provider: Anthropic | Budget: $300 hard ceiling", 5)
        add(win, y + 3, 2, "Menu order", 1, curses.A_BOLD)
        visible = min(len(order), max(1, h - y - 7))
        for i, item in enumerate(order[:visible]):
            active = i == cursor
            add(win, y + 4 + i, 2, ">" if active else " ", 1 if active else 5, curses.A_BOLD)
            add(win, y + 4 + i, 5, item, 1 if active else 5, curses.A_BOLD if active else 0)
        add(win, h - 3, 2, "Up/Down or mouse: select   Ctrl-P/Ctrl-V: reorder   Enter: save   q/Esc: back", 6)
        add(win, h - 2, 2, f"STATUS: {order[cursor]} | ordering constraints enforced | secrets hidden", 1, curses.A_BOLD)
        win.refresh()
        key = win.getch()
        if key == curses.KEY_MOUSE:
            event = mouse_event()
            if event is None:
                continue
            _x, mouse_y, bstate = event
            idx = mouse_y - (y + 4)
            if 0 <= idx < visible:
                cursor = idx
                if bstate & getattr(curses, "BUTTON1_CLICKED", 0):
                    continue
            continue
        if is_cancel(key):
            return
        if is_up(key):
            cursor = max(0, cursor - 1)
            continue
        if is_down(key):
            cursor = min(len(order) - 1, cursor + 1)
            continue
        if key == 16:  # Ctrl-P: move up
            try:
                order = reorder(order, order[cursor], -1, DEFAULT_CONSTRAINTS)
                cursor = max(0, cursor - 1)
            except OrderingError:
                pass
            continue
        if key == 22:  # Ctrl-V: move down
            try:
                order = reorder(order, order[cursor], 1, DEFAULT_CONSTRAINTS)
                cursor = min(len(order) - 1, cursor + 1)
            except OrderingError:
                pass
            continue
        if key in (10, 13, curses.KEY_ENTER):
            save_order(order)
            add(win, h - 4, 2, "Saved.", 2)
            win.refresh()
