#!/usr/bin/env python3
"""Safe provider/account/model discovery for flossware-ai.

Never prints or persists credential values. Model results are cached locally
under ~/.flossware/ai/cache/models and contain public model metadata only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from model_router_ai import discover_accounts, discover_all_models, provider_definitions

ROOT = Path(os.environ.get("FLOSSWARE_AI_ROOT", Path.home() / ".flossware" / "ai"))
CACHE = ROOT / "cache" / "models.json"


def profile() -> str:
    return (ROOT / "state" / "active-profile").read_text().strip() if (ROOT / "state" / "active-profile").exists() else "personal"


def permitted(provider: str, prof: str) -> bool:
    return prof == "personal" or provider == "anthropic"


def providers() -> None:
    configured = {a["provider"] for a in discover_accounts()}
    for p in provider_definitions():
        status = "configured" if p["id"] in configured else "not configured"
        print(f'{p["id"]:<14} {p["name"]:<18} {status}')


def accounts() -> None:
    found = discover_accounts()
    if not found:
        print("No providers configured in the current environment.")
        return
    prof = profile()
    for a in found:
        allowed = permitted(a["provider"], prof)
        print(f'{a["provider"]:<14} {a["id"]:<22} configured  {"allowed" if allowed else "blocked by profile"}')


def models(refresh: bool) -> None:
    prof = profile()
    if refresh or not CACHE.exists():
        found = discover_all_models()
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"timestamp": int(time.time()), "models": found}, indent=2) + "\n")
        try:
            CACHE.chmod(0o600)
        except OSError:
            pass
    else:
        try:
            found = json.loads(CACHE.read_text()).get("models", [])
        except (OSError, json.JSONDecodeError):
            found = []
    visible = [m for m in found if permitted(m.get("provider", ""), prof)]
    if not visible:
        print("No models discovered for the active profile.")
        return
    print(f'{"Provider":<14} {"Model":<60} {"Free-capable":<12}')
    print("-" * 88)
    for m in sorted(visible, key=lambda x: (x.get("provider", ""), x.get("id", ""))):
        print(f'{m.get("provider", ""):<14} {m.get("id", ""):<60} {str(m.get("free_capable", False)):<12}')


def main() -> int:
    parser = argparse.ArgumentParser(description="FlossWare provider/account/model discovery")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("providers")
    sub.add_parser("accounts")
    m = sub.add_parser("models")
    m.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if args.command == "providers": providers()
    elif args.command == "accounts": accounts()
    else: models(args.refresh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
