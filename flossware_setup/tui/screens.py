"""Screen-level TUI behavior for setup control center and wizard."""

from __future__ import annotations

import curses
import os
from pathlib import Path

from flossware_setup.artifacts import generate_artifacts
from flossware_setup.catalog import AGENTS, BUDGET_POLICIES, CAPABILITIES, PROVIDERS
from flossware_setup.config import Config, load_project_state, review_lines
from flossware_setup.credentials import credential_status
from flossware_setup.installer import install_packages
from flossware_setup.tui.input import is_cancel, is_confirm, primary_click
from flossware_setup.tui.widgets import add, header, menu, text_input


def welcome_screen(win, theme_name: str, external_theme) -> bool:
    """Show welcome. Returns False if the user quits."""
    y = header(win, "Setup Control Center")
    add(win, y, 2, "Provider-neutral coding-agent setup.", 5)
    add(win, y + 1, 2, "Keyboard and mouse are both supported when available.", 5)
    if external_theme:
        add(win, y + 2, 2, f"Theme: {theme_name} (curses-themes).", 1)
        add(win, y + 3, 2, "Press t for theme help, Enter/click to continue, q to quit.", 6)
    else:
        add(win, y + 2, 2, "Press Enter/click to continue, q to quit.", 6)
    win.refresh()
    while True:
        key = win.getch()
        if key == curses.KEY_MOUSE:
            if primary_click() is not None:
                return True
        elif is_cancel(key):
            return False
        elif key == ord("t") and external_theme:
            add(
                win,
                y + 5,
                2,
                "Theme loaded from FlossWare/curses-themes. Use --theme NAME to choose another.",
                1,
            )
            win.refresh()
            win.getch()
        elif is_confirm(key):
            return True


def credentials_screen(win) -> None:
    """Show provider credential presence (names only, never values)."""
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
    """Review Current Configuration from persisted project state only."""
    y = header(win, "Review Current Configuration")
    h, _ = win.getmaxyx()
    state = load_project_state(repo_dir)
    lines = review_lines(repo_dir)
    if state:
        artifacts = []
        repo = Path(repo_dir).resolve()
        for name in (".flossware-ai.json", "ai_config.py"):
            if (repo / name).is_file():
                artifacts.append(name)
        for agent in AGENTS:
            if agent.id in set(state.get("agents") or []):
                for rel in agent.files:
                    if (repo / rel).is_file():
                        artifacts.append(rel)
        if artifacts:
            lines.append("")
            lines.append("Generated artifacts present:")
            for name in sorted(set(artifacts)):
                lines.append(f"  · {name}")
    for i, line in enumerate(lines[: max(1, h - y - 3)]):
        color = 2 if "✓" in line else 5
        add(win, y + i, 2, line, color)
    add(win, h - 2, 2, "Enter / Esc / q  back", 6)
    win.refresh()
    while True:
        key = win.getch()
        if is_confirm(key) or is_cancel(key):
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


def error_screen(win, message: str) -> None:
    y = header(win, "Setup Error")
    add(win, y, 2, message, 4)
    add(win, y + 2, 2, "Press any key.", 6)
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
        value = text_input(win, "Monthly budget ceiling in USD:", "50")
        try:
            cfg.budget_amount = max(0.0, float(value))
        except ValueError:
            cfg.budget_amount = 50.0
    else:
        cfg.budget_amount = BUDGET_POLICIES[cfg.budget_index][1]

    cfg.repo_dir = text_input(win, "Project directory:", os.getcwd())
    if not (Path(cfg.repo_dir).resolve() / ".git").exists():
        raise ValueError(f"Not a git repository: {Path(cfg.repo_dir).resolve()}")
    return cfg
