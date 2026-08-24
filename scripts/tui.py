#!/usr/bin/env python3
"""FlossWare AI interactive control-plane TUI.

Keyboard-first, mouse-friendly curses UI.  The selected item's description is
always shown in the status/help line so users can understand capabilities
without memorizing FlossWare component names.
"""
from __future__ import annotations

import curses
import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    name: str
    description: str


AGENTS = [
    Item("Claude Code", "Anthropic coding agent; reads CLAUDE.md project instructions."),
    Item("Crush", "Charmbracelet coding agent; uses shared AGENTS.md context and FlossWare MCP."),
    Item("Codex", "OpenAI coding agent; uses AGENTS.md project instructions."),
    Item("OpenCode", "Provider-neutral coding agent; uses AGENTS.md and configured models."),
    Item("Cursor", "AI editor; uses .cursorrules project guidance."),
    Item("Aider", "Terminal pair-programming agent; uses FlossWare conventions."),
    Item("Cline", "VS Code coding agent; uses .clinerules project guidance."),
    Item("Roo Code", "VS Code agent; uses .roo/rules project guidance."),
    Item("Gemini CLI", "Google coding CLI; uses GEMINI.md project instructions."),
    Item("GitHub Copilot", "GitHub coding assistant; uses repository instructions."),
    Item("Windsurf", "AI IDE; uses .windsurfrules project guidance."),
    Item("Amazon Q", "AWS coding assistant; uses .amazonq project rules."),
    Item("Kiro", "AWS agentic IDE; uses .kiro steering files."),
]

COMPONENTS = [
    Item("model-router-ai", "Model routing: selects eligible models/providers using policy, capability, cost, and failover rules."),
    Item("resilience-ai", "Resilience: retries, timeouts, circuit breakers, and graceful failure handling."),
    Item("structured-output-ai", "Structured output: validates model responses against explicit schemas."),
    Item("consensus-ai", "Consensus: combines multiple model responses using voting and verification strategies."),
    Item("evaluation-ai", "Evaluation: scores outputs and supports adversarial/quality verification."),
    Item("observability-ai", "Observability: exposes logs, metrics, traces, usage, and cost information."),
    Item("security-ai", "Security: validates inputs, masks secrets, and provides security/audit controls."),
    Item("rag-ai", "RAG: retrieves relevant knowledge and context for model requests."),
    Item("genetic-optimizer-ai", "Optimization: searches configuration/task strategies using evolutionary methods."),
]

MENUS = [
    Item("Agents", "Configure which coding agents receive FlossWare project context and integrations."),
    Item("Components", "Select independent FlossWare AI capabilities that agents or Loom can consume."),
    Item("Accounts / Models", "Inspect configured accounts, credential sources, policies, and discoverable models."),
    Item("Doctor", "Run FlossWare AI diagnostics and report configuration or dependency problems."),
    Item("Exit", "Leave the FlossWare AI control panel."),
]


def setup_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    for pair, fg in enumerate((curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_YELLOW,
                               curses.COLOR_RED, curses.COLOR_WHITE, curses.COLOR_MAGENTA), 1):
        curses.init_pair(pair, fg, -1)


def draw_header(win, title: str) -> int:
    win.erase()
    _, width = win.getmaxyx()
    line = "=" * min(76, max(10, width - 4))
    win.addstr(1, 2, line, curses.color_pair(1))
    win.addstr(2, 2, f" FlossWare AI | {title}", curses.color_pair(1) | curses.A_BOLD)
    win.addstr(3, 2, line, curses.color_pair(1))
    return 5


def safe_add(win, y: int, x: int, text: str, attr: int = 0) -> None:
    h, w = win.getmaxyx()
    if 0 <= y < h - 1 and x < w - 1:
        try:
            win.addnstr(y, x, text, max(1, w - x - 1), attr)
        except curses.error:
            pass


def status_line(win, item: Item | None, hint: str = "") -> None:
    h, _ = win.getmaxyx()
    safe_add(win, h - 3, 2, "STATUS: " + (item.description if item else hint), curses.color_pair(6))
    safe_add(win, h - 2, 2, "↑/↓ move  Space select  Enter open/confirm  / search  q back", curses.color_pair(5))


def menu(win, title: str, items: list[Item], multi: bool = False) -> list[int] | int | None:
    cursor = 0
    selected: set[int] = set()
    query = ""
    while True:
        filtered = [(i, item) for i, item in enumerate(items) if query.lower() in item.name.lower()]
        if not filtered:
            filtered = []
        if cursor >= len(filtered):
            cursor = max(0, len(filtered) - 1)
        y = draw_header(win, title)
        for row, (_, item) in enumerate(filtered):
            if y + row >= win.getmaxyx()[0] - 4:
                break
            idx = filtered[row][0]
            mark = "[x]" if idx in selected else "[ ]" if multi else ("(o)" if row == cursor else "( )")
            attr = curses.A_REVERSE if row == cursor else 0
            safe_add(win, y + row, 2, f"{'> ' if row == cursor else '  '}{mark} {item.name}", attr)
        current = filtered[cursor][1] if filtered else None
        status_line(win, current, "No matching items." if query else "Select an item.")
        safe_add(win, 0, max(2, win.getmaxyx()[1] - 30), f"Filter: {query}" if query else "", curses.color_pair(3))
        win.refresh()
        key = win.getch()
        if key in (curses.KEY_UP, ord('k')):
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN, ord('j')):
            cursor = min(max(0, len(filtered) - 1), cursor + 1)
        elif key == ord('/'):
            curses.echo()
            try:
                safe_add(win, 0, 2, "Search: ")
                query = win.getstr(0, 10, 60).decode(errors="replace").strip()
            finally:
                curses.noecho()
            cursor = 0
        elif key in (curses.KEY_BACKSPACE, 127, 8) and query:
            query = query[:-1]
            cursor = 0
        elif key == ord(' ') and multi and filtered:
            selected.symmetric_difference_update({filtered[cursor][0]})
        elif key == ord('a') and multi:
            selected = {i for i, _ in filtered}
        elif key == ord('n') and multi:
            selected.clear()
        elif key in (10, 13, curses.KEY_ENTER):
            if not filtered:
                continue
            return sorted(selected) if multi else filtered[cursor][0]
        elif key in (ord('q'), 27):
            return None


def pause(win, title: str, message: str) -> None:
    y = draw_header(win, title)
    safe_add(win, y, 2, message, curses.color_pair(2))
    safe_add(win, y + 2, 2, "Press any key to return.", curses.color_pair(6))
    win.refresh()
    win.getch()


def main_menu(win) -> None:
    while True:
        choice = menu(win, "Control Plane", MENUS)
        if choice is None or choice == 4:
            return
        if choice == 0:
            ids = menu(win, "Coding Agents", AGENTS, multi=True)
            if ids is not None:
                names = ", ".join(AGENTS[i].name for i in ids)
                pause(win, "Agents", f"Selected: {names or 'none'}")
        elif choice == 1:
            ids = menu(win, "FlossWare AI Components", COMPONENTS, multi=True)
            if ids is not None:
                names = ", ".join(COMPONENTS[i].name for i in ids)
                pause(win, "Components", f"Selected: {names or 'none'}")
        elif choice == 2:
            profile = os.environ.get("FLOSSWARE_PROFILE", "personal")
            pause(win, "Accounts / Models", f"Active profile: {profile}. Use accounts --verify and models --available for live discovery.")
        elif choice == 3:
            root = os.environ.get("FLOSSWARE_AI_ROOT", os.path.expanduser("~/.flossware/ai"))
            python = os.path.join(root, "venv", "bin", "python")
            discovery = os.path.join(root, "discovery.py")
            if os.path.exists(python) and os.path.exists(discovery):
                proc = subprocess.run([python, discovery, "doctor"], capture_output=True, text=True, timeout=60)
                pause(win, "Doctor", proc.stdout or proc.stderr or "No diagnostic output.")
            else:
                pause(win, "Doctor", f"Managed discovery runtime not found under {root}.")


def main() -> int:
    try:
        curses.wrapper(lambda win: (curses.curs_set(0), win.keypad(True), setup_colors(), main_menu(win)))
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
