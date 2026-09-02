#!/usr/bin/env python3
"""Safe provider/account/model discovery for flossware-ai."""
from __future__ import annotations
import argparse
import json
import os
import time
from pathlib import Path
from model_router_ai import discover_accounts, discover_all_models, provider_definitions

# Identity discovery is owned by model_router_ai.discovery. Always bind from
# the submodule (stable since the discovery module was introduced), then
# prefer a package-root re-export when the installed model-router-ai exposes
# one. This avoids ImportError on older package roots that never listed
# discover_identities in model_router_ai.__all__.
from model_router_ai.discovery import discover_identities as discover_identities

try:
    from model_router_ai import discover_identities as _root_discover_identities
except ImportError:  # pragma: no cover - older package roots
    pass
else:
    discover_identities = _root_discover_identities

ROOT = Path(os.environ.get("FLOSSWARE_AI_ROOT", Path.home() / ".flossware" / "ai"))
CACHE = ROOT / "cache" / "models.json"

def profile() -> str:
    p = ROOT / "state" / "active-profile"
    return p.read_text().strip() if p.exists() else "personal"

def permitted(provider: str, prof: str) -> bool:
    return prof == "personal" or provider == "anthropic"

def account_map():
    return {a["id"]: a for a in discover_accounts()}

def providers() -> None:
    configured = {a["provider"] for a in discover_accounts()}
    prof = profile()
    print(f"FlossWare AI | Providers | profile: {prof}\n")
    print(f'{"Provider":<14} {"Name":<20} Status')
    print("-" * 62)
    for p in provider_definitions():
        status = "configured" if p["id"] in configured else "not configured"
        if not permitted(p["id"], prof) and status == "configured": status = "configured / blocked by profile"
        print(f'{p["id"]:<14} {p["name"]:<20} {status}')

def accounts(verify: bool = False) -> None:
    found = discover_accounts(); prof = profile()
    print(f"FlossWare AI | Accounts | profile: {prof}\n")
    if not found:
        print("No providers configured in the current environment."); return
    identities = {x["account"]: x for x in discover_identities()} if verify else {}
    print(f'{"Provider":<14} {"Account":<22} {"Identity":<28} {"Credential":<22} Status')
    print("-" * 122)
    for a in found:
        ident = identities.get(a["id"], {})
        identity = ident.get("identity") or {}
        identity_text = identity.get("email") or identity.get("name") or identity.get("id") or (ident.get("identity_status", "not checked") if verify else "not checked")
        allowed = permitted(a["provider"], prof)
        verified = ident.get("identity_status") == "verified"
        if verify and verified and allowed: status = "VERIFIED / allowed"
        elif verify and ident.get("identity_status") == "unverified": status = "UNVERIFIED / allowed" if allowed else "UNVERIFIED / blocked"
        else: status = "configured / allowed" if allowed else "configured / blocked"
        print(f'{a["provider"]:<14} {a["label"]:<22} {str(identity_text):<28} {a.get("credential_source", "configured"):<22} {status}')
    if verify:
        print("\nIdentity values come from provider APIs where supported. Credential values are never displayed or stored.")

def load_models(refresh: bool):
    if refresh or not CACHE.exists():
        found = discover_all_models(); CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"timestamp": int(time.time()), "models": found}, indent=2) + "\n")
        try: CACHE.chmod(0o600)
        except OSError: pass
        return found
    try: return json.loads(CACHE.read_text()).get("models", [])
    except (OSError, json.JSONDecodeError): return []

def model_status(model: dict, configured: bool, prof: str) -> tuple[str, str, str]:
    discovered = bool(model.get("id")); policy = permitted(model.get("provider", ""), prof); access = configured and discovered
    return ("yes" if configured else "no", "confirmed" if access else "not confirmed", "allowed" if policy else "blocked")

def models(refresh: bool, free_only: bool, provider: str | None, available_only: bool) -> None:
    prof = profile(); configured = account_map(); found = load_models(refresh); rows = []
    for m in found:
        p = m.get("provider", "")
        if provider and p != provider: continue
        if free_only and not m.get("free_capable", False): continue
        cfg, access, policy = model_status(m, m.get("account") in configured, prof)
        if available_only and not (access == "confirmed" and policy == "allowed"): continue
        rows.append((m, cfg, access, policy))
    print(f"FlossWare AI | Models | profile: {prof}\n")
    print("CONFIGURED = credential detected; DISCOVERED = authenticated provider advertised model; AVAILABLE = discovered + profile policy allowed.\n")
    if not rows: print("No models in the requested inventory."); return
    print(f'{"Provider":<14} {"Account":<20} {"Model":<48} {"Access":<14} {"Policy":<10} Status'); print("-" * 122)
    for m, cfg, access, policy in sorted(rows, key=lambda x: (x[0].get("provider", ""), x[0].get("account", ""), x[0].get("id", ""))):
        status = "AVAILABLE" if access == "confirmed" and policy == "allowed" else "BLOCKED" if policy == "blocked" and access == "confirmed" else "UNAVAILABLE"
        print(f'{m.get("provider", ""):<14} {m.get("account_label", m.get("account", "")):<20} {m.get("id", ""):<48} {access:<14} {policy:<10} {status}')
    available_count = sum(1 for _, _, a, p in rows if a == "confirmed" and p == "allowed")
    print(f"\n{len(rows)} model(s) in inventory; {available_count} available to the active profile.")

def explain(model_id: str) -> None:
    prof = profile(); configured = account_map(); found = load_models(False); matches = [m for m in found if m.get("id") == model_id]
    if not matches: print(f"Model not found in inventory: {model_id}\nRun: flossware-ai models --refresh"); return
    for m in matches:
        provider = m.get("provider", "unknown"); cfg, access, policy = model_status(m, m.get("account") in configured, prof)
        status = "AVAILABLE" if access == "confirmed" and policy == "allowed" else "BLOCKED" if policy == "blocked" and access == "confirmed" else "UNAVAILABLE"
        print(f"Model:       {m.get('id', model_id)}\nProvider:    {provider}\nAccount:     {m.get('account_label', m.get('account', 'unknown'))}\nProfile:     {prof}\nConfigured:  {cfg}\nAccess:      {access}\nPolicy:      {policy}\nStatus:      {status}\nFree:        {'yes' if m.get('free_capable', False) else 'no/unknown'}\nCredential value: not displayed")

def doctor() -> int:
    prof = profile(); accounts_found = account_map(); models_found = load_models(False)
    available = [m for m in models_found if m.get("account") in accounts_found and permitted(m.get("provider", ""), prof)]
    print(f"FlossWare AI | Doctor | profile: {prof}\nProvider definitions: {len(provider_definitions())}\nConfigured accounts:  {len(accounts_found)}\nDiscovered models:    {len(models_found)}\nAvailable models:     {len(available)}\nModel cache:          {'present' if CACHE.exists() else 'not populated'}\nCredential values:    not displayed")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="FlossWare provider/account/model discovery")
    sub = parser.add_subparsers(dest="command", required=True); sub.add_parser("providers")
    a = sub.add_parser("accounts"); a.add_argument("--verify", action="store_true")
    m = sub.add_parser("models"); m.add_argument("--refresh", action="store_true"); m.add_argument("--free", action="store_true", dest="free_only"); m.add_argument("--provider"); m.add_argument("--available", action="store_true", dest="available_only")
    e = sub.add_parser("explain"); e.add_argument("model"); sub.add_parser("doctor")
    args = parser.parse_args()
    if args.command == "providers": providers()
    elif args.command == "accounts": accounts(args.verify)
    elif args.command == "models": models(args.refresh, args.free_only, args.provider, args.available_only)
    elif args.command == "explain": explain(args.model)
    else: return doctor()
    return 0
if __name__ == "__main__": raise SystemExit(main())
