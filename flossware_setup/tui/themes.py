"""Selectable TUI color themes (persisted under the FlossWare state root only)."""

from __future__ import annotations

import curses
from typing import Mapping

# Logical pair ids used by widgets / ide.
PAIR_TITLE = 1
PAIR_OK = 2
PAIR_WARN = 3
PAIR_ERROR = 4
PAIR_TEXT = 5
PAIR_MUTED = 6
PAIR_HIGHLIGHT = 7
PAIR_BORDER = 8
PAIR_STATUS = 9

# name -> list of (pair_id, fg, bg); -1 means default terminal color.
_THEME_PAIRS: dict[str, list[tuple[int, int, int]]] = {
    "turbo": [
        (PAIR_TITLE, curses.COLOR_YELLOW, curses.COLOR_BLUE),
        (PAIR_OK, curses.COLOR_GREEN, curses.COLOR_BLUE),
        (PAIR_WARN, curses.COLOR_YELLOW, curses.COLOR_BLUE),
        (PAIR_ERROR, curses.COLOR_RED, curses.COLOR_BLUE),
        (PAIR_TEXT, curses.COLOR_WHITE, curses.COLOR_BLUE),
        (PAIR_MUTED, curses.COLOR_CYAN, curses.COLOR_BLUE),
        (PAIR_HIGHLIGHT, curses.COLOR_BLACK, curses.COLOR_CYAN),
        (PAIR_BORDER, curses.COLOR_WHITE, curses.COLOR_BLUE),
        (PAIR_STATUS, curses.COLOR_BLACK, curses.COLOR_CYAN),
    ],
    "dbase4": [
        (PAIR_TITLE, curses.COLOR_GREEN, curses.COLOR_BLACK),
        (PAIR_OK, curses.COLOR_GREEN, curses.COLOR_BLACK),
        (PAIR_WARN, curses.COLOR_YELLOW, curses.COLOR_BLACK),
        (PAIR_ERROR, curses.COLOR_RED, curses.COLOR_BLACK),
        (PAIR_TEXT, curses.COLOR_GREEN, curses.COLOR_BLACK),
        (PAIR_MUTED, curses.COLOR_WHITE, curses.COLOR_BLACK),
        (PAIR_HIGHLIGHT, curses.COLOR_BLACK, curses.COLOR_GREEN),
        (PAIR_BORDER, curses.COLOR_GREEN, curses.COLOR_BLACK),
        (PAIR_STATUS, curses.COLOR_BLACK, curses.COLOR_GREEN),
    ],
    "classic": [
        (PAIR_TITLE, curses.COLOR_WHITE, curses.COLOR_BLACK),
        (PAIR_OK, curses.COLOR_WHITE, curses.COLOR_BLACK),
        (PAIR_WARN, curses.COLOR_WHITE, curses.COLOR_BLACK),
        (PAIR_ERROR, curses.COLOR_WHITE, curses.COLOR_BLACK),
        (PAIR_TEXT, curses.COLOR_WHITE, curses.COLOR_BLACK),
        (PAIR_MUTED, curses.COLOR_WHITE, curses.COLOR_BLACK),
        (PAIR_HIGHLIGHT, curses.COLOR_BLACK, curses.COLOR_WHITE),
        (PAIR_BORDER, curses.COLOR_WHITE, curses.COLOR_BLACK),
        (PAIR_STATUS, curses.COLOR_BLACK, curses.COLOR_WHITE),
    ],
    "monochrome": [
        (PAIR_TITLE, -1, -1),
        (PAIR_OK, -1, -1),
        (PAIR_WARN, -1, -1),
        (PAIR_ERROR, -1, -1),
        (PAIR_TEXT, -1, -1),
        (PAIR_MUTED, -1, -1),
        (PAIR_HIGHLIGHT, -1, -1),
        (PAIR_BORDER, -1, -1),
        (PAIR_STATUS, -1, -1),
    ],
}

THEME_NAMES: tuple[str, ...] = tuple(_THEME_PAIRS.keys())
THEME_LABELS: dict[str, str] = {
    "turbo": "Turbo C++ inspired (default)",
    "dbase4": "dBASE IV inspired",
    "classic": "Classic DOS",
    "monochrome": "Modern / monochrome",
}


def normalize_theme(name: str | None) -> str:
    key = (name or "turbo").strip().lower()
    if key in ("dbase", "dbase-iv"):
        return "dbase4"
    if key in ("modern",):
        return "monochrome"
    if key == "default":
        return "turbo"
    return key if key in _THEME_PAIRS else "turbo"


def apply_theme(name: str | None = None) -> str:
    """Initialize color pairs for *name*. Returns the effective theme id.

    Degrades gracefully when the terminal has fewer than 8 colors: pairs still
    initialize with defaults where possible; monochrome skips custom colors.
    """
    theme = normalize_theme(name)
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        return theme
    colors = 0
    try:
        colors = curses.COLORS
    except curses.error:
        colors = 0
    pairs = _THEME_PAIRS[theme]
    for pair_id, fg, bg in pairs:
        try:
            if colors < 8 or theme == "monochrome":
                curses.init_pair(pair_id, -1, -1)
            else:
                curses.init_pair(pair_id, fg, bg)
        except curses.error:
            try:
                curses.init_pair(pair_id, -1, -1)
            except curses.error:
                pass
    return theme


def theme_definitions() -> Mapping[str, str]:
    """Map theme id -> short human label (for docs and tests)."""
    return dict(THEME_LABELS)
