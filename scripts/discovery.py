#!/usr/bin/env python3
"""Safe provider/account/model discovery for flossware-ai.

Credential values are never printed or persisted. The inventory contains
public model metadata plus capability status only.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from model_router_ai import discover_accounts, discover_all_models, provider_definitions

ROOT = Path(os.environ.get("FLOSSWARE_AI_ROOT", Path.home() / ".flossware" / "ai"))
CACHE = ROOT / "cache" / "models.json"


def profile() -> str:
    p = ROOT / "state" / "active-profile"
    return p.read_text().strip() if p.exists() else "personal"


def permitted(provider: str, prof: str) -> bool:
    return prof == "personal" or provider == "anthropic"


def account_map():
    return {a["provider"]: a for a in discover_accounts()}


def providers() -> None:
    configured = account_map()
    print(f"FlossWare AI | Providers | profile: {profile()}\n")
    print(f'{"Provider":<14} {"Name":<20} Status')
    print("-" * 55)
    for p in provider_definitions():
        status = "configured" if p["id"] in configured else "not configured"
        if not permitted(p["id"], profile()) and status == "configured":
            status = "configured / blocked by profile"
        print(f'{p["id"]:<14} {p["name"]:<20} {status}')


def accounts() -> None:
    found = discover_accounts()
    prof = profile()
    print(f"FlossWare AI | Accounts | profile: {prof}\n")
    if not found:
        print("No providers configured in the current environment.")
        return
    print(f'{"Provider":<14} {"Account":<24} {"Credential":<12} Status')
    print("-" * 70)
    for a in found:
        allowed = permitted(a["provider"], prof)
        print(f'{a["provider"]:<14} {a["id"]:<24} {a.get("auth_type", "configured"):<12} {"allowed" if allowed else "blocked by profile"}')


def load_models(refresh: bool):
    if refresh or not CACHE.exists():
        found = discover_all_models()
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"timestamp": int(time.time()), "models": found}, indent=2) + "\n")
        try:
            CACHE.chmod(0o600)
        except OSError:
            pass
        return found
    try:
        return json.loads(CACHE.read_text()).get("models", [])
    except (OSError, json.JSONDecodeError):
        return []


def models(refresh: bool, free_only: bool, provider: str | None) -> None:
    prof = profile()
    found = load_models(refresh)
    visible = [m for m in found if permitted(m.get("provider", ""), prof)]
    if provider:
        visible = [m for m in visible if m.get("provider") == provider]
    if free_only:
        visible = [m for m in visible if m.get("free_capable", False)]
    print(f"FlossWare AI | Available Models | profile: {prof}\n")
    if not visible:
        print("No models discovered for the active profile.")
        return
    print(f'{"Provider":<14} {"Model":<60} {"Access":<10} {"Cost":<12}')
    print("-" * 100)
    for m in sorted(visible, key=lambda x: (x.get("provider", ""), x.get("id", ""))):
        cost = "free-capable" if m.get("free_capable", False) else "paid/unknown"
        access = "available" if m.get("available", True) else "discovered"
        print(f'{m.get("provider", ""):<14} {m.get("id", ""):<60} {access:<10} {cost:<12}')
    print(f"\n{len(visible)} model(s) visible to the active profile.")


def explain(model_id: str) -> None:
    prof = profile()
    found = load_models(False)
    matches = [m for m in found if m.get("id") == model_id]
    if not matches:
        print(f"Model not found in inventory: {model_id}")
        print("Run: flossware-ai models --refresh")
        return
    for m in matches:
        provider = m.get("provider", "unknown")
        print(f"Model:       {m.get('id', model_id)}")
        print(f"Provider:    {provider}")
        print(f"Profile:     {prof}")
        print(f"Credential:  {'configured' if provider in account_map() else 'not configured'}")
        print(f"Policy:      {'allowed' if permitted(provider, prof) else 'blocked by profile'}")
        print(f"Access:      {'available' if m.get('available', True) else 'discovered only'}")
        print(f"Free:        {'yes' if m.get('free_capable', False) else 'no/unknown'}")
        print("Credential value: not displayed")


def doctor() -> int:
    prof = profile()
    accounts_found = account_map()
    models_found = load_models(False)
    visible = [m for m in models_found if permitted(m.get("provider", ""), prof)]
    print(f"FlossWare AI | Doctor | profile: {prof}\n")
    print(f"Provider definitions: {len(provider_definitions())}")
    print(f"Configured accounts:  {len(accounts_found)}")
    print(f"Visible models:      {len(visible)}")
    print(f"Model cache:         {'present' if CACHE.exists() else 'not populated'}")
    print("Credential values:   not displayed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="FlossWare provider/account/model discovery")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("providers")
    sub.add_parser("accounts")
    m = sub.add_parser("models")
    m.add_argument("--refresh", action="store_true")
    m.add_argument("--free", action="store_true", dest="free_only")
    m.add_argument("--provider")
    e = sub.add_parser("explain")
    e.add_argument("model")
    sub.add_parser("doctor")
    args = parser.parse_args()
    if args.command == "providers": providers()
    elif args.command == "accounts": accounts()
    elif args.command == "models": models(args.refresh, args.free_only, args.provider)
    elif args.command == "explain": explain(args.model)
    else: return doctor()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
