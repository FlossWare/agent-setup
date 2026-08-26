"""Non-interactive FlossWare setup/configuration CLI."""
from __future__ import annotations
import argparse
from flossware_setup.demo import run_demo
from flossware_setup.config_contract import ConfigLayer, ConfigResolver, Policy


def _resolver() -> ConfigResolver:
    r = ConfigResolver()
    r.add_layer(ConfigLayer("defaults", 0, {"provider": "anthropic", "budget.monthly": 300.0, "optimization.population": 30}))
    return r


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="flossware-ai", description="FlossWare configuration control plane")
    sub = p.add_subparsers(dest="command")
    sub.add_parser("demo", help="run deterministic offline configuration/optimization demo")
    config = sub.add_parser("config", help="inspect and validate effective configuration")
    config_sub = config.add_subparsers(dest="config_command")
    config_sub.add_parser("show")
    explain = config_sub.add_parser("explain")
    explain.add_argument("key")
    config_sub.add_parser("validate")
    args = p.parse_args(argv)
    if args.command == "demo": return run_demo()
    if args.command == "config":
        r = _resolver()
        if args.config_command == "show":
            for k, v in r.resolve().items(): print(f"{k} = {v!r}")
            return 0
        if args.config_command == "explain":
            print(r.explain(args.key)); return 0
        if args.config_command == "validate":
            Policy(allowed={"provider": ["anthropic"]}).validate(r.resolve())
            print("Configuration: VALID"); return 0
    p.print_help()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
