"""Small UX fixes layered over the curses IDE.

Keeps the core IDE intact while making user-created profiles discoverable and
ensuring popup windows use the active palette instead of curses' default black
background.
"""
from __future__ import annotations

import curses


def install_tui_fixes() -> None:
    """Install the profile-creation menu entry and repaint-safe popups."""
    from flossware_setup.tui import ide

    # Make profile creation discoverable. The implementation already exists in
    # ide.create_profile(), it simply wasn't exposed from a menu.
    config_items = list(ide.ITEMS.get("Config", ()))
    if "Create Profile" not in config_items:
        try:
            insert_at = config_items.index("Profiles") + 1
        except ValueError:
            insert_at = 0
        config_items.insert(insert_at, "Create Profile")
        ide.ITEMS["Config"] = tuple(config_items)

    if getattr(ide, "_ux_fixes_installed", False):
        return

    original_popup = ide._popup
    original_close = ide._close
    parents: dict[int, object] = {}

    def popup(win, top, left, height, width, title):
        panel = original_popup(win, top, left, height, width, title)
        parents[id(panel)] = win
        # The original helper used pair 0, which is commonly a black terminal
        # background. Pair 5 is the application's normal background palette.
        try:
            panel.bkgd(" ", curses.color_pair(5))
            panel.erase()
            panel.noutrefresh()
            curses.doupdate()
            panel.border()
            panel.addstr(0, 2, f" {title} ", curses.A_BOLD)
        except curses.error:
            pass
        return panel

    def close(panel):
        parent = parents.pop(id(panel), None)
        original_close(panel)
        if parent is not None:
            try:
                parent.touchwin()
                parent.noutrefresh()
                curses.doupdate()
            except curses.error:
                pass

    ide._popup = popup
    ide._close = close
    ide._ux_fixes_installed = True
