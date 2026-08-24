#!/usr/bin/env python3
"""Safe provider/account/model discovery for flossware-ai.

Credential values are never printed or persisted. The inventory contains
public model metadata plus capability status only.

Status semantics:
  configured  = usable provider/account credential was detected
  discovered  = provider authenticated and advertised the model
  available   = discovered and permitted by the active profile
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
    prof = profile()
    print(f"FlossWare AI | Providers | profile: {prof}\n")
    print(f'{"Provider":<14} {"Name":<20} Status')
    print("-" * 62)
    for p in provider_definitions():
        status = "configured" if p["id"] in configured else "not configured"
        if not permitted(p["id"], prof) and status == "configured":
            status = "configured / blocked by profile"
        print(f'{p["id"]:<14} {p["name"]:<20} {status}')


def accounts() -> None:
    found = discover_accounts()
    prof = profile()
    print(f"FlossWare AI | Accounts | profile: {prof}\n")
    if not found:
        print("No providers configured in the current environment.")
        return
    print(f'{"Provider":<14} {"Account":<24} {"Credential":<24} Status')
    print("-" * 82)
    for a in found:
        allowed = permitted(a["provider"], prof)
        print(f'{a["provider"]:<14} {a["id"]:<24} {a.get("credential_source", "configured"):<24} {"configured / allowed" if allowed else "configured / blocked"}')


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


def model_status(model: dict, configured: bool, prof: str) -> tuple[str, str, str]:
    """Return configured/access/policy status for a discovered model.

    A model returned by an authenticated provider's model endpoint is treated
    as access-confirmed. Profile policy is evaluated separately.
    """
    discovered = bool(model.get("id"))
    policy = permitted(model.get("provider", ""), prof)
    access = configured and discovered
    status = "available" if access and policy else "blocked by profile" if access else "unavailable"
    return ("yes" if configured else "no", "confirmed" if access else "not confirmed", "allowed" if policy else "blocked")


def models(refresh: bool, free_only: bool, provider: str | None, available_only: bool) -> None:
    prof = profile()
    configured = account_map()
    found = load_models(refresh)
    rows = []
    for m in found:
        p = m.get("provider", "")
        if provider and p != provider:
            continue
        if free_only and not m.get("free_capable", False):
            continue
        cfg, access, policy = model_status(m, p in configured, prof)
        if available_only and not (access == "confirmed" and policy == "allowed"):
            continue
        rows.append((m, cfg, access, policy))

    print(f"FlossWare AI | Models | profile: {prof}\n")
    print("Status: CONFIGURED = credential detected; DISCOVERED = provider authenticated and advertised model; AVAILABLE = discovered + policy allowed.\n")
    if not rows:
        print("No models in the requested inventory.")
        return
    print(f'{"Provider":<14} {"Model":<56} {"Configured":<11} {"Access":<14} {"Policy":<10} Status')
    print("-" * 118)
    for m, cfg, access, policy in sorted(rows, key=lambda x: (x[0].get("provider", ""), x[0].get("id", ""))):
        status = "AVAILABLE" if access == "confirmed" and policy == "allowed" else "BLOCKED" if policy == "blocked" and access == "confirmed" else "UNAVAILABLE"
        print(f'{m.get("provider", ""):<14} {m.get("id", ""):<56} {cfg:<11} {access:<14} {policy:<10} {status}')
    print(f"\n{len(rows)} model(s) in inventory; {sum(1 for _, _, a, p in rows if a == "confirmed" and p == "allowed")} available to the active profile.")


def explain(model_id: str) -> None:
    prof = profile()
    configured = account_map()
    found = load_models(False)
    matches = [m for m in found if m.get("id") == model_id]
    if not matches:
        print(f"Model not found in inventory: {model_id}")
        print("Run: flossware-ai models --refresh")
        return
    for m in matches:
        provider = m.get("provider", "unknown")
        cfg, access, policy = model_status(m, provider in configured, prof)
        status = "AVAILABLE" if access == "confirmed" and policy == "allowed" else "BLOCKED" if policy == "blocked" and access == "confirmed" else "UNAVAILABLE"
        print(f"Model:       {m.get('id', model_id)}")
        print(f"Provider:    {provider}")
        print(f"Profile:     {prof}")
        print(f"Configured:  {cfg}")
        print(f"Access:      {access}")
        print(f"Policy:      {policy}")
        print(f"Status:      {status}")
        print(f"Free:        {'yes' if m.get('free_capable', False) else 'no/unknown'}")
        print("Credential value: not displayed")


def doctor() -> int:
    prof = profile()
    accounts_found = account_map()
    models_found = load_models(False)
    available = [m for m in models_found if m.get("provider", "") in accounts_found and permitted(m.get("provider", ""), prof)]
    print(f"FlossWare AI | Doctor | profile: {prof}\n")
    print(f"Provider definitions: {len(provider_definitions())}")
    print(f"Configured accounts:  {len(accounts_found)}")
    print(f"Discovered models:    {len(models_found)}")
    print(f"Available models:     {len(available)}")
    print(f"Model cache:          {'present' if CACHE.exists() else 'not populated'}")
    print("Credential values:    not displayed")
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
    m.add_argument("--available", action="store_true", dest="available_only")
    e = sub.add_parser("explain")
    e.add_argument("model")
    sub.add_parser("doctor")
    args = parser.parse_args()
    if args.command == "providers": providers()
    elif args.command == "accounts": accounts()
    elif args.command == "models": models(args.refresh, args.free_only, args.provider, args.available_only)
    elif args.command == "explain": explain(args.model)
    else: return doctor()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
