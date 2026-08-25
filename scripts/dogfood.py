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
INSTALL_ROOT = Path(os.environ.get("FLOSSWARE_AI_ROOT", Path.home() / ".flossware" / "ai"))
AGENTS = {
    "claude-code": ("claude", "CLAUDE.md"),
    "crush": ("crush", "AGENTS.md"),
    "codex": ("codex", "AGENTS.md"),
    "opencode": ("opencode", "AGENTS.md"),
}
SECRET_MARKERS = (
    "sk-", "AIza", "Bearer ", "api_key=", "api-key=", "access_token=",
)


def check(name: str, ok: bool, detail: str) -> bool:
    marker = "OK" if ok else "FAIL"
    print(f"[{marker}] {name}: {detail}")
    return ok


def is_source_tree() -> bool:
    return (ROOT / ".git").exists() and (ROOT / "scripts" / "install.sh").is_file()


def main() -> int:
    parser = argparse.ArgumentParser(description="FlossWare coding-agent dogfood acceptance checks")
    parser.add_argument("--strict", action="store_true", help="require Claude Code and Crush to be installed")
    args = parser.parse_args()
    failures = 0
    source_tree = is_source_tree()
    target = ROOT if source_tree else INSTALL_ROOT

    if source_tree:
        failures += not check("Repository", True, str(ROOT))
        failures += not check("Installer", (ROOT / "scripts" / "install.sh").is_file(), "POSIX installer present")
        failures += not check("TUI", (ROOT / "scripts" / "setup.py").is_file(), "setup implementation present")
        failures += not check("Discovery", (ROOT / "scripts" / "discovery.py").is_file(), "provider/model discovery present")
        pyproject = ROOT / "pyproject.toml"
        text = pyproject.read_text(encoding="utf-8") if pyproject.exists() else ""
        failures += not check("Packaging", "build-backend = \"setuptools.build_meta\"" in text, "PEP 517 setuptools backend")
        failures += not check("Dependencies", "[project.optional-dependencies]" in text, "capabilities are optional extras")
    else:
        failures += not check("Installation", target.is_dir(), f"installed runtime at {target}")
        failures += not check("Installer", (target / "coding-agent-setup" / "scripts" / "install.sh").is_file(), "installer payload present")
        failures += not check("TUI", (target / "setup.py").is_file(), "setup implementation present")
        failures += not check("Discovery", (target / "discovery.py").is_file(), "provider/model discovery present")
        failures += not check("Acceptance", (target / "dogfood.py").is_file(), "dogfood acceptance runtime present")

    generated = list(target.glob("**/.flossware-ai.json"))
    for path in generated:
        body = path.read_text(encoding="utf-8", errors="replace")
        bad = any(marker in body for marker in SECRET_MARKERS)
        failures += not check("Credential safety", not bad, f"no obvious credential value in {path.relative_to(target)}")

    for agent, (command, instruction) in AGENTS.items():
        found = shutil.which(command) is not None
        instruction_exists = (target / instruction).exists() if source_tree else False
        if args.strict and agent in {"claude-code", "crush"}:
            failures += not check(agent, found, f"{command} is installed")
        else:
            print(f"- {agent}: {'installed' if found else 'not installed'}; instruction file {'present' if instruction_exists else 'not generated'}")

    profile = os.environ.get("FLOSSWARE_PROFILE", "personal")
    if not profile or profile not in {"personal", "redhat"}:
        profile_file = target / "state" / "active-profile"
        profile = profile_file.read_text(encoding="utf-8").strip() if profile_file.exists() else "personal"
    failures += not check("Profile", profile in {"personal", "redhat"}, f"active profile value is {profile!r}")
    print("\nCredential values are never displayed by this acceptance test.")
    if args.strict:
        print("Strict mode validates the two primary dogfood agents: Claude Code and Crush.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
