"""Non-interactive FlossWare setup/configuration CLI."""
from __future__ import annotations

import argparse

from flossware_setup.config_control import DEFAULT_CONSTRAINTS, effective_config, load_order, save_order, validate_effective_config
from flossware_setup.config_contract import OrderingError, reorder
from flossware_setup.demo import run_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flossware-ai", description="FlossWare configuration control plane")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo", help="run deterministic offline configuration/optimization demo")
    sub.add_parser("tui", help="open the Setup Control Center")
    config = sub.add_parser("config", help="inspect and validate effective configuration")
    config_sub = config.add_subparsers(dest="config_command")
    config_sub.add_parser("show")
    explain = config_sub.add_parser("explain")
    explain.add_argument("key")
    config_sub.add_parser("validate")
    order = config_sub.add_parser("order", help="inspect or modify the persisted menu order")
    order.add_argument("action", choices=("show", "move"))
    order.add_argument("item", nargs="?")
    order.add_argument("direction", nargs="?", choices=("up", "down"))
    args = parser.parse_args(argv)

    if args.command == "demo":
        return run_demo()
    if args.command == "tui":
        from flossware_setup.tui import main as tui_main
        return tui_main([])
    if args.command == "config":
        if args.config_command == "show":
            for key, value in effective_config().resolve().items():
                print(f"{key} = {value!r}")
            return 0
        if args.config_command == "explain":
            print(effective_config().explain(args.key))
            return 0
        if args.config_command == "validate":
            validate_effective_config()
            print("Configuration: VALID")
            return 0
        if args.config_command == "order":
            current = load_order()
            if args.action == "show":
                print(" -> ".join(current))
                return 0
            if not args.item or not args.direction:
                parser.error("config order move requires ITEM and up|down")
            try:
                updated = reorder(current, args.item, 1 if args.direction == "down" else -1, DEFAULT_CONSTRAINTS)
                save_order(updated)
            except OrderingError as exc:
                print(f"Ordering rejected: {exc}")
                return 2
            print(" -> ".join(updated))
            return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
