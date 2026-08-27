"""Interactive configuration validation popup for the curses TUI."""
from __future__ import annotations

import curses

from flossware_setup.config_control import validate_effective_config


def validate_popup(win):
    """Validate the active profile and display the result in a modal popup."""
    from flossware_setup.tui.ide import _active, _close, _popup

    profile, _source = _active()
    try:
        validate_effective_config(profile)
        ok = True
        lines = [f"Profile: {profile}", "Configuration validation: PASS"]
    except Exception as exc:
        ok = False
        lines = [f"Profile: {profile}", "Configuration validation: FAIL", str(exc)]

    h, w = win.getmaxyx()
    height = min(max(8, len(lines) + 5), h - 2)
    width = min(max(46, max(len(line) for line in lines) + 6), w - 4)
    top = max(1, (h - height) // 2)
    left = max(1, (w - width) // 2)
    panel = _popup(win, top, left, height, width, "Validate Configuration")
    try:
        for i, line in enumerate(lines):
            panel.addnstr(2 + i, 2, line, width - 4, curses.A_BOLD if i == 1 else 0)
        panel.addnstr(height - 2, 2, "Enter/Esc close", width - 4)
        panel.noutrefresh()
        curses.doupdate()
        while True:
            key = panel.getch()
            if key in (10, 13, curses.KEY_ENTER, 27, ord("q"), ord("Q"), curses.KEY_MOUSE):
                break
    except curses.error:
        pass
    finally:
        _close(panel)
    return ok
