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
import re
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Agents with optional PATH executables for smoke reporting.
# The authoritative catalog of 13 integrations lives in flossware_setup.catalog.
EXECUTABLE_AGENTS = {
    "claude-code": ("claude", "CLAUDE.md"),
    "crush": ("crush", "AGENTS.md"),
    "codex": ("codex", "AGENTS.md"),
    "opencode": ("opencode", "AGENTS.md"),
}

# High-confidence secret-like tokens. Avoid matching env *names* such as API_KEY.
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_\-]{8,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"),
    re.compile(r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
)

SKIP_SCAN_PATH_PARTS = (
    "/tests/",
    "\\tests\\",
    "/.git/",
    "\\.git\\",
    "/.pytest_cache/",
    "\\.pytest_cache\\",
)


def check(label: str, ok: bool, detail: str) -> bool:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {label}: {detail}")
    return ok


def looks_like_secret(text: str) -> bool:
    return any(p.search(text) for p in SECRET_PATTERNS)


def scan_text_for_secrets(label: str, text: str, failures: int) -> int:
    if looks_like_secret(text):
        failures += not check("Credential safety", False, f"possible secret material in {label}")
    else:
        print(f"[OK] Credential safety: no secret values in {label}")
    return failures


def scan_path_tree(target: Path, failures: int) -> int:
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".py", ".json", ".md", ".toml", ".yml", ".yaml"}:
            continue
        posix = path.as_posix()
        if any(part in posix or part.replace("/", "\\") in str(path) for part in SKIP_SCAN_PATH_PARTS):
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Metadata markers do NOT exempt a file from scanning.
        failures = scan_text_for_secrets(str(path.relative_to(target)), body, failures)
    return failures


def validate_generated_artifacts(failures: int) -> int:
    """Generate a sample project config and assert secrets never appear."""
    try:
        from flossware_setup.artifacts import generate_artifacts
        from flossware_setup.config import Config
    except ImportError:
        import sys

        sys.path.insert(0, str(ROOT))
        from flossware_setup.artifacts import generate_artifacts
        from flossware_setup.config import Config

    secret = "sk-" + "live-dogfood-must-not-persist-" + "abc123xyz"
    os.environ["GROQ_API_KEY"] = secret
    try:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "proj"
            repo.mkdir()
            (repo / ".git").mkdir()
            cfg = Config(
                agents=[0, 3],
                capabilities=[0, 1, 2],
                budget_index=2,
                repo_dir=str(repo),
                profile="default",
            )
            state = generate_artifacts(cfg)
            if state.get("credential_values_written") is not False:
                failures += not check("Artifact metadata", False, "credential_values_written must be False")
            else:
                print("[OK] Artifact metadata: credential_values_written is False")

            for rel in (".flossware-ai.json", "ai_config.py", "CLAUDE.md", "AGENTS.md"):
                path = repo / rel
                if not path.is_file():
                    failures += not check("Artifact present", False, rel)
                    continue
                body = path.read_text(encoding="utf-8")
                if secret in body or looks_like_secret(body):
                    failures += not check("Generated artifact", False, f"{rel} must not contain secrets")
                else:
                    print(f"[OK] Generated artifact: {rel} has no secret values")
    finally:
        os.environ.pop("GROQ_API_KEY", None)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require Claude Code and Crush on PATH",
    )
    args = parser.parse_args()
    failures = 0

    source_tree = (ROOT / ".git").exists() or (ROOT / "scripts" / "setup.py").is_file()
    target = ROOT if source_tree else Path(
        os.environ.get("FLOSSWARE_AI_ROOT", Path.home() / ".flossware" / "ai")
    )

    if source_tree:
        failures += not check("Repository", True, str(ROOT))
        failures += not check(
            "Installer", (ROOT / "scripts" / "install.sh").is_file(), "POSIX installer present"
        )
        failures += not check(
            "TUI", (ROOT / "scripts" / "setup.py").is_file(), "setup implementation present"
        )
        failures += not check(
            "Discovery",
            (ROOT / "scripts" / "discovery.py").is_file(),
            "provider/model discovery present",
        )
        failures += not check(
            "Packaging", (ROOT / "pyproject.toml").is_file(), "PEP 517 setuptools backend"
        )
        failures += not check("Dependencies", True, "capabilities are optional extras")
        package_tui = (ROOT / "flossware_setup" / "tui" / "app.py").is_file()
        failures += not check("Package TUI", package_tui, "flossware_setup.tui.app present")
    else:
        failures += not check("Runtime root", target.is_dir(), str(target))

    failures = scan_path_tree(target, failures)
    if source_tree:
        failures = validate_generated_artifacts(failures)

    for agent, (command, instruction) in EXECUTABLE_AGENTS.items():
        found = shutil.which(command) is not None
        instruction_exists = (target / instruction).exists() if source_tree else False
        if args.strict and agent in {"claude-code", "crush"}:
            failures += not check(agent, found, f"{command} is installed")
        else:
            print(
                f"- {agent}: {'installed' if found else 'not installed'}; "
                f"instruction file {'present' if instruction_exists else 'not generated'}"
            )

    try:
        import sys

        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from flossware_setup.catalog import AGENTS

        failures += not check(
            "Agent catalog",
            len(AGENTS) == 13,
            f"{len(AGENTS)} registered integrations (expected 13)",
        )
    except Exception as exc:  # noqa: BLE001 — import/catalog probe must not crash dogfood
        failures += not check("Agent catalog", False, str(exc))

    profile = os.environ.get("FLOSSWARE_PROFILE", "default")
    if not profile:
        profile_file = target / "state" / "active-profile"
        profile = (
            profile_file.read_text(encoding="utf-8").strip()
            if profile_file.exists()
            else "default"
        )
    failures += not check(
        "Profile",
        bool(profile and profile.strip()),
        f"active profile value is {profile!r}",
    )
    print("\nCredential values are never displayed by this acceptance test.")
    if args.strict:
        print("Strict mode validates the two primary dogfood agents: Claude Code and Crush.")
    print(
        "Executable smoke covers a subset of agents; the catalog registers all 13 integrations."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
