"""Curses TUI for FlossWare coding-agent setup.

Supports keyboard and mouse interaction. Hosts the Setup Control Center
including the Review Current Configuration screen. Credential values are
never displayed.
"""

from __future__ import annotations

import curses
import os
import sys
from pathlib import Path

from flossware_setup.artifacts import generate_artifacts
from flossware_setup.catalog import AGENTS, BUDGET_POLICIES, CAPABILITIES, PROVIDERS
from flossware_setup.config import Config, review_lines
from flossware_setup.credentials import credential_status
from flossware_setup.installer import install_packages


def load_theme(name: str):
    """Load FlossWare themes when available, without installing during TUI startup."""
    try:
        from curses_themes import ThemeManager

        return ThemeManager.load(name)
    except Exception:
        return None


def palette() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)


def enable_mouse(win) -> bool:
    """Enable terminal mouse reporting when the curses implementation supports it."""
    try:
        mask = curses.ALL_MOUSE_EVENTS
        if hasattr(curses, "REPORT_MOUSE_POSITION"):
            mask |= curses.REPORT_MOUSE_POSITION
        curses.mousemask(mask)
        if hasattr(curses, "mouseinterval"):
            curses.mouseinterval(200)
        return True
    except (AttributeError, curses.error):
        return False


def mouse_click(event) -> tuple[int, int] | None:
    """Return (x, y) for a primary-button click, otherwise None."""
    try:
        _id, x, y, _z, bstate = curses.getmouse()
    except curses.error:
        return None
    clicked = getattr(curses, "BUTTON1_CLICKED", 0)
    pressed = getattr(curses, "BUTTON1_PRESSED", 0)
    if bstate & (clicked | pressed):
        return x, y
    return None


def add(win, y: int, x: int, text: str, pair: int = 5, attr: int = 0) -> None:
    h, w = win.getmaxyx()
    if 0 <= y < h and x < w - 1:
        try:
            win.addnstr(
                y,
                max(0, x),
                text,
                max(0, w - max(0, x) - 1),
                curses.color_pair(pair) | attr,
            )
        except curses.error:
            pass


def header(win, title: str, step: int | None = None) -> int:
    win.erase()
    _, w = win.getmaxyx()
    label = (
        f" FlossWare AI  |  {title} "
        if step is None
        else f" FlossWare AI  |  {step}/5  {title} "
    )
    add(win, 1, 2, "=" * min(max(10, w - 4), 72), 1)
    add(win, 2, 2, label, 1, curses.A_BOLD)
    add(win, 3, 2, "=" * min(max(10, w - 4), 72), 1)
    return 5


def menu(
    win,
    title: str,
    items: list[tuple[str, str]],
    selected: list[int] | None = None,
    multi: bool = True,
) -> list[int] | int | None:
    selected_set = set(selected or [])
    cursor = 0
    while True:
        y = header(win, title)
        h, _ = win.getmaxyx()
        visible = min(len(items), max(0, h - y - 3))
        for i, item in enumerate(items[:visible]):
            name, desc = item[0], item[1]
            if multi:
                mark = "[x]" if i in selected_set else "[ ]"
            else:
                mark = "(o)" if i == cursor else "( )"
            prefix = "> " if i == cursor else "  "
            add(win, y + i, 2, prefix, 1 if i == cursor else 5, curses.A_BOLD)
            add(
                win,
                y + i,
                5,
                mark,
                2 if i in selected_set or (not multi and i == cursor) else 3,
            )
            add(
                win,
                y + i,
                10,
                name,
                1 if i == cursor else 5,
                curses.A_BOLD if i == cursor else 0,
            )
            add(win, y + i, 10 + len(name) + 3, desc, 5)
        add(
            win,
            h - 2,
            2,
            "↑/↓ navigate  Space/click toggle  Enter confirm  a all  n none  q quit",
            6,
        )
        win.refresh()
        key = win.getch()
        if key == curses.KEY_MOUSE:
            click = mouse_click(key)
            if click is None:
                continue
            _, click_y = click
            clicked_index = click_y - y
            if 0 <= clicked_index < visible:
                cursor = clicked_index
                if multi:
                    if cursor in selected_set:
                        selected_set.remove(cursor)
                    else:
                        selected_set.add(cursor)
                else:
                    return cursor
            continue
        if key in (curses.KEY_UP, ord("k")):
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            cursor = min(max(0, len(items) - 1), cursor + 1)
        elif multi and key == ord(" "):
            if cursor in selected_set:
                selected_set.remove(cursor)
            else:
                selected_set.add(cursor)
        elif multi and key == ord("a"):
            selected_set = set(range(len(items)))
        elif multi and key == ord("n"):
            selected_set = set()
        elif key in (10, 13, curses.KEY_ENTER):
            if multi:
                return sorted(selected_set)
            return cursor
        elif key in (ord("q"), 27):
            return None


def input_screen(win, prompt: str, default: str = "") -> str:
    curses.echo()
    curses.curs_set(1)
    y = header(win, "Input")
    add(win, y, 2, prompt, 1)
    add(win, y + 2, 2, default, 5)
    win.move(y + 2, 2 + len(default))
    win.refresh()
    try:
        raw = win.getstr(y + 2, 2, 200)
        text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        text = text.strip() or default
    except Exception:
        text = default
    finally:
        curses.noecho()
        curses.curs_set(0)
    return text


def key_status(win) -> None:
    y = header(win, "Provider Credentials")
    status = credential_status()
    configured = 0
    for name, env, _url in PROVIDERS:
        present = status.get(name, False)
        if present:
            configured += 1
        add(win, y, 2, "SET" if present else "---", 2 if present else 3, curses.A_BOLD)
        add(win, y, 8, name, 1 if present else 5, curses.A_BOLD)
        add(win, y, 22, f"${env}", 5)
        y += 1
        if y >= win.getmaxyx()[0] - 4:
            break
    add(
        win,
        win.getmaxyx()[0] - 2,
        2,
        f"{configured} provider credential(s) detected. No credential is required.",
        2 if configured else 3,
    )
    win.refresh()
    win.getch()


def review_screen(win, repo_dir: str = ".") -> None:
    """Review Current Configuration control-center screen."""
    y = header(win, "Review Current Configuration")
    h, _ = win.getmaxyx()
    lines = review_lines(repo_dir)
    for i, line in enumerate(lines[: max(1, h - y - 3)]):
        color = 2 if "✓" in line else 5
        add(win, y + i, 2, line, color)
    add(win, h - 2, 2, "Enter / Esc / q  back", 6)
    win.refresh()
    while True:
        key = win.getch()
        if key in (10, 13, 27, ord("q")):
            return


def build_screen(win, cfg: Config) -> None:
    y = header(win, "Building Configuration")
    add(win, y, 2, "Installing selected FlossWare libraries...", 3)
    win.refresh()
    install_packages(cfg.capabilities)
    generate_artifacts(cfg)
    win.erase()
    y = header(win, "Setup Complete")
    add(win, y, 2, "Configuration generated successfully.", 2, curses.A_BOLD)
    add(win, y + 2, 2, "No credential values were written to generated files.", 2)
    add(win, y + 4, 2, "Press any key to continue.", 6)
    win.refresh()
    win.getch()


def configure_wizard(win) -> Config | None:
    """Multi-step selection wizard (agents → capabilities → budget → repo)."""
    cfg = Config()
    agents = menu(
        win,
        "Select Coding Agents",
        [(a.name, a.description) for a in AGENTS],
        multi=True,
    )
    if agents is None or not agents:
        return None
    cfg.agents = list(agents)

    caps = menu(
        win,
        "FlossWare AI Capabilities",
        [(c[0], c[1]) for c in CAPABILITIES],
        selected=[i for i, c in enumerate(CAPABILITIES) if c[2]],
        multi=True,
    )
    if caps is None:
        return None
    cfg.capabilities = list(caps)

    budget = menu(
        win,
        "Budget Policy",
        [(b[0], b[2]) for b in BUDGET_POLICIES],
        multi=False,
    )
    if budget is None:
        return None
    cfg.budget_index = int(budget)
    if BUDGET_POLICIES[cfg.budget_index][1] < 0:
        value = input_screen(win, "Monthly budget ceiling in USD:", "50")
        try:
            cfg.budget_amount = max(0.0, float(value))
        except ValueError:
            cfg.budget_amount = 50.0
    else:
        cfg.budget_amount = BUDGET_POLICIES[cfg.budget_index][1]

    cfg.repo_dir = input_screen(win, "Project directory:", os.getcwd())
    if not (Path(cfg.repo_dir).resolve() / ".git").exists():
        raise ValueError(f"Not a git repository: {Path(cfg.repo_dir).resolve()}")
    return cfg


def run(stdscr, theme_name: str = "dark") -> None:
    curses.curs_set(0)
    stdscr.keypad(True)
    palette()
    enable_mouse(stdscr)
    external_theme = load_theme(theme_name)

    y = header(stdscr, "Setup Control Center")
    add(stdscr, y, 2, "Provider-neutral coding-agent setup.", 5)
    add(stdscr, y + 1, 2, "Keyboard and mouse are both supported when available.", 5)
    if external_theme:
        add(stdscr, y + 2, 2, f"Theme: {theme_name} (curses-themes).", 1)
        add(stdscr, y + 3, 2, "Press t for theme help, Enter/click to continue, q to quit.", 6)
    else:
        add(stdscr, y + 2, 2, "Press Enter/click to continue, q to quit.", 6)
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key == curses.KEY_MOUSE:
            if mouse_click(key) is not None:
                break
        elif key in (ord("q"), 27):
            return
        elif key == ord("t") and external_theme:
            add(
                stdscr,
                y + 5,
                2,
                "Theme loaded from FlossWare/curses-themes. Use --theme NAME to choose another.",
                1,
            )
            stdscr.refresh()
            stdscr.getch()
        elif key in (10, 13):
            break

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
            key_status(stdscr)
        else:
            try:
                cfg = configure_wizard(stdscr)
                if cfg is None:
                    continue
                key_status(stdscr)
                build_screen(stdscr, cfg)
                review_screen(stdscr, cfg.repo_dir)
            except Exception as exc:
                y = header(stdscr, "Setup Error")
                add(stdscr, y, 2, str(exc), 4)
                add(stdscr, y + 2, 2, "Press any key.", 6)
                stdscr.refresh()
                stdscr.getch()


def main(argv: list[str] | None = None) -> int:
    """CLI entry for the setup TUI."""
    args = list(sys.argv[1:] if argv is None else argv)
    theme_name = "dark"
    if "--help" in args or "-h" in args:
        print("Usage: python3 scripts/setup.py [--theme NAME]")
        print(
            "Provider credentials are optional; use scripts/install.sh for non-interactive setup."
        )
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
    except Exception as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        return 1
    return 0
