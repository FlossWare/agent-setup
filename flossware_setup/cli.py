"""Non-interactive FlossWare setup/configuration CLI."""
from __future__ import annotations

import argparse
import json
import os
import subprocess

from flossware_setup.config_control import (DEFAULT_CONSTRAINTS, effective_config, load_order, save_order,
    profile_for_directory, load_profile, validate_effective_config)
from flossware_setup.config_contract import OrderingError, reorder
from flossware_setup.demo import run_demo


def _agent_env(command: list[str]) -> tuple[dict[str, str], str]:
    profile, source = profile_for_directory()
    config = effective_config(profile).resolve()
    validate_effective_config(profile)
    env = os.environ.copy()
    env.update({
        "FLOSSWARE_PROFILE": profile,
        "FLOSSWARE_PROFILE_SOURCE": source or "default/personal",
        "FLOSSWARE_CONFIG": json.dumps(config, separators=(",", ":")),
        "FLOSSWARE_CONFIG_FILE": str((__import__("pathlib").Path.home() / ".flossware" / "ai" / "profiles" / f"{profile}.toml")),
    })
    policy = load_profile(profile).get("model_policy", {})
    allowed = list(policy.get("allowed_providers") or [])
    if allowed and allowed != ["*configured*"]:
        executable = os.path.basename(command[0]).lower()
        if executable not in {"claude", "claude-code"}:
            raise ValueError(f"profile '{profile}' permits only Anthropic coding agents; refusing to launch '{command[0]}'")
        env["FLOSSWARE_ALLOWED_PROVIDERS"] = ",".join(allowed)
    return env, profile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flossware-ai", description="FlossWare configuration control plane")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo", help="run deterministic offline configuration/optimization demo")
    sub.add_parser("tui", help="open the Setup Control Center")
    run = sub.add_parser("run", help="run a coding agent using the profile resolved for the current directory")
    run.add_argument("agent", nargs=argparse.REMAINDER, help="agent command and arguments, for example: claude")
    config = sub.add_parser("config", help="inspect and validate effective configuration")
    config_sub = config.add_subparsers(dest="config_command")
    config_sub.add_parser("show")
    explain = config_sub.add_parser("explain")
    explain.add_argument("key")
    config_sub.add_parser("validate")
    current = config_sub.add_parser("current", help="show the profile selected for the current directory")
    current.add_argument("--json", action="store_true")
    bindings = config_sub.add_parser("bindings", help="show directory-to-profile bindings")
    bindings.add_argument("--json", action="store_true")
    order = config_sub.add_parser("order", help="inspect or modify the persisted menu order")
    order.add_argument("action", choices=("show", "move"))
    order.add_argument("item", nargs="?")
    order.add_argument("direction", nargs="?", choices=("up", "down"))
    args = parser.parse_args(argv)

    if args.command == "demo": return run_demo()
    if args.command == "tui":
        from flossware_setup.tui import main as tui_main
        return tui_main([])
    if args.command == "run":
        if not args.agent: parser.error("run requires an agent command, for example: flossware-ai run claude")
        command = args.agent
        if command[0] == "--": command = command[1:]
        try: env, profile = _agent_env(command)
        except ValueError as exc:
            print(f"Profile policy rejected command: {exc}")
            return 2
        print(f"FlossWare profile: {profile} (directory resolved)")
        return subprocess.call(command, env=env)
    if args.command == "config":
        if args.config_command == "show":
            for key, value in effective_config().resolve().items(): print(f"{key} = {value!r}")
            return 0
        if args.config_command == "explain": print(effective_config().explain(args.key)); return 0
        if args.config_command == "validate": validate_effective_config(); print("Configuration: VALID"); return 0
        if args.config_command == "current":
            profile, source = profile_for_directory()
            data = {"directory": str(__import__("pathlib").Path.cwd()), "profile": profile, "source": source}
            print(json.dumps(data, indent=2) if args.json else f"{data['profile']}\nsource = {data['source'] or 'default/personal'}")
            return 0
        if args.config_command == "bindings":
            from flossware_setup.config_control import load_bindings
            data = load_bindings()
            if args.json: print(json.dumps(data, indent=2))
            else:
                for directory, profile in sorted(data.items()): print(f"{profile:<28} {directory}")
            return 0
        if args.config_command == "order":
            current_order = load_order()
            if args.action == "show": print(" -> ".join(current_order)); return 0
            if not args.item or not args.direction: parser.error("config order move requires ITEM and up|down")
            try: updated = reorder(current_order, args.item, 1 if args.direction == "down" else -1, DEFAULT_CONSTRAINTS); save_order(updated)
            except OrderingError as exc: print(f"Ordering rejected: {exc}"); return 2
            print(" -> ".join(updated)); return 0
    parser.print_help(); return 0


if __name__ == "__main__": raise SystemExit(main())
