"""Application lifecycle for the Turbo C++ inspired setup IDE."""

from __future__ import annotations

import curses
import sys

from flossware_setup.tui.ide import run as run_ide
from flossware_setup.tui.input import enable_mouse
from flossware_setup.tui.widgets import palette


def load_theme(name: str):
    """Load an optional FlossWare theme without installing during startup."""
    try:
        from curses_themes import ThemeManager
        return ThemeManager.load(name)
    except Exception:  # noqa: BLE001 - optional dependency
        return None


def run(stdscr, theme_name: str | None = None) -> None:
    """Run the persistent full-screen configuration IDE."""
    from flossware_setup.config_control import load_theme as load_persisted_theme
    from flossware_setup.tui.themes import normalize_theme

    curses.curs_set(0)
    stdscr.keypad(True)
    chosen = normalize_theme(theme_name) if theme_name else load_persisted_theme()
    palette(chosen)
    try:
        stdscr.bkgd(" ", curses.color_pair(5))
    except curses.error:
        pass
    enable_mouse()
    load_theme(chosen)  # optional external package
    run_ide(stdscr)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    theme_name = None
    if "--help" in args or "-h" in args:
        print("Usage: flossware-setup [--theme NAME]")
        print("       flossware-ai tui [--theme NAME]")
        print("       python3 scripts/setup.py [--theme NAME]")
        return 0
    for i, arg in enumerate(args):
        if arg == "--theme" and i + 1 < len(args):
            theme_name = args[i + 1]
        elif arg.startswith("--theme="):
            theme_name = arg.split("=", 1)[1]
    if not sys.stdout.isatty():
        print("Non-interactive environment. Use scripts/install.sh instead.", file=sys.stderr)
        return 1
    try:
        curses.wrapper(lambda win: run(win, theme_name))
    except (KeyboardInterrupt, curses.error) as exc:
        print(f"Setup cancelled: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Setup failed: {exc}", file=sys.stderr)
        return 1
    return 0
