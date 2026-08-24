#!/usr/bin/env python3
"""Non-interactive agent integration helper."""
from __future__ import annotations
import argparse, importlib.util, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("flossware_setup", ROOT / "setup.py")
if spec is None or spec.loader is None:
    raise SystemExit("unable to load setup.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
parser = argparse.ArgumentParser(description="Configure one coding agent with FlossWare AI")
parser.add_argument("agent")
parser.add_argument("--repo", default=".")
parser.add_argument("--capability", action="append", dest="capabilities")
args = parser.parse_args()
ids = {a.id: i for i, a in enumerate(mod.AGENT_ADAPTERS)}
if args.agent not in ids:
    raise SystemExit(f"unknown agent: {args.agent}. Use 'flossware-ai agents'.")
selected = args.capabilities or [c[0] for c in mod.CAPABILITIES if c[2]]
cap_ids = {c[0]: i for i, c in enumerate(mod.CAPABILITIES)}
unknown = [c for c in selected if c not in cap_ids]
if unknown:
    raise SystemExit("unknown capability: " + ", ".join(unknown))
cfg = mod.Config(agents=[ids[args.agent]], capabilities=[cap_ids[c] for c in selected], repo_dir=args.repo)
mod.generate_artifacts(cfg)
print(f"Configured {args.agent} for {Path(args.repo).resolve()}")
print("Credential values were not written.")
