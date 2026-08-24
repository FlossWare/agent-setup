#!/usr/bin/env python3
"""Interactive FlossWare coding-agent setup TUI.

The TUI is provider-neutral: credentials are optional, budget is a policy,
and generated artifacts never contain credential values.
"""

from __future__ import annotations

import curses
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

FLOSSWARE_BASE = "https://github.com/FlossWare"


@dataclass(frozen=True)
class AgentAdapter:
    """Metadata and project instruction targets for a coding agent."""

    id: str
    name: str
    description: str
    files: tuple[str, ...]


# Project-local instruction mechanisms verified against current agent documentation.
# Shared AGENTS.md consumers intentionally use the same file rather than creating
# competing agent-specific copies.
AGENT_ADAPTERS = (
    AgentAdapter("claude-code", "Claude Code", "Anthropic project instructions", ("CLAUDE.md",)),
    AgentAdapter("cursor", "Cursor", "Cursor project rules", (".cursorrules",)),
    AgentAdapter("opencode", "OpenCode", "Shared agent instructions", ("AGENTS.md",)),
    AgentAdapter("crush", "Crush", "Shared agent instructions", ("AGENTS.md",)),
    AgentAdapter("codex", "Codex", "Shared agent instructions", ("AGENTS.md",)),
    AgentAdapter("aider", "Aider", "Aider conventions", ("CONVENTIONS.md",)),
    AgentAdapter("cline", "Cline", "Cline project rules", (".clinerules/FlossWare.md",)),
    AgentAdapter("roo-code", "Roo Code", "Roo Code project rules", (".roo/rules/FlossWare.md",)),
    AgentAdapter("gemini-cli", "Gemini CLI", "Gemini project instructions", ("GEMINI.md",)),
    AgentAdapter(
        "github-copilot",
        "GitHub Copilot",
        "GitHub Copilot repository instructions",
        (".github/copilot-instructions.md",),
    ),
)

# Backward-compatible indexed view used by the existing TUI/config format.
AGENTS = tuple((a.name, a.id, a.files[0]) for a in AGENT_ADAPTERS)

CAPABILITIES = [
    ("model-router-ai", "LLM routing, provider failover, capability and cost awareness", True),
    ("resilience-ai", "Retry, circuit breakers, timeouts", True),
    ("structured-output-ai", "Schema-validated model output", True),
    ("consensus-ai", "Multi-model voting", False),
    ("evaluation-ai", "Quality scoring and adversarial verification", False),
    ("observability-ai", "Structured logging, metrics, cost tracking", False),
    ("security-ai", "Validation, secret masking, audit logging", False),
    ("rag-ai", "Document retrieval and hybrid search", False),
    ("genetic-optimizer-ai", "Genetic optimization and task tuning", False),
]

BUDGET_POLICIES = [
    ("Strict budget", 0.0, "Only providers/models permitted by a zero-cost policy"),
    ("Light", 10.0, "Up to $10/month"),
    ("Medium", 50.0, "Up to $50/month"),
    ("Custom", -1.0, "Set an explicit monthly ceiling"),
]

PROVIDERS = [
    ("Cohere", "COHERE_API_KEY", "https://dashboard.cohere.com/api-keys"),
    ("OpenRouter", "OPENROUTER_API_KEY", "https://openrouter.ai/keys"),
    ("Gemini", "GEMINI_API_KEY", "https://aistudio.google.com/apikey"),
    ("Groq", "GROQ_API_KEY", "https://console.groq.com/keys"),
    ("Cerebras", "CEREBRAS_API_KEY", "https://cloud.cerebras.ai/"),
    ("HuggingFace", "HUGGINGFACE_API_KEY", "https://huggingface.co/settings/tokens"),
]


@dataclass
class Config:
    agents: list[int] = field(default_factory=list)
    capabilities: list[int] = field(default_factory=list)
    budget_index: int = 2
    budget_amount: float = 50.0
    repo_dir: str = "."
    theme: str = "dark"


def load_theme(name: str):
    """Load FlossWare themes when available, without installing during TUI startup."""
    try:
        from curses_themes import ThemeManager
        return ThemeManager.load(name)
    except Exception:
        return None


def palette():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)


def add(win, y, x, text, pair=5, attr=0):
    h, w = win.getmaxyx()
    if 0 <= y < h and x < w - 1:
        try:
            win.addnstr(y, max(0, x), text, max(0, w - max(0, x) - 1), curses.color_pair(pair) | attr)
        except curses.error:
            pass


def header(win, title, step=None):
    win.erase()
    _, w = win.getmaxyx()
    label = f" FlossWare AI  |  {title} " if step is None else f" FlossWare AI  |  {step}/5  {title} "
    add(win, 1, 2, "=" * min(max(10, w - 4), 72), 1)
    add(win, 2, 2, label, 1, curses.A_BOLD)
    add(win, 3, 2, "=" * min(max(10, w - 4), 72), 1)
    return 5


def menu(win, title, items, selected=None, multi=True):
    selected = set(selected or [])
    cursor = 0
    while True:
        y = header(win, title)
        h, w = win.getmaxyx()
        for i, item in enumerate(items):
            if y + i >= h - 3:
                break
            name, desc = item[0], item[1]
            mark = "[x]" if i in selected else "[ ]" if multi else "(o)" if i == cursor else "( )"
            prefix = "> " if i == cursor else "  "
            add(win, y + i, 2, prefix, 1 if i == cursor else 5, curses.A_BOLD)
            add(win, y + i, 5, mark, 2 if i in selected or (not multi and i == cursor) else 3)
            add(win, y + i, 10, name, 1 if i == cursor else 5, curses.A_BOLD if i == cursor else 0)
            add(win, y + i, 10 + len(name) + 3, desc, 5)
        add(win, h - 2, 2, "↑/↓ navigate  Space toggle  Enter confirm  a all  n none  q quit", 6)
        win.refresh()
        key = win.getch()
        if key in (curses.KEY_UP, ord('k')):
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN, ord('j')):
            cursor = min(len(items) - 1, cursor + 1)
        elif multi and key == ord(' '):
            if cursor in selected:
                selected.remove(cursor)
            else:
                selected.add(cursor)
        elif multi and key == ord('a'):
            selected = set(range(len(items)))
        elif multi and key == ord('n'):
            selected.clear()
        elif key in (10, 13, curses.KEY_ENTER):
            return sorted(selected) if multi else cursor
        elif key in (ord('q'), 27):
            return None


def input_screen(win, prompt, default):
    y = header(win, "Configuration")
    add(win, y, 2, prompt, 5)
    add(win, y + 2, 2, f"[{default}] ", 1)
    curses.echo()
    try:
        win.move(y + 2, 2 + len(default) + 3)
        value = win.getstr(y + 2, 2 + len(default) + 3, 240).decode().strip()
    finally:
        curses.noecho()
    return value or default


def key_status(win):
    y = header(win, "Provider Credentials")
    add(win, y, 2, "Credentials are optional. Values are never displayed or written.", 5)
    y += 2
    configured = 0
    for name, env, _ in PROVIDERS:
        present = bool(os.environ.get(env))
        configured += int(present)
        add(win, y, 2, "SET " if present else "----", 2 if present else 3, curses.A_BOLD)
        add(win, y, 8, name, 1 if present else 5, curses.A_BOLD)
        add(win, y, 22, f"${env}", 5)
        y += 1
        if y >= win.getmaxyx()[0] - 4:
            break
    add(win, win.getmaxyx()[0] - 2, 2, f"{configured} provider credential(s) detected. No credential is required.", 2 if configured else 3)
    win.refresh()
    win.getch()


def pip_packages(capabilities):
    return [f"git+{FLOSSWARE_BASE}/{CAPABILITIES[i][0]}.git" for i in capabilities]


def _write_if_missing(path: Path, content: str) -> None:
    """Create an instruction file without overwriting user configuration."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _agent_content(base: list[str], adapter: AgentAdapter) -> str:
    content = list(base)
    if adapter.id == "aider":
        content[0] = "# FlossWare AI Integration"
        content.extend([
            "",
            "Aider: load this file as a read-only conventions file.",
            "",
        ])
    return "\n".join(content) + "\n"


def generate_artifacts(cfg: Config):
    repo = Path(cfg.repo_dir).resolve()
    if not (repo / ".git").exists():
        raise ValueError(f"Not a git repository: {repo}")
    names = [CAPABILITIES[i][0] for i in cfg.capabilities]
    policy = BUDGET_POLICIES[cfg.budget_index]
    budget = cfg.budget_amount if policy[1] < 0 else policy[1]
    provider_status = {name: bool(os.environ.get(env)) for name, env, _ in PROVIDERS}
    provider_vars = {name: env for name, env, _ in PROVIDERS}

    install_lines = "\n".join(f"python -m pip install {pkg}" for pkg in pip_packages(cfg.capabilities))
    providers_md = "\n".join(f"- {name}: `${env}` ({'configured' if provider_status[name] else 'not set'})" for name, env, _ in PROVIDERS)
    base = [
        "## FlossWare AI Integration",
        "",
        "This project uses provider-neutral FlossWare AI libraries. Provider selection and spending are explicit policy decisions, not hard-coded vendor or pricing preferences.",
        "",
        "### AI Stack",
        *[f"- **[{n}]({FLOSSWARE_BASE}/{n})**: {CAPABILITIES[i][1]}" for i, n in [(i, CAPABILITIES[i][0]) for i in cfg.capabilities]],
        "",
        f"### Budget policy: {policy[0]}",
        f"Monthly ceiling: ${budget:g}",
        "",
        "### Providers",
        providers_md,
        "",
        "Credential values are never stored in generated files. Configure them through a secure environment, OS secret store, CI secret store, or provider/router secret mechanism.",
        "",
        "### Install",
        "```bash",
        install_lines,
        "```",
        "",
    ]
    for idx in cfg.agents:
        adapter = AGENT_ADAPTERS[idx]
        content = _agent_content(base, adapter)
        for relative_path in adapter.files:
            _write_if_missing(repo / relative_path, content)
        if adapter.id == "aider":
            _write_if_missing(repo / ".aider.conf.yml", "# FlossWare AI conventions\nread: CONVENTIONS.md\n")

    config = {
        "tool": "FlossWare/coding-agent-setup",
        "budget_policy": policy[0],
        "monthly_budget": budget,
        "capabilities": names,
        "providers": provider_status,
        "provider_env_vars": provider_vars,
        "credential_values_written": False,
        "agents": [AGENT_ADAPTERS[i].id for i in cfg.agents],
        "theme": cfg.theme,
    }
    (repo / "ai_config.py").write_text(
        "# Auto-generated by FlossWare/coding-agent-setup. No credential values are stored.\n"
        + f"MONTHLY_BUDGET = {budget!r}\n"
        + f"BUDGET_POLICY = {policy[0]!r}\n"
        + f"PROVIDER_ENV_VARS = {provider_vars!r}\n"
        + "ACTIVE_PROVIDERS = {k: bool(__import__('os').environ.get(v)) for k, v in PROVIDER_ENV_VARS.items()}\n",
        encoding="utf-8",
    )
    (repo / ".flossware-ai.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def build(win, cfg):
    y = header(win, "Building Configuration")
    add(win, y, 2, "Installing selected FlossWare libraries...", 3)
    win.refresh()
    for pkg in pip_packages(cfg.capabilities):
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", pkg], capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            raise RuntimeError(f"Required library failed to install: {pkg}\n{result.stderr[-1200:]}")
    generate_artifacts(cfg)
    win.erase()
    y = header(win, "Setup Complete")
    add(win, y, 2, "Configuration generated successfully.", 2, curses.A_BOLD)
    add(win, y + 2, 2, "No credential values were written to generated files.", 2)
    add(win, y + 4, 2, "Press any key to exit.", 6)
    win.refresh()
    win.getch()


def run(stdscr, theme_name):
    curses.curs_set(0)
    stdscr.keypad(True)
    palette()
    external_theme = load_theme(theme_name)
    cfg = Config(theme=theme_name)
    y = header(stdscr, "Coding Agent Setup")
    add(stdscr, y, 2, "Configure supported coding agents with FlossWare AI.", 5)
    add(stdscr, y + 2, 2, "Provider-neutral. Credentials optional. Budget is a policy.", 2)
    add(stdscr, y + 4, 2, "Press Enter to start, t for theme selection, q to quit.", 6)
    stdscr.refresh()
    key = stdscr.getch()
    if key in (ord('q'), 27):
        return
    if key == ord('t') and external_theme:
        add(stdscr, y + 6, 2, "Theme loaded from FlossWare/curses-themes. Use --theme NAME to choose another.", 1)
        stdscr.refresh()
        stdscr.getch()

    agents = menu(stdscr, "Select Coding Agents", [(a.name, a.description) for a in AGENT_ADAPTERS], multi=True)
    if not agents:
        return
    cfg.agents = agents
    caps = menu(stdscr, "FlossWare AI Capabilities", [(c[0], c[1]) for c in CAPABILITIES], selected=[i for i, c in enumerate(CAPABILITIES) if c[2]], multi=True)
    if caps is None:
        return
    cfg.capabilities = caps
    budget = menu(stdscr, "Budget Policy", [(b[0], b[2]) for b in BUDGET_POLICIES], multi=False)
    if budget is None:
        return
    cfg.budget_index = budget
    if BUDGET_POLICIES[budget][1] < 0:
        value = input_screen(stdscr, "Monthly budget ceiling in USD:", "50")
        try:
            cfg.budget_amount = max(0.0, float(value))
        except ValueError:
            cfg.budget_amount = 50.0
    else:
        cfg.budget_amount = BUDGET_POLICIES[budget][1]
    cfg.repo_dir = input_screen(stdscr, "Project directory:", os.getcwd())
    if not (Path(cfg.repo_dir).resolve() / ".git").exists():
        raise ValueError(f"Not a git repository: {Path(cfg.repo_dir).resolve()}")
    key_status(stdscr)
    build(stdscr, cfg)


def main():
    theme_name = "dark"
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print("Usage: python3 scripts/setup.py [--theme NAME]")
        print("Provider credentials are optional; use scripts/install.sh for non-interactive setup.")
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
    except Exception as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
