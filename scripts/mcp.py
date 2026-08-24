#!/usr/bin/env python3
"""Generate safe, agent-neutral FlossWare MCP configuration.

The generated configuration contains only the command needed to start the
local FlossWare router. Provider credentials are inherited by the router
process and are never copied into agent configuration.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get("FLOSSWARE_AI_ROOT", Path.home() / ".flossware" / "ai"))
ROUTER = ROOT / "venv" / "bin" / "python"
SERVER = ROOT / "router_mcp.py"


def server_command() -> list[str]:
    return [str(ROUTER), str(SERVER)]


def config(agent: str) -> dict:
    command = server_command()
    if agent == "claude":
        return {"mcpServers": {"flossware": {"type": "stdio", "command": command[0], "args": command[1:]}}}
    if agent == "opencode":
        return {"$schema": "https://opencode.ai/config.json", "mcp": {"servers": {"flossware": {"type": "local", "command": command}}}}
    if agent in {"crush", "codex", "cursor", "aider", "cline", "roo-code", "gemini-cli", "github-copilot", "windsurf", "amazon-q", "kiro"}:
        return {"name": "flossware", "transport": "stdio", "command": command[0], "args": command[1:]}
    raise SystemExit(f"unsupported agent: {agent}")


def main() -> int:
    p = argparse.ArgumentParser(description="FlossWare MCP configuration generator")
    p.add_argument("agent", choices=("claude", "opencode", "crush", "codex", "cursor", "aider", "cline", "roo-code", "gemini-cli", "github-copilot", "windsurf", "amazon-q", "kiro"))
    p.add_argument("--print", action="store_true", dest="print_only")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    payload = config(args.agent)
    text = json.dumps(payload, indent=2) + "\n"
    if args.print_only or args.output is None:
        print(text, end="")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing agent configuration: {args.output}")
    args.output.write_text(text, encoding="utf-8")
    try: args.output.chmod(0o600)
    except OSError: pass
    print(f"Wrote FlossWare MCP configuration: {args.output}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
