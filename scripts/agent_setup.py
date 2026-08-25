"""Non-interactive agent integration helper.

Uses the flossware_setup package catalog (AGENTS) and artifact generator.
Credential values are never written.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from flossware_setup.artifacts import generate_artifacts
from flossware_setup.catalog import AGENTS, CAPABILITIES
from flossware_setup.config import Config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Configure one coding agent with FlossWare AI"
    )
    parser.add_argument("agent")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--capability", action="append", dest="capabilities")
    args = parser.parse_args(argv)

    ids = {a.id for a in AGENTS}
    if args.agent not in ids:
        print(
            f"unknown agent: {args.agent}. Known: {', '.join(sorted(ids))}",
            file=sys.stderr,
        )
        return 1

    selected = args.capabilities or [c[0] for c in CAPABILITIES if c[2]]
    known_caps = {c[0] for c in CAPABILITIES}
    unknown = [c for c in selected if c not in known_caps]
    if unknown:
        print("unknown capability: " + ", ".join(unknown), file=sys.stderr)
        return 1

    cfg = Config(
        agents=[args.agent],
        capabilities=list(selected),
        repo_dir=args.repo,
    )
    generate_artifacts(cfg)
    print(f"Configured {args.agent} for {Path(args.repo).resolve()}")
    print("Credential values were not written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
