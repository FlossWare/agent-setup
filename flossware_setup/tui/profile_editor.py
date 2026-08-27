"""Interactive profile editor for the curses TUI."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from flossware_setup.config_control import available_profiles, load_profile, profiles_dir


def profile_path(name: str) -> Path:
    return profiles_dir() / f"{name}.toml"


def _toml_value(value: Any) -> str:
    if isinstance(value, bool): return "true" if value else "false"
    if isinstance(value, str): return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(value, (int, float)): return str(value)
    if isinstance(value, list): return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    raise TypeError(f"unsupported TOML value: {type(value).__name__}")


def _dump_toml(data: dict[str, Any]) -> str:
    """Serialize profile data without dropping fields unknown to the editor."""
    out: list[str] = []
    def emit_table(name: str, values: dict[str, Any]) -> None:
        if out: out.append("")
        out.append(f"[{name}]")
        nested: list[tuple[str, dict[str, Any]]] = []
        for key, value in values.items():
            if isinstance(value, dict): nested.append((key, value))
            else: out.append(f"{key} = {_toml_value(value)}")
        for key, value in nested: emit_table(f"{name}.{key}", value)
    for key, value in data.items():
        if not isinstance(value, dict): out.append(f"{key} = {_toml_value(value)}")
    for key, value in data.items():
        if isinstance(value, dict): emit_table(key, value)
    return "\n".join(out) + "\n"


def edit_profile(name: str, values: dict[str, object] | None = None) -> Path:
    """Update editable fields while preserving every other profile setting."""
    if name not in available_profiles(): raise ValueError(f"unknown profile: {name}")
    path = profile_path(name); data = load_profile(name)
    if values is None: return path
    model = data.setdefault("model_policy", {}); optimization = data.setdefault("optimization", {}); cost = data.setdefault("cost", {})
    for key in ("allow_local_models", "allow_personal_accounts", "allow_provider_fallback", "allow_unconfigured_providers"):
        if key in values: model[key] = bool(values[key])
    if "allowed_providers" in values: model["allowed_providers"] = list(values["allowed_providers"])
    if "optimization_enabled" in values: optimization["enabled"] = bool(values["optimization_enabled"])
    if "optimization_strategy" in values: optimization["strategy"] = str(values["optimization_strategy"])
    if "optimization_population" in values: optimization.setdefault("genetic", {})["population_size"] = int(values["optimization_population"])
    if "monthly_limit_usd" in values: cost["monthly_limit_usd"] = float(values["monthly_limit_usd"])
    if "hard_limit" in values: cost["hard_limit"] = bool(values["hard_limit"])
    path.write_text(_dump_toml(data), encoding="utf-8"); return path


def edit_profile_tui(win, name: str, popup, close, add, palette) -> None:
    """Interactive editor for policy, provider, optimizer, and budget settings."""
    import curses
    data = load_profile(name); model = data.get("model_policy", {}); optimization = data.get("optimization", {}); genetic = optimization.get("genetic", {}) if isinstance(optimization.get("genetic", {}), dict) else {}; cost = data.get("cost", {})
    providers = list(model.get("allowed_providers") or ["*configured*"]); strategies = ["hybrid", "genetic", "thompson"]; strategy = str(optimization.get("strategy", "hybrid")); strategy = strategy if strategy in strategies else "hybrid"
    fields: list[list[Any]] = [["Allowed providers", ",".join(str(x) for x in providers), "text"], ["Allow local models", bool(model.get("allow_local_models", True)), "bool"], ["Allow personal accounts", bool(model.get("allow_personal_accounts", False)), "bool"], ["Allow provider fallback", bool(model.get("allow_provider_fallback", False)), "bool"], ["Allow unconfigured providers", bool(model.get("allow_unconfigured_providers", False)), "bool"], ["Optimization enabled", bool(optimization.get("enabled", True)), "bool"], ["Optimization strategy", strategy, "cycle"], ["Population size", int(genetic.get("population_size", 30) or 30), "int"], ["Monthly limit (USD)", float(cost.get("monthly_limit_usd", 0.0) or 0.0), "money"], ["Hard budget limit", bool(cost.get("hard_limit", False)), "bool"]]
    idx = 0
    while True:
        h, w = win.getmaxyx(); height = min(len(fields) + 5, h - 2); width = min(76, w - 4); top, left = max(1, (h - height) // 2), max(1, (w - width) // 2); panel = popup(win, top, left, height, width, f"Edit Profile: {name}")
        for i, (label, value, kind) in enumerate(fields):
            shown = value if kind == "text" else ("ON" if value else "OFF") if kind == "bool" else f"${value:.2f}" if kind == "money" else str(value); add(panel, 2 + i, 2, ("> " if i == idx else "  ") + f"{label}: {shown}", palette("selected" if i == idx else "normal"))
        panel.addnstr(height - 2, 2, "Enter/Space edit | +/- change | S save | Esc cancel", width - 4, palette("muted")); panel.refresh(); key = panel.getch(); close(panel)
        if key in (27, ord("q"), ord("Q")): return
        if key in (curses.KEY_UP, ord("k")): idx = (idx - 1) % len(fields); continue
        if key in (curses.KEY_DOWN, ord("j")): idx = (idx + 1) % len(fields); continue
        kind = fields[idx][2]
        if key in (10, 13, curses.KEY_ENTER, ord(" ")):
            if kind == "bool": fields[idx][1] = not fields[idx][1]
            elif kind == "cycle": fields[idx][1] = strategies[(strategies.index(fields[idx][1]) + 1) % len(strategies)]
            elif kind == "text":
                curses.echo(); curses.curs_set(1)
                try: raw = panel.getstr(2 + idx, min(width - 2, 23), width - 26).decode("utf-8", "ignore").strip()
                finally: curses.noecho(); curses.curs_set(0)
                if raw: fields[idx][1] = raw
        elif key in (ord("+"), ord("=")) and kind in ("int", "money"): fields[idx][1] += 10
        elif key in (ord("-"), ord("_")) and kind in ("int", "money"): fields[idx][1] = max(0, fields[idx][1] - 10)
        elif key in (ord("s"), ord("S")):
            proposed = {"allowed_providers": [p.strip() for p in str(fields[0][1]).split(",") if p.strip()], "allow_local_models": fields[1][1], "allow_personal_accounts": fields[2][1], "allow_provider_fallback": fields[3][1], "allow_unconfigured_providers": fields[4][1], "optimization_enabled": fields[5][1], "optimization_strategy": fields[6][1], "optimization_population": fields[7][1], "monthly_limit_usd": fields[8][1], "hard_limit": fields[9][1]}
            if not proposed["allowed_providers"]: proposed["allowed_providers"] = ["*configured*"]
            if name != "personal" and proposed["allowed_providers"] != ["*configured*"] and (proposed["allow_personal_accounts"] or proposed["allow_unconfigured_providers"] or proposed["allow_provider_fallback"]): continue
            edit_profile(name, proposed); return
