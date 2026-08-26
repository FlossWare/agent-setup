"""Screen-level TUI behavior for setup control center and wizard."""

from __future__ import annotations

import curses
import os
from pathlib import Path

from flossware_setup.artifacts import generate_artifacts
from flossware_setup.catalog import AGENTS, BUDGET_POLICIES, CAPABILITIES, PROVIDERS
from flossware_setup.config import (
    Config,
    get_active_project,
    git_status_label,
    is_git_repository,
    load_project_state,
    project_state_path,
    resolve_review_project,
    review_lines,
)
from flossware_setup.credentials import credential_status
from flossware_setup.installer import install_packages
from flossware_setup.tui.input import is_cancel, is_confirm, primary_click
from flossware_setup.tui.widgets import add, header, menu, text_input


def welcome_screen(win, theme_name: str, external_theme) -> bool:
    """Show welcome. Returns False if the user quits."""
    y = header(win, "Setup Control Center")
    add(win, y, 2, "Provider-neutral coding-agent setup.", 5)
    add(win, y + 1, 2, "Keyboard and mouse are both supported when available.", 5)
    active = get_active_project()
    if active is not None:
        add(win, y + 2, 2, f"Active project: {active}", 1)
        tip_row = y + 3
    else:
        tip_row = y + 2
    if external_theme:
        add(win, tip_row, 2, f"Theme: {theme_name} (curses-themes).", 1)
        add(win, tip_row + 1, 2, "Press t for theme help, Enter/click to continue, q to quit.", 6)
    else:
        add(win, tip_row, 2, "Press Enter/click to continue, q to quit.", 6)
    win.refresh()
    while True:
        key = win.getch()
        if key == curses.KEY_MOUSE:
            if primary_click() is not None:
                return True
        elif is_cancel(key):
            return False
        elif key == ord("t") and external_theme:
            add(win, tip_row + 3, 2, "Theme loaded from FlossWare/curses-themes. Use --theme NAME to choose another.", 1)
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
    add(win, win.getmaxyx()[0] - 2, 2, f"{configured} provider credential(s) detected (names only). Enter to continue.", 6)
    win.refresh()
    while True:
        key = win.getch()
        if is_confirm(key) or is_cancel(key):
            return


def _artifact_lines(repo_dir: Path, state: dict) -> list[str]:
    lines = ["", "Central FlossWare state (outside project):"]
    central = project_state_path(repo_dir)
    lines.append(f"  [{'yes' if central.is_file() else 'no'}] {central}")
    lines.append(git_status_label(repo_dir))
    for agent_id in state.get("agents") or []:
        lines.append(f"  agent id: {agent_id}")
    return lines


def review_screen(win, repo_dir: str | Path | None = None) -> None:
    """Review Current Configuration from persisted project state only."""
    project = resolve_review_project(repo_dir)
    y = header(win, "Review Current Configuration")
    h, _ = win.getmaxyx()
    state = load_project_state(project)
    lines = review_lines(project)
    if state:
        lines.extend(_artifact_lines(project, state))
    for i, line in enumerate(lines[: max(1, h - y - 3)]):
        color = 2 if "yes" in line or "SET" in line else 5
        add(win, y + i, 2, line, color)
    add(win, h - 2, 2, "Enter / Esc / q  back", 6)
    win.refresh()
    while True:
        key = win.getch()
        if is_confirm(key) or is_cancel(key):
            return


def build_screen(win, cfg: Config) -> None:
    y = header(win, "Building Configuration")
    add(win, y, 2, f"Applying profile: {cfg.profile}", 1)
    add(win, y + 1, 2, "Installing selected FlossWare libraries...", 3)
    win.refresh()
    install_packages(cfg.capabilities)
    generate_artifacts(cfg)
    win.erase()
    y = header(win, "Setup Complete")
    add(win, y, 2, "Configuration generated successfully.", 2, curses.A_BOLD)
    add(win, y + 1, 2, f"Profile: {cfg.profile}", 1, curses.A_BOLD)
    add(win, y + 3, 2, "No credential values were written to generated files.", 2)
    add(win, y + 5, 2, f"Active project: {Path(cfg.repo_dir).resolve()}", 1)
    add(win, y + 7, 2, "Press any key to continue.", 6)
    win.refresh()
    win.getch()


def error_screen(win, message: str) -> None:
    y = header(win, "Setup Error")
    add(win, y, 2, message, 4)
    add(win, y + 2, 2, "Press any key.", 6)
    win.refresh()
    win.getch()


def _select_agents(win) -> list[str] | None:
    indexes = menu(win, "Select Coding Agents", [(a.name, a.description) for a in AGENTS], multi=True)
    if indexes is None or not indexes:
        return None
    return [AGENTS[i].id for i in indexes]


def _select_capabilities(win) -> list[str] | None:
    defaults = [i for i, c in enumerate(CAPABILITIES) if c[2]]
    indexes = menu(win, "FlossWare AI Capabilities", [(c[0], c[1]) for c in CAPABILITIES], selected=defaults, multi=True)
    if indexes is None:
        return None
    return [CAPABILITIES[i][0] for i in indexes]


def _select_budget(win, cfg: Config) -> bool:
    choice = menu(win, "Budget Policy", [(b[1], b[3]) for b in BUDGET_POLICIES], multi=False)
    if choice is None:
        return False
    policy_id, _label, amount, _desc = BUDGET_POLICIES[int(choice)]
    cfg.budget_policy = policy_id
    if amount < 0:
        value = text_input(win, "Monthly budget ceiling in USD:", "50")
        try:
            cfg.budget_amount = max(0.0, float(value))
        except ValueError:
            cfg.budget_amount = 50.0
    else:
        cfg.budget_amount = amount
    return True


def configure_wizard(win, profile: str = "default") -> Config | None:
    """Multi-step selection wizard using the selected configuration profile."""
    cfg = Config(profile=profile)
    agents = _select_agents(win)
    if agents is None:
        return None
    cfg.agents = agents
    caps = _select_capabilities(win)
    if caps is None:
        return None
    cfg.capabilities = caps
    if not _select_budget(win, cfg):
        return None
    default_repo = str(get_active_project() or Path(os.getcwd()).resolve())
    cfg.repo_dir = text_input(win, "Project directory:", default_repo)
    target = Path(cfg.repo_dir).expanduser().resolve()
    if not target.is_dir():
        raise ValueError(f"Not a directory: {target}")
    # Git is optional; status is informational only.
    _ = is_git_repository(target)
    return cfg
