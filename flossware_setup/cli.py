"""Non-interactive FlossWare setup/configuration CLI."""
from __future__ import annotations

import argparse
import json
import os
import subprocess

from flossware_setup.config_control import (
    DEFAULT_CONSTRAINTS,
    available_profiles,
    create_profile,
    effective_config,
    load_active_profile,
    load_order,
    load_profile,
    profile_for_directory,
    save_active_profile,
    save_order,
    update_profile,
    validate_effective_config,
    validate_profile_data,
)
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
        "FLOSSWARE_CONFIG_FILE": str((__import__("flossware_setup.config_control", fromlist=["state_dir"]).state_dir() / "profiles" / f"{profile}.toml")),
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
    tui_p = sub.add_parser("tui", help="open the Setup Control Center")
    tui_p.add_argument("tui_args", nargs=argparse.REMAINDER, help="arguments forwarded to the TUI (e.g. --theme dbase4)")
    run = sub.add_parser("run", help="run a coding agent using the profile resolved for the current directory")
    run.add_argument("agent", nargs=argparse.REMAINDER, help="agent command and arguments, for example: claude")
    setup = sub.add_parser("setup", help="provision supported coding-agent integrations")
    setup_sub = setup.add_subparsers(dest="setup_command")
    crush = setup_sub.add_parser("crush", help="configure Crush with the FlossWare free/local gateway")
    crush.add_argument("--free-only", action="store_true", default=True, help="use only the free/local FlossWare gateway")
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

    profile_p = sub.add_parser("profile", help="create, select, inspect, and edit configuration profiles")
    profile_sub = profile_p.add_subparsers(dest="profile_command")
    profile_sub.add_parser("list", help="list available profiles")
    p_show = profile_sub.add_parser("show", help="show a profile document")
    p_show.add_argument("name", nargs="?", default=None, help="profile name (default: active)")
    p_show.add_argument("--json", action="store_true")
    p_create = profile_sub.add_parser("create", help="create a profile from a template")
    p_create.add_argument("name")
    p_create.add_argument("--from", dest="template", default="default", help="template profile (default: default)")
    p_select = profile_sub.add_parser("select", help="set the active profile")
    p_select.add_argument("name")
    p_edit = profile_sub.add_parser("edit", help="update editable profile policy fields")
    p_edit.add_argument("name")
    p_edit.add_argument("--allow-local-models", dest="allow_local_models", choices=("true", "false"))
    p_edit.add_argument("--allow-personal-accounts", dest="allow_personal_accounts", choices=("true", "false"))
    p_edit.add_argument("--allow-provider-fallback", dest="allow_provider_fallback", choices=("true", "false"))
    p_edit.add_argument("--allow-unconfigured-providers", dest="allow_unconfigured_providers", choices=("true", "false"))
    p_edit.add_argument("--providers", help="comma-separated allowed provider refs or *configured*")
    p_edit.add_argument("--monthly-limit", type=float, help="monthly budget USD")
    p_edit.add_argument("--hard-limit", choices=("true", "false"))
    p_val = profile_sub.add_parser("validate", help="validate a profile document")
    p_val.add_argument("name", nargs="?", default=None)

    args = parser.parse_args(argv)


    if args.command == "demo": return run_demo()
    if args.command == "tui":
        from flossware_setup.tui import main as tui_main
        rest = list(getattr(args, "tui_args", []) or [])
        if rest and rest[0] == "--":
            rest = rest[1:]
        return tui_main(rest)
    if args.command == "setup":
        if args.setup_command == "crush":
            from flossware_setup.crush_setup import setup_crush
            try:
                return setup_crush(free_only=args.free_only)
            except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
                print(f"Crush setup failed: {exc}")
                return 2
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
            profile, source = profile_for_directory()
            print(f"# profile={profile} source={source or 'default'}")
            for key, value in effective_config(profile).resolve().items():
                print(f"{key} = {value!r}")
            return 0
        if args.config_command == "explain":
            profile, _ = profile_for_directory()
            print(effective_config(profile).explain(args.key))
            return 0
        if args.config_command == "validate":
            profile, source = profile_for_directory()
            try:
                validate_effective_config(profile)
            except ValueError as exc:
                print(f"Configuration: INVALID ({profile} / {source or 'default'}): {exc}")
                return 2
            print(f"Configuration: VALID (profile={profile}, source={source or 'default'})")
            return 0
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

    if getattr(args, "command", None) == "profile":
        def _bool_arg(raw):
            return None if raw is None else raw == "true"
        if args.profile_command == "list":
            active = load_active_profile()
            for name in available_profiles():
                mark = "*" if name == active else " "
                print(f"{mark} {name}")
            return 0
        if args.profile_command == "show":
            name = args.name or load_active_profile()
            try:
                data = load_profile(name)
            except ValueError as exc:
                print(f"Profile error: {exc}")
                return 2
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                print(f"profile = {name}")
                for key, value in data.items():
                    print(f"{key} = {value!r}")
            return 0
        if args.profile_command == "create":
            try:
                path = create_profile(args.name, template=args.template)
            except ValueError as exc:
                print(f"Profile create failed: {exc}")
                return 2
            print(f"Created profile {args.name} at {path}")
            return 0
        if args.profile_command == "select":
            try:
                path = save_active_profile(args.name)
            except ValueError as exc:
                print(f"Profile select failed: {exc}")
                return 2
            print(f"Active profile: {args.name} ({path})")
            return 0
        if args.profile_command == "edit":
            values = {}
            mapping = {
                "allow_local_models": _bool_arg(getattr(args, "allow_local_models", None)),
                "allow_personal_accounts": _bool_arg(getattr(args, "allow_personal_accounts", None)),
                "allow_provider_fallback": _bool_arg(getattr(args, "allow_provider_fallback", None)),
                "allow_unconfigured_providers": _bool_arg(getattr(args, "allow_unconfigured_providers", None)),
                "hard_limit": _bool_arg(getattr(args, "hard_limit", None)),
            }
            for key, value in mapping.items():
                if value is not None:
                    values[key] = value
            if getattr(args, "providers", None):
                values["allowed_providers"] = [part.strip() for part in args.providers.split(",") if part.strip()]
            if getattr(args, "monthly_limit", None) is not None:
                values["monthly_limit_usd"] = args.monthly_limit
            try:
                path = update_profile(args.name, values or None)
            except ValueError as exc:
                print(f"Profile edit failed: {exc}")
                return 2
            print(f"Updated profile {args.name} at {path}")
            return 0
        if args.profile_command == "validate":
            name = args.name or load_active_profile()
            try:
                data = load_profile(name)
                validate_profile_data(data, name=name)
                validate_effective_config(name)
            except ValueError as exc:
                print(f"Profile INVALID ({name}): {exc}")
                return 2
            print(f"Profile VALID ({name})")
            return 0
        profile_p.print_help()
        return 0

    parser.print_help(); return 0


if __name__ == "__main__": raise SystemExit(main())
