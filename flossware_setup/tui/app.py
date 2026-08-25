"""Application lifecycle and navigation for the setup TUI."""

from __future__ import annotations

import curses
import sys
from typing import Optional

from flossware_setup.tui.input import enable_mouse
from flossware_setup.tui.screens import (
    build_screen,
    configure_wizard,
    credentials_screen,
    error_screen,
    review_screen,
    welcome_screen,
)
from flossware_setup.tui.widgets import menu, palette


def load_theme(name: str):
    """Load FlossWare themes when available, without installing during TUI startup."""
    try:
        from curses_themes import ThemeManager

        return ThemeManager.load(name)
    except Exception:  # noqa: BLE001 — optional dependency may raise anything
        return None


def run(stdscr, theme_name: str = "dark") -> None:
    curses.curs_set(0)
    stdscr.keypad(True)
    palette()
    enable_mouse()
    external_theme = load_theme(theme_name)

    if not welcome_screen(stdscr, theme_name, external_theme):
        return

    while True:
        choice = menu(
            stdscr,
            "Setup Control Center",
            [
                ("Review Current Configuration", "Inspect persisted project configuration"),
                ("Configure / Change Setup", "Select agents, capabilities and budget"),
                ("Provider Credentials", "View detected credential sources (names only)"),
                ("Exit", "Leave Setup"),
            ],
            multi=False,
        )
        if choice is None or choice == 3:
            return
        if choice == 0:
            review_screen(stdscr, ".")
        elif choice == 2:
            credentials_screen(stdscr)
        else:
            try:
                cfg = configure_wizard(stdscr)
                if cfg is None:
                    continue
                credentials_screen(stdscr)
                build_screen(stdscr, cfg)
                review_screen(stdscr, cfg.repo_dir)
            except (ValueError, OSError, RuntimeError, curses.error) as exc:
                error_screen(stdscr, str(exc))
            except Exception as exc:  # noqa: BLE001 — last-resort UI recovery
                error_screen(stdscr, str(exc))


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry for the setup TUI."""
    args = list(sys.argv[1:] if argv is None else argv)
    theme_name = "dark"
    if "--help" in args or "-h" in args:
        print("Usage: flossware-setup [--theme NAME]")
        print("       python3 scripts/setup.py [--theme NAME]")
        print("Provider credentials are optional; use scripts/install.sh for non-interactive setup.")
        return 0
    for i, arg in enumerate(args):
        if arg == "--theme" and i + 1 < len(args):
            theme_name = args[i + 1]
        elif arg.startswith("--theme="):
            theme_name = arg.split("=", 1)[1]
    if not sys.stdout.isatty():
        print(
            "Non-interactive environment. Use scripts/install.sh instead.",
            file=sys.stderr,
        )
        return 1
    try:
        curses.wrapper(lambda win: run(win, theme_name))
    except (KeyboardInterrupt, curses.error) as exc:
        print(f"Setup cancelled: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — top-level CLI boundary
        print(f"Setup failed: {exc}", file=sys.stderr)
        return 1
    return 0
