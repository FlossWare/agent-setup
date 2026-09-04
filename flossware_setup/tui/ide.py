"""Turbo C++ inspired full-screen configuration IDE."""
from __future__ import annotations

import curses

from curses_tui import build_window_manager, validate

from flossware_setup.config_control import (
    available_profiles,
    effective_config,
    load_active_profile,
    save_active_profile,
)
from flossware_setup.tui.contract import build_document
from flossware_setup.tui.input import is_mouse, mouse_event, resolve_list_mouse
from flossware_setup.tui.widgets import add, palette

MENU = ("File", "Edit", "View", "Config", "Models", "Agents", "Optimize", "Help")
ITEMS = {
    "File": ("Exit",),
    "Edit": ("Reorder menus",),
    "View": ("Profiles", "Directory Bindings", "Configuration", "Theme"),
    "Config": ("Profiles", "Create Profile", "Directory Bindings", "Validate"),
    "Models": ("Select Model",),
    "Agents": ("Select Agent",),
    "Optimize": ("Settings",),
    "Help": ("About",),
}


def _popup(win: object, top: int, left: int, height: int, width: int, title: str):
    h, w = win.getmaxyx()
    height = max(3, min(int(height), max(3, h - 2)))
    width = max(10, min(int(width), max(10, w - 2)))
    top = max(0, min(int(top), max(0, h - height)))
    left = max(0, min(int(left), max(0, w - width)))
    panel = curses.newwin(height, width, top, left)
    panel.keypad(True)
    try:
        panel.bkgd(" ")
        panel.erase()
        panel.border()
        panel.addnstr(0, 2, f" {title} ", max(0, width - 4), curses.A_BOLD)
        panel.noutrefresh()
        curses.doupdate()
    except curses.error:
        pass
    return panel


def _close(panel: object) -> None:
    try:
        panel.erase()
        panel.noutrefresh()
        curses.doupdate()
    except curses.error:
        pass


def profile_selector(win: object) -> str | None:
    """Select a profile using the existing keyboard/mouse interaction model."""
    profiles = list(available_profiles())
    current = load_active_profile()
    cursor = profiles.index(current) if current in profiles else 0
    origin_y = 5
    while True:
        profiles = list(available_profiles())
        if not profiles:
            return None
        cursor = min(cursor, len(profiles) - 1)
        win.erase()
        h, w = win.getmaxyx()
        add(win, 1, 2, "FlossWare AI  |  Select Profile", 1, curses.A_BOLD)
        _draw_box(win, 3, 4, min(h - 4, 9), min(w - 5, 52), "Profiles")
        for i, profile in enumerate(profiles):
            add(
                win,
                origin_y + i,
                7,
                (">" if i == cursor else " ") + " " + profile.replace("-", " ").title(),
                2 if i == cursor else 5,
                curses.A_BOLD if i == cursor else 0,
            )
        add(win, h - 2, 2, "Enter/click Select   Esc Cancel   Up/Down Navigate", 6)
        win.refresh()
        key = win.getch()
        if is_mouse(key):
            action = resolve_list_mouse(mouse_event(), origin_y=origin_y, count=len(profiles))
            if action is None:
                continue
            kind, index = action
            cursor = index
            if kind == "activate":
                save_active_profile(profiles[cursor])
                return profiles[cursor]
            continue
        if key in (curses.KEY_UP, ord("k")):
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            cursor = min(len(profiles) - 1, cursor + 1)
        elif key in (10, 13, curses.KEY_ENTER):
            save_active_profile(profiles[cursor])
            return profiles[cursor]
        elif key == 27:
            return None


def _draw_box(win: object, top: int, left: int, bottom: int, right: int, title: str) -> None:
    try:
        win.addch(top, left, curses.ACS_ULCORNER)
        win.hline(top, left + 1, curses.ACS_HLINE, max(0, right - left - 1))
        win.addch(top, right, curses.ACS_URCORNER)
        win.vline(top + 1, left, curses.ACS_VLINE, max(0, bottom - top - 1))
        win.vline(top + 1, right, curses.ACS_VLINE, max(0, bottom - top - 1))
        win.addch(bottom, left, curses.ACS_LLCORNER)
        win.hline(bottom, left + 1, curses.ACS_HLINE, max(0, right - left - 1))
        win.addch(bottom, right, curses.ACS_LRCORNER)
        add(win, top, left + 2, f" {title} ", 1, curses.A_BOLD)
    except curses.error:
        pass


def _effective_profile_config(profile: str) -> dict[str, object]:
    try:
        return effective_config(profile).resolve()
    except Exception:
        return {}


def _render_contract(win: object, profile: str, config: dict[str, object]) -> None:
    """Validate and render the canonical 1.0 document through curses-tui."""
    h, w = win.getmaxyx()
    document = build_document(profile, config, list(available_profiles()))
    validate(document)
    manager = build_window_manager(document, w, h)
    manager.draw(win)
    add(
        win,
        max(0, h - 4),
        2,
        f"Profile: {profile.upper()}   |   Provider: {config.get('provider', 'unknown')}   |   READY",
        1,
        curses.A_BOLD,
    )
    add(win, max(0, h - 3), 2, "F7 Profiles   F6 Models   F8 Optimize   F2 Save   F10 Menu", 6)
    add(win, max(0, h - 2), 2, "Mouse/Arrows Navigate   Enter Select   Esc Exit", 6)


def run(win: object) -> None:
    """Run the Setup TUI using the canonical TUI Schema 1.0 contract."""
    palette()
    win.keypad(True)
    active = load_active_profile()
    while True:
        win.erase()
        config = _effective_profile_config(active)
        _render_contract(win, active, config)
        win.refresh()
        key = win.getch()
        if is_mouse(key):
            names = list(available_profiles())
            action = resolve_list_mouse(mouse_event(), origin_y=4, count=len(names))
            if action is not None:
                kind, index = action
                if 0 <= index < len(names):
                    active = names[index]
                    if kind == "activate":
                        save_active_profile(active)
            continue
        if key in (curses.KEY_F7, ord("p"), ord("P")):
            chosen = profile_selector(win)
            if chosen:
                active = chosen
        elif key in (27, ord("q"), ord("Q")):
            return


def main() -> int:
    curses.wrapper(run)
    return 0
