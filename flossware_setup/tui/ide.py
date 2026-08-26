"""Turbo C++ inspired full-screen configuration IDE."""
from __future__ import annotations

import curses
from pathlib import Path

from flossware_setup.config_control import effective_config, state_dir
from flossware_setup.tui.widgets import add, palette

PROFILES = ("personal", "redhat", "redhat-cost-conscious")
MENU = ("File", "Edit", "View", "Config", "Models", "Agents", "Optimize", "Help")


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


def profile_selector(win) -> str | None:
    current = load_active_profile()
    cursor = PROFILES.index(current)
    while True:
        win.erase()
        h, w = win.getmaxyx()
        add(win, 1, 2, "FlossWare AI  |  Select Profile", 1, curses.A_BOLD)
        _draw_box(win, 3, 4, min(h - 4, 9), min(w - 5, 52), "Profiles")
        for i, profile in enumerate(PROFILES):
            marker = ">" if i == cursor else " "
            label = profile.replace("-", " ").title()
            add(win, 5 + i, 7, f"{marker} {label}", 2 if i == cursor else 5, curses.A_BOLD if i == cursor else 0)
        add(win, h - 2, 2, "Enter Select   Esc Cancel   Up/Down Navigate", 6)
        win.refresh()
        key = win.getch()
        if key in (curses.KEY_UP, ord("k")):
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


def run(win) -> None:
    palette()
    win.keypad(True)
    active = load_active_profile()
    while True:
        win.erase()
        h, w = win.getmaxyx()
        config = _effective_profile_config(active)
        add(win, 0, 0, " File   Edit   View   Config   Models   Agents   Optimize   Help ", 1, curses.A_BOLD)
        add(win, 1, 0, "-" * max(1, w - 1), 1)
        left = max(18, min(27, w // 4))
        _draw_box(win, 2, 1, max(3, h - 5), left, "Profiles")
        for i, profile in enumerate(PROFILES):
            marker = ">" if profile == active else " "
            add(win, 4 + i, 3, f"{marker} {profile.replace('-', ' ').title()}", 2 if profile == active else 5, curses.A_BOLD if profile == active else 0)
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
        add(win, h - 3, 2, "F7 Profiles   F6 Models   F8 Optimize   F2 Save   F10 Menu", 6)
        add(win, h - 2, 2, "Mouse/Arrows Navigate   Enter Select   Esc Exit", 6)
        win.refresh()
        key = win.getch()
        if key in (curses.KEY_F7, ord("p"), ord("P")):
            chosen = profile_selector(win)
            if chosen:
                active = chosen
        elif key in (27, ord("q"), ord("Q")):
            return


def main() -> int:
    curses.wrapper(run)
    return 0
