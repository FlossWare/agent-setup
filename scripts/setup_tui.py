#!/usr/bin/env python3
"""Persistent FlossWare AI setup/control-panel TUI.

The TUI is an editor for the same on-disk state consumed by the CLI and agent
integration layer. Configuration is profile-scoped, loaded on startup, saved
on every confirmed change, and never stores credential values.
"""
from __future__ import annotations

import curses
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("FLOSSWARE_AI_ROOT", Path.home() / ".flossware" / "ai"))
STATE = ROOT / "state"
ACTIVE_PROFILE = STATE / "active-profile"

AGENTS = [
    ("Claude Code", "claude-code", "CLAUDE.md"),
    ("Cursor", "cursor", ".cursorrules"),
    ("OpenCode", "opencode", "AGENTS.md"),
    ("Crush", "crush", "AGENTS.md"),
    ("Codex", "codex", "AGENTS.md"),
    ("Aider", "aider", "CONVENTIONS.md"),
    ("Cline", "cline", ".clinerules/FlossWare.md"),
    ("Roo Code", "roo-code", ".roo/rules/FlossWare.md"),
    ("Gemini CLI", "gemini-cli", "GEMINI.md"),
    ("GitHub Copilot", "github-copilot", ".github/copilot-instructions.md"),
    ("Windsurf", "windsurf", ".windsurfrules"),
    ("Amazon Q Developer", "amazon-q", ".amazonq/rules/FlossWare.md"),
    ("Kiro", "kiro", ".kiro/steering/FlossWare.md"),
]
COMPONENTS = [
    ("Model Router", "model-router-ai", "Routing, provider failover, capability and cost awareness."),
    ("Resilience", "resilience-ai", "Retries, fallbacks, circuit breakers and recovery."),
    ("Structured Output", "structured-output-ai", "Schema-constrained and validated output."),
    ("Consensus", "consensus-ai", "Multi-model voting and confidence."),
    ("Evaluation", "evaluation-ai", "Quality scoring and adversarial verification."),
    ("Observability", "observability-ai", "Traces, metrics and operational visibility."),
    ("Security", "security-ai", "Validation, policy and secret handling."),
    ("RAG", "rag-ai", "Retrieval and grounded generation."),
    ("Genetic Optimizer", "genetic-optimizer-ai", "Evolutionary workflow and model optimization."),
]
RUNTIMES = [
    ("Auto", "auto", "Use the first healthy runtime according to platform policy."),
    ("Podman", "podman", "Preferred container runtime on Linux."),
    ("Docker", "docker", "Docker Engine or Docker Desktop."),
    ("Native", "native", "Do not use a container runtime."),
]
DECORATORS = [
    ("Security / Policy", "security"),
    ("Model Routing", "routing"),
    ("Cache", "cache"),
    ("Retry", "retry"),
    ("Circuit Breaker", "circuit-breaker"),
    ("Observability", "observability"),
    ("Evaluation", "evaluation"),
    ("Cost / Token Accounting", "cost-accounting"),
]
PROFILES = [("Personal", "personal"), ("Red Hat", "redhat")]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def active_profile():
    try:
        value = ACTIVE_PROFILE.read_text(encoding="utf-8").strip()
        return value if value in {"personal", "redhat"} else "personal"
    except OSError:
        return "personal"


def profile_file(profile):
    return STATE / f"config-{profile}.json"


def default_config(profile):
    return {
        "version": 1,
        "profile": profile,
        "agents": [],
        "components": ["model-router-ai", "resilience-ai", "structured-output-ai"],
        "runtime": "auto",
        "decorators": [x[1] for x in DECORATORS],
        "updated_at": None,
    }


def load_config(profile):
    path = profile_file(profile)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("configuration must be an object")
    except (OSError, ValueError):
        data = default_config(profile)
    base = default_config(profile)
    base.update(data)
    base["profile"] = profile
    return base


def save_config(config):
    STATE.mkdir(parents=True, exist_ok=True)
    config["updated_at"] = now()
    path = profile_file(config["profile"])
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(path)
    os.chmod(path, 0o600)
    ACTIVE_PROFILE.write_text(config["profile"] + "\n", encoding="utf-8")
    os.chmod(ACTIVE_PROFILE, 0o600)


def configured_agent_ids(config):
    return {x for x in config.get("agents", []) if x in {a[1] for a in AGENTS}}


def configured_component_ids(config):
    return {x for x in config.get("components", []) if x in {c[1] for c in COMPONENTS}}


def palette():
    curses.start_color()
    curses.use_default_colors()
    for i, fg in enumerate((curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_RED, curses.COLOR_WHITE, curses.COLOR_MAGENTA), 1):
        curses.init_pair(i, fg, -1)


def add(win, y, x, text, pair=5, attr=0):
    h, w = win.getmaxyx()
    if 0 <= y < h and x < w - 1:
        try:
            win.addnstr(y, max(0, x), str(text), max(0, w - max(0, x) - 1), curses.color_pair(pair) | attr)
        except curses.error:
            pass


def status_text(config, dirty=False):
    if dirty:
        return "● MODIFIED"
    return "● SAVED" if config.get("updated_at") else "● DEFAULT"


def header(win, config, title):
    win.erase()
    _, w = win.getmaxyx()
    add(win, 0, 2, f" FlossWare AI   Profile: [{config['profile']} ▼]   {status_text(config)}", 1, curses.A_BOLD)
    add(win, 1, 2, "=" * min(100, max(10, w - 4)), 1)
    add(win, 2, 2, "Agents │ Accounts │ Models │ Components │ MCP │ Policies │ Summary", 5)
    add(win, 3, 2, f" {title}", 1, curses.A_BOLD)
    add(win, 4, 2, "-" * min(100, max(10, w - 4)), 1)
    return 6


def footer(win, config, hint="↑↓ navigate  Space toggle  Enter select  Esc back  F10 exit"):
    h, _ = win.getmaxyx()
    add(win, h - 2, 2, f"{status_text(config)}  │  {hint}", 6)


def select_menu(win, config, title, items, selected=None, multi=False, descriptions=True):
    cursor = 0
    selected = set(selected or [])
    while True:
        y = header(win, config, title)
        h, w = win.getmaxyx()
        visible = items[:max(1, h - 10)]
        for i, item in enumerate(visible):
            label = item[0] if isinstance(item, tuple) else item
            desc = item[2] if len(item) > 2 else "" if isinstance(item, tuple) else ""
            if multi:
                mark = "[x]" if i in selected else "[ ]"
            else:
                mark = "●" if i == cursor else "○"
            add(win, y + i, 2, "> " if i == cursor else "  ", 1, curses.A_BOLD if i == cursor else 0)
            add(win, y + i, 5, mark, 2 if i in selected or (not multi and i == cursor) else 3)
            add(win, y + i, 10, label, 1 if i == cursor else 5, curses.A_BOLD if i == cursor else 0)
            if descriptions and desc:
                add(win, y + i, min(w - 30, 12 + len(label)), desc, 5)
        footer(win, config)
        win.refresh()
        key = win.getch()
        if key in (curses.KEY_UP, ord("k")):
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            cursor = min(len(items) - 1, cursor + 1)
        elif multi and key == ord(" "):
            selected.symmetric_difference_update({cursor})
        elif multi and key == ord("a"):
            selected = set(range(len(items)))
        elif multi and key == ord("n"):
            selected.clear()
        elif key in (10, 13, curses.KEY_ENTER):
            return sorted(selected) if multi else cursor
        elif key in (27, ord("q")):
            return None


def pager(win, config, title, lines):
    offset = 0
    lines = list(lines) or ["No output."]
    while True:
        y = header(win, config, title)
        h, w = win.getmaxyx()
        usable = max(1, h - 10)
        for i, line in enumerate(lines[offset:offset + usable]):
            add(win, y + i, 2, line, 5)
        footer(win, config, "↑↓ scroll  PgUp/PgDn page  Esc back")
        win.refresh()
        key = win.getch()
        if key in (27, ord("q"), 10, 13, curses.KEY_ENTER):
            return
        if key in (curses.KEY_DOWN, ord("j")):
            offset = min(max(0, len(lines) - usable), offset + 1)
        elif key in (curses.KEY_UP, ord("k")):
            offset = max(0, offset - 1)
        elif key == curses.KEY_NPAGE:
            offset = min(max(0, len(lines) - usable), offset + usable)
        elif key == curses.KEY_PPAGE:
            offset = max(0, offset - usable)


def choose_profile(win, config):
    idx = select_menu(win, config, "Profile", PROFILES, multi=False)
    if idx is None:
        return config
    profile = PROFILES[idx][1]
    if profile == config["profile"]:
        return config
    save_config(config)
    new = load_config(profile)
    save_config(new)
    return new


def edit_agents(win, config):
    ids = configured_agent_ids(config)
    selected = select_menu(win, config, "Coding Agents", AGENTS, [i for i, a in enumerate(AGENTS) if a[1] in ids], multi=True)
    if selected is None:
        return
    config["agents"] = [AGENTS[i][1] for i in selected]
    save_config(config)
    pause(win, config, "Agents", ["Saved.", "Enabled: " + (", ".join(config["agents"]) or "none")])


def edit_components(win, config):
    ids = configured_component_ids(config)
    selected = select_menu(win, config, "FlossWare Components", COMPONENTS, [i for i, c in enumerate(COMPONENTS) if c[1] in ids], multi=True)
    if selected is None:
        return
    config["components"] = [COMPONENTS[i][1] for i in selected]
    save_config(config)
    pause(win, config, "Components", ["Saved.", "Enabled: " + (", ".join(config["components"]) or "none")])


def edit_runtime(win, config):
    current = next((i for i, x in enumerate(RUNTIMES) if x[1] == config.get("runtime")), 0)
    idx = select_menu(win, config, "Container Runtime", RUNTIMES, multi=False)
    if idx is None:
        return
    config["runtime"] = RUNTIMES[idx][1]
    save_config(config)
    pause(win, config, "Runtime", [f"Saved: {config['runtime']}", f"Previous: {RUNTIMES[current][1]}"])


def edit_decorators(win, config):
    stack = [x for x in config.get("decorators", []) if x in {d[1] for d in DECORATORS}]
    stack += [d[1] for d in DECORATORS if d[1] not in stack]
    cursor = 0
    while True:
        y = header(win, config, "Decorator Pipeline")
        add(win, y, 2, "Outer → Inner", 6)
        for i, key in enumerate(stack[:max(1, win.getmaxyx()[0] - y - 6)]):
            label = next(d[0] for d in DECORATORS if d[1] == key)
            add(win, y + 2 + i, 2, f"{i + 1:2}. {label}", 1 if i == cursor else 5, curses.A_REVERSE if i == cursor else 0)
        footer(win, config, "↑↓ select  ←→ reorder  s save  r reset  Esc back")
        win.refresh()
        key = win.getch()
        if key in (curses.KEY_UP, ord("k")):
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            cursor = min(len(stack) - 1, cursor + 1)
        elif key == curses.KEY_LEFT and cursor:
            stack[cursor - 1], stack[cursor] = stack[cursor], stack[cursor - 1]; cursor -= 1
        elif key == curses.KEY_RIGHT and cursor < len(stack) - 1:
            stack[cursor + 1], stack[cursor] = stack[cursor], stack[cursor + 1]; cursor += 1
        elif key == ord("r"):
            stack = [d[1] for d in DECORATORS]; cursor = 0
        elif key == ord("s"):
            config["decorators"] = stack
            save_config(config)
        elif key in (27, ord("q")):
            return


def discovery(win, config, cmd, title):
    py = ROOT / "venv/bin/python"
    script = ROOT / "discovery.py"
    try:
        p = subprocess.run([str(py), str(script), *cmd], capture_output=True, text=True, timeout=90)
        output = p.stdout or p.stderr or "No output."
    except (OSError, subprocess.SubprocessError) as exc:
        output = f"Discovery failed: {exc}"
    pager(win, config, title, output.splitlines())


def summary(win, config):
    agents = [a[0] for a in AGENTS if a[1] in configured_agent_ids(config)]
    comps = [c[0] for c in COMPONENTS if c[1] in configured_component_ids(config)]
    lines = [
        "Configuration",
        "-------------",
        f"Profile             {config['profile']}",
        f"Active agents       {len(agents)}" + (f": {', '.join(agents)}" if agents else ": none"),
        f"Components          {len(comps)}" + (f": {', '.join(comps)}" if comps else ": none"),
        f"Runtime             {config.get('runtime', 'auto')}",
        f"Decorator pipeline  {len(config.get('decorators', []))} stages",
        "Accounts/models     Use Accounts / Models to inspect live discovery",
        "Credentials         Environment/agent-managed; values are never stored by this TUI",
        f"Last saved          {config.get('updated_at') or 'not yet saved'}",
        f"Config file         {profile_file(config['profile'])}",
        "",
        "This is the persisted control-plane state for the selected profile.",
    ]
    pager(win, config, "Configuration Summary", lines)


def pause(win, config, title, lines):
    pager(win, config, title, lines)


def exit_screen(win, config):
    agents = ", ".join(config.get("agents", [])) or "none"
    comps = ", ".join(config.get("components", [])) or "none"
    lines = [
        "Configuration saved",
        "",
        f"Profile             {config['profile']}",
        f"Agents              {agents}",
        f"Components          {comps}",
        f"Runtime             {config.get('runtime', 'auto')}",
        f"MCP                 available through the installed control plane",
        f"Saved               {config.get('updated_at') or 'now'}",
        f"File                {profile_file(config['profile'])}",
        "",
        "Credential values are not stored in this configuration.",
        "Press any key to exit.",
    ]
    pager(win, config, "Exit Summary", lines)


def main():
    def app(win):
        curses.curs_set(0)
        win.keypad(True)
        palette()
        config = load_config(active_profile())
        # Normalize and persist an initial profile state so the first launch is
        # immediately inspectable from both the TUI and CLI.
        if not config.get("updated_at"):
            save_config(config)
        while True:
            items = [
                ("Summary", "summary", "Current persisted configuration"),
                ("Profile", "profile", "Switch the active profile"),
                ("Agents", "agents", "Enable external coding-agent integrations"),
                ("Accounts / Models", "accounts", "Inspect live providers, identities and models"),
                ("Components", "components", "Select independently usable FlossWare capabilities"),
                ("MCP", "mcp", "Inspect MCP configuration and status"),
                ("Policies / Decorators", "decorators", "Configure cross-cutting behavior"),
                ("Container Runtime", "runtime", "Choose auto, Podman, Docker or native"),
                ("Doctor", "doctor", "Run installation and discovery diagnostics"),
                ("Exit", "exit", "Show the final saved state and leave"),
            ]
            idx = select_menu(win, config, "Control Panel", items, multi=False)
            if idx is None or items[idx][1] == "exit":
                exit_screen(win, config)
                return
            key = items[idx][1]
            if key == "summary": summary(win, config)
            elif key == "profile": config = choose_profile(win, config)
            elif key == "agents": edit_agents(win, config)
            elif key == "accounts": discovery(win, config, ["accounts", "--verify"], "Accounts / Identities")
            elif key == "components": edit_components(win, config)
            elif key == "mcp": discovery(win, config, ["doctor"], "MCP / Control Plane Health")
            elif key == "decorators": edit_decorators(win, config)
            elif key == "runtime": edit_runtime(win, config)
            elif key == "doctor": discovery(win, config, ["doctor"], "Doctor")

    curses.wrapper(app)


if __name__ == "__main__":
    main()
