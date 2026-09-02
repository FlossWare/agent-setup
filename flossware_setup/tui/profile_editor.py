"""Interactive profile editor for the curses TUI."""
from __future__ import annotations

from typing import Any

from flossware_setup.config_control import (
    edit_profile,
    load_profile,
    update_profile,
)

# Re-export for callers that imported edit_profile from this module.
__all__ = ["edit_profile", "edit_profile_tui", "update_profile", "parse_providers_field"]


def parse_providers_field(raw: str) -> list[str]:
    """Parse the Allowed providers text field into provider references."""
    parts = [part.strip() for part in str(raw).split(",") if part.strip()]
    return parts or ["*configured*"]


def edit_text_field(panel, row: int, col: int, width: int, current: str) -> str:
    """Prompt for a single-line text value using curses (testable via panel stub)."""
    import curses

    prompt_col = col
    panel.addnstr(row, 2, " " * max(0, width), width)
    panel.addnstr(row, 2, "New value: ", width)
    panel.refresh()
    curses.echo()
    try:
        raw = panel.getstr(row, 13, max(8, min(40, width - 14)))
    finally:
        curses.noecho()
    if raw is None:
        return current
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace").strip()
    else:
        text = str(raw).strip()
    return text if text else current


def edit_profile_tui(win, name: str, popup, close, _add=None, _palette=None) -> None:
    """Interactive editor for policy, provider, optimizer, and budget settings."""
    import curses

    data = load_profile(name)
    model = data.get("model_policy", {})
    optimization = data.get("optimization", {})
    genetic = optimization.get("genetic", {}) if isinstance(optimization.get("genetic", {}), dict) else {}
    cost = data.get("cost", {})
    providers = list(model.get("allowed_providers") or ["*configured*"])
    strategies = ["hybrid", "genetic", "thompson"]
    strategy = str(optimization.get("strategy", "hybrid"))
    strategy = strategy if strategy in strategies else "hybrid"
    fields: list[list[Any]] = [
        ["Allowed providers", ",".join(str(x) for x in providers), "text"],
        ["Allow local models", bool(model.get("allow_local_models", True)), "bool"],
        ["Allow personal accounts", bool(model.get("allow_personal_accounts", False)), "bool"],
        ["Allow provider fallback", bool(model.get("allow_provider_fallback", False)), "bool"],
        ["Allow unconfigured providers", bool(model.get("allow_unconfigured_providers", False)), "bool"],
        ["Optimization enabled", bool(optimization.get("enabled", True)), "bool"],
        ["Optimization strategy", strategy, "choice", strategies],
        ["Population size", int(genetic.get("population_size", 30) or 30), "int"],
        ["Monthly budget USD", float(cost.get("monthly_limit_usd", 0.0) or 0.0), "money"],
        ["Hard budget limit", bool(cost.get("hard_limit", False)), "bool"],
    ]
    idx = 0
    panel = popup(win, 2, 4, min(20, max(14, len(fields) + 8)), 64, f"Edit profile: {name}")
    try:
        while True:
            panel.erase()
            panel.border()
            panel.addnstr(0, 2, f" Edit profile: {name} ", 60, curses.A_BOLD)
            for i, field in enumerate(fields):
                label, value = field[0], field[1]
                marker = ">" if i == idx else " "
                panel.addnstr(2 + i, 2, f"{marker} {label}: {value}", 58)
            panel.addnstr(len(fields) + 3, 2, "Enter/Space edit  s save  Esc cancel", 58)
            panel.refresh()
            key = panel.getch()
            if key in (27, ord("q"), ord("Q")):
                return
            if key in (curses.KEY_UP, ord("k")):
                idx = (idx - 1) % len(fields)
            elif key in (curses.KEY_DOWN, ord("j")):
                idx = (idx + 1) % len(fields)
            elif key in (ord("+"), ord("=")) and fields[idx][2] in ("int", "money"):
                fields[idx][1] = fields[idx][1] + 10
            elif key in (ord("-"), ord("_")) and fields[idx][2] in ("int", "money"):
                fields[idx][1] = max(0, fields[idx][1] - 10)
            elif key in (ord(" "), 10, 13, curses.KEY_ENTER):
                kind = fields[idx][2]
                if kind == "bool":
                    fields[idx][1] = not fields[idx][1]
                elif kind == "choice":
                    choices = fields[idx][3]
                    cur = fields[idx][1]
                    fields[idx][1] = choices[(choices.index(cur) + 1) % len(choices)] if cur in choices else choices[0]
                elif kind == "text":
                    current = str(fields[idx][1])
                    fields[idx][1] = edit_text_field(
                        panel, len(fields) + 4, 2, 58, current
                    )
            elif key in (ord("s"), ord("S")):
                proposed = {
                    "allowed_providers": parse_providers_field(str(fields[0][1])),
                    "allow_local_models": fields[1][1],
                    "allow_personal_accounts": fields[2][1],
                    "allow_provider_fallback": fields[3][1],
                    "allow_unconfigured_providers": fields[4][1],
                    "optimization_enabled": fields[5][1],
                    "optimization_strategy": fields[6][1],
                    "optimization_population": fields[7][1],
                    "monthly_limit_usd": fields[8][1],
                    "hard_limit": fields[9][1],
                }
                update_profile(name, proposed)
                return
    finally:
        close(panel)
