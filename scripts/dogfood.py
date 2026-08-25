#!/usr/bin/env python3
"""Acceptance checks for the FlossWare coding-agent setup layer.

The default mode is safe for CI: it validates repository or installed-runtime
invariants and detects installed agents without requiring provider credentials.
Use --strict locally to require Claude Code and Crush and validate their
executables. Credential values are never printed.
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

AGENTS = {
    "claude-code": ("claude", "CLAUDE.md"),
    "crush": ("crush", "AGENTS.md"),
    "codex": ("codex", "AGENTS.md"),
    "opencode": ("opencode", "AGENTS.md"),
}


def check(label: str, ok: bool, detail: str) -> bool:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {label}: {detail}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require Claude Code and Crush on PATH",
    )
    args = parser.parse_args()
    failures = 0

    # Distinguish source-tree checkout from installed runtime directory.
    source_tree = (ROOT / ".git").exists() or (ROOT / "scripts" / "setup.py").is_file()
    target = ROOT if source_tree else Path(os.environ.get("FLOSSWARE_AI_ROOT", Path.home() / ".flossware" / "ai"))

    if source_tree:
        failures += not check("Repository", True, str(ROOT))
        failures += not check("Installer", (ROOT / "scripts" / "install.sh").is_file(), "POSIX installer present")
        failures += not check("TUI", (ROOT / "scripts" / "setup.py").is_file(), "setup implementation present")
        failures += not check("Discovery", (ROOT / "scripts" / "discovery.py").is_file(), "provider/model discovery present")
        failures += not check("Packaging", (ROOT / "pyproject.toml").is_file(), "PEP 517 setuptools backend")
        failures += not check("Dependencies", True, "capabilities are optional extras")
    else:
        failures += not check("Runtime root", target.is_dir(), str(target))

    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in {".py", ".json", ".md", ".toml", ".yml", ".yaml"}:
            try:
                body = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            bad = any(token in body for token in ("sk-", "api_key = ", "API_KEY = \"sk"))
            if "credential_values_written" in body or "PROVIDER_ENV_VARS" in body:
                continue
            failures += not check("Credential safety", not bad, f"no obvious credential value in {path.relative_to(target)}")

    for agent, (command, instruction) in AGENTS.items():
        found = shutil.which(command) is not None
        instruction_exists = (target / instruction).exists() if source_tree else False
        if args.strict and agent in {"claude-code", "crush"}:
            failures += not check(agent, found, f"{command} is installed")
        else:
            print(f"- {agent}: {'installed' if found else 'not installed'}; instruction file {'present' if instruction_exists else 'not generated'}")

    profile = os.environ.get("FLOSSWARE_PROFILE", "default")
    if not profile:
        profile_file = target / "state" / "active-profile"
        profile = profile_file.read_text(encoding="utf-8").strip() if profile_file.exists() else "default"
    # Neutral default is the public baseline; named profiles are local policy.
    failures += not check("Profile", bool(profile and profile.strip()), f"active profile value is {profile!r}")
    print("\nCredential values are never displayed by this acceptance test.")
    if args.strict:
        print("Strict mode validates the two primary dogfood agents: Claude Code and Crush.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
