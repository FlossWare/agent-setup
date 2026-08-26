"""Turbo C++ inspired full-screen configuration IDE."""
from __future__ import annotations

import curses
from pathlib import Path

from flossware_setup.config_control import effective_config, state_dir
from flossware_setup.tui.input import enable_mouse, mouse_event
from flossware_setup.tui.widgets import add, palette

PROFILES = ("personal", "redhat", "redhat-cost-conscious")
MENU = ("File", "Edit", "View", "Config", "Models", "Agents", "Optimize", "Help")
MENU_ITEMS = {
    "File": ("Save", "Exit"),
    "Edit": ("Reorder menus", "Reset layout"),
    "View": ("Profiles", "Configuration", "Status"),
    "Config": ("Profiles", "Validate", "Explain"),
    "Models": ("Discover models", "Refresh models"),
    "Agents": ("Agent configuration",),
    "Optimize": ("Thompson Sampling", "Genetic Optimizer"),
    "Help": ("Keyboard and mouse", "About"),
}


def _profile_path() -> Path:
    return state_dir() / "profile"


def load_active_profile() -> str:
    try:
        value = _profile_path().read_text(encoding="utf-8").strip()
        return value if value in PROFILES else "personal"
    except OSError:
        return "personal"


def save_active_profile(name: str) -> None:
    if name not in PROFILES:
        raise ValueError(f"unknown profile: {name}")
    state_dir().mkdir(parents=True, exist_ok=True)
    _profile_path().write_text(name + "\n", encoding="utf-8")


def _draw_box(win, top: int, left: int, bottom: int, right: int, title: str) -> None:
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


def _menu_x_positions() -> list[tuple[str, int, int]]:
    x = 1
    result = []
    for name in MENU:
        start = x
        x += len(name) + 2
        result.append((name, start, x - 1))
    return result


def _popup_menu(win, name: str, x: int) -> str | None:
    items = MENU_ITEMS.get(name, ())
    h, w = win.getmaxyx()
    width = min(max((len(i) for i in items), default=10) + 4, max(12, w - x - 1))
    height = len(items) + 2
    if height >= h:
        height = max(3, h - 2)
    top = 1
    cursor = 0
    while True:
        try:
            win.erase()
            # Redraw the main shell behind the dropdown.
            _draw_main(win)
            for i, item in enumerate(items[: height - 2]):
                add(win, top + 1 + i, x, f" {'> ' if i == cursor else '  '}{item}", 2 if i == cursor else 5,
                    curses.A_BOLD if i == cursor else 0)
            win.refresh()
            key = win.getch()
        except curses.error:
            return None
        if key == curses.KEY_MOUSE:
            event = mouse_event()
            if not event:
                continue
            mx, my, bstate = event
            if bstate & (getattr(curses, "BUTTON1_CLICKED", 0) | getattr(curses, "BUTTON1_PRESSED", 0)):
                if x <= mx < x + width and top + 1 <= my < top + 1 + len(items):
                    return items[my - top - 1]
                if my == 0:
                    for menu_name, left, right in _menu_x_positions():
                        if left <= mx <= right:
                            return _popup_menu(win, menu_name, left)
                return None
        elif key in (curses.KEY_UP, ord("k")):
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            cursor = min(max(0, len(items) - 1), cursor + 1)
        elif key in (10, 13, curses.KEY_ENTER):
            return items[cursor] if items else None
        elif key == 27:
            return None


def profile_selector(win) -> str | None:
    current = load_active_profile()
    cursor = PROFILES.index(current)
    enable_mouse()
    while True:
        win.erase()
        h, w = win.getmaxyx()
        add(win, 1, 2, "FlossWare AI  |  Select Profile", 1, curses.A_BOLD)
        _draw_box(win, 3, 4, min(h - 4, 9), min(w - 5, 52), "Profiles")
        for i, profile in enumerate(PROFILES):
            marker = ">" if i == cursor else " "
            label = profile.replace("-", " ").title()
            add(win, 5 + i, 7, f"{marker} {label}", 2 if i == cursor else 5, curses.A_BOLD if i == cursor else 0)
        add(win, h - 2, 2, "Enter Select   Esc Cancel   Up/Down Navigate   Mouse Click Select", 6)
        win.refresh()
        key = win.getch()
        if key == curses.KEY_MOUSE:
            event = mouse_event()
            if event:
                _x, y, bstate = event
                if bstate & (getattr(curses, "BUTTON1_CLICKED", 0) | getattr(curses, "BUTTON1_PRESSED", 0)):
                    if 5 <= y < 5 + len(PROFILES):
                        cursor = y - 5
                        save_active_profile(PROFILES[cursor])
                        return PROFILES[cursor]
        elif key in (curses.KEY_UP, ord("k")):
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            cursor = min(len(PROFILES) - 1, cursor + 1)
        elif key in (10, 13, curses.KEY_ENTER):
            save_active_profile(PROFILES[cursor])
            return PROFILES[cursor]
        elif key == 27:
            return None


def _effective_profile_config(profile: str) -> dict[str, object]:
    try:
        return effective_config(profile).resolve()
    except Exception:
        return {}


def _draw_main(win) -> None:
    h, w = win.getmaxyx()
    add(win, 0, 0, " " + "  ".join(MENU), 1, curses.A_BOLD)
    add(win, 1, 0, "-" * max(1, w - 1), 1)


def _run_menu_action(win, action: str | None, active: str) -> str | None:
    if action in {"Profiles", "Profile"}:
        return profile_selector(win)
    if action == "Exit":
        return "__EXIT__"
    return None


def run(win) -> None:
    palette()
    win.keypad(True)
    enable_mouse()
    active = load_active_profile()
    while True:
        win.erase()
        h, w = win.getmaxyx()
        config = _effective_profile_config(active)
        _draw_main(win)
        left = max(20, min(29, w // 4))
        _draw_box(win, 2, 1, max(3, h - 5), left, "Profiles")
        for i, profile in enumerate(PROFILES):
            marker = ">" if profile == active else " "
            add(win, 4 + i, 3, f"{marker} {profile.replace('-', ' ').title()}", 2 if profile == active else 5,
                curses.A_BOLD if profile == active else 0)
        panel_left = left + 2
        _draw_box(win, 2, panel_left, max(3, h - 5), max(panel_left + 2, w - 2), "Configuration")
        fields = [
            ("Provider", config.get("provider", "unknown")),
            ("Budget", f"${float(config.get('budget.monthly', 0)):.2f} / month"),
            ("Optimizer", config.get("optimization.strategy", "unknown")),
            ("Personal accounts", "allowed" if config.get("policy.allow_personal_accounts") else "blocked"),
            ("Provider fallback", "allowed" if config.get("policy.allow_provider_fallback") else "blocked"),
        ]
        for i, (name, value) in enumerate(fields):
            add(win, 4 + i, panel_left + 3, f"{name:<22} {value}", 5)
        add(win, h - 4, 2, f"Profile: {active.upper()}   |   Provider: {config.get('provider', 'unknown')}   |   READY", 1, curses.A_BOLD)
        add(win, h - 3, 2, "Click menus/profile   Alt+letter menus   Arrows navigate   Enter select", 6)
        add(win, h - 2, 2, "Function keys are optional and never required   |   Esc/Q Exit", 6)
        win.refresh()
        key = win.getch()
        if key == curses.KEY_MOUSE:
            event = mouse_event()
            if event:
                x, y, bstate = event
                clicked = getattr(curses, "BUTTON1_CLICKED", 0) | getattr(curses, "BUTTON1_PRESSED", 0)
                if bstate & clicked:
                    if y == 0:
                        for menu_name, left_x, right_x in _menu_x_positions():
                            if left_x <= x <= right_x:
                                action = _popup_menu(win, menu_name, left_x)
                                chosen = _run_menu_action(win, action, active)
                                if chosen == "__EXIT__":
                                    return
                                if chosen:
                                    active = chosen
                                break
                    elif 4 <= y < 4 + len(PROFILES) and 2 <= x < left:
                        chosen = profile_selector(win)
                        if chosen:
                            active = chosen
                    elif h - 4 <= y <= h - 3:
                        chosen = profile_selector(win)
                        if chosen:
                            active = chosen
            continue
        # Avoid F-key bindings entirely. KDE may own them; the TUI remains fully usable.
        if key in (27, ord("q"), ord("Q")):
            return
        if key in (ord("p"), ord("P")):
            chosen = profile_selector(win)
            if chosen:
                active = chosen
            continue
        # Alt+menu support is terminal-dependent; curses commonly reports ESC + letter.
        if key == 27:
            continue


def main() -> int:
    curses.wrapper(run)
    return 0
