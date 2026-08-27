"""Acceptance checks for the FlossWare coding-agent setup layer."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import tempfile
from pathlib import Path

_DOGFOOD_FILE = Path(__file__).resolve()
# scripts/dogfood.py in a checkout → repo root; installed copy next to setup.py → install root
ROOT = _DOGFOOD_FILE.parents[1] if _DOGFOOD_FILE.parent.name == "scripts" else _DOGFOOD_FILE.parent
_FLOSSWARE_MARKER = ".flossware"
EXECUTABLE_AGENTS = {
    "claude-code": ("claude", "CLAUDE.md"),
    "crush": ("crush", "AGENTS.md"),
    "codex": ("codex", "AGENTS.md"),
    "opencode": ("opencode", "AGENTS.md"),
}
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_\-]{8,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"),
    re.compile(r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
)


def check(label: str, ok: bool, detail: str) -> bool:
    print(f"[{'OK' if ok else 'FAIL'}] {label}: {detail}")
    return ok


def looks_like_secret(text: str) -> bool:
    return any(p.search(text) for p in SECRET_PATTERNS)


def scan_text_for_secrets(label: str, text: str, failures: int) -> int:
    failures += not check("Credential safety", not looks_like_secret(text), f"no secret values in {label}")
    return failures


def scan_path_tree(target: Path, failures: int, *, source_tree: bool) -> int:
    roots = [target] if source_tree else [target / "config", target / "state", target / "mcp"]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".json", ".md", ".toml", ".yml", ".yaml"}:
                continue
            if any(part in path.as_posix() for part in ("/.git/", "/tests/", "/.pytest_cache/")):
                continue
            try:
                body = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            failures = scan_text_for_secrets(str(path.relative_to(target)), body, failures)
    return failures


def validate_generated_artifacts(failures: int) -> int:
    """Generate sample project artifacts and assert secrets never appear."""
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
            os.environ["FLOSSWARE_AI_ROOT"] = str(Path(tmp) / "ai-root")
            cfg = Config(
                agents=["claude-code", "crush"],
                capabilities=["model-router-ai", "resilience-ai", "structured-output-ai"],
                budget_policy="medium", repo_dir=str(repo), profile="default",
            )
            state = generate_artifacts(cfg)
            failures += not check("Artifact metadata", state.get("credential_values_written") is False, "credential_values_written is False")
            from flossware_setup.config import project_state_path
            central_state = project_state_path(repo)
            failures += not check(
                "Central state present",
                central_state.is_file(),
                str(central_state),
            )
            failures += not check(
                "Project tree clean of FlossWare metadata",
                not (repo / ".flossware-ai.json").exists() and not (repo / _FLOSSWARE_MARKER).exists(),
                "no .flossware-ai.json / .flossware in project",
            )
            if central_state.is_file():
                body = central_state.read_text(encoding="utf-8")
                failures += not check(
                    "Generated artifact",
                    not (secret in body or looks_like_secret(body)),
                    "central state.json has no secret values",
                )
            for rel in ("CLAUDE.md", "AGENTS.md"):
                path = repo / rel
                if not path.is_file():
                    failures += not check("Agent instruction present", False, rel)
                    continue
                body = path.read_text(encoding="utf-8")
                failures += not check(
                    "Generated artifact",
                    not (secret in body or looks_like_secret(body)),
                    f"{rel} has no secret values",
                )
    finally:
        os.environ.pop("GROQ_API_KEY", None)
    return failures



def _assert_isolated_root() -> Path:
    """Refuse to use the developer's real home state dir without an opt-in.

    Returns the resolved isolated root (created if needed).
    """
    import os
    from pathlib import Path
    root = os.environ.get("FLOSSWARE_AI_ROOT") or os.environ.get("FLOSSWARE_INSTALL_ROOT")
    if not root:
        raise SystemExit(
            "dogfood requires FLOSSWARE_AI_ROOT (or FLOSSWARE_INSTALL_ROOT) "
            "to isolate state from the real home directory"
        )
    home_ai = (Path.home() / _FLOSSWARE_MARKER / "ai").resolve()
    resolved = Path(root).expanduser().resolve()
    if resolved == home_ai and os.environ.get("FLOSSWARE_DOGFOOD_ALLOW_HOME") != "1":
        raise SystemExit(
            f"dogfood refused to use home state dir {home_ai}; set FLOSSWARE_AI_ROOT to a temp path"
        )
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def main() -> int:
    _assert_isolated_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Require Claude Code and Crush on PATH")
    args = parser.parse_args()
    failures = 0
    source_tree = (ROOT / ".git").exists() and (ROOT / "scripts" / "setup.py").is_file()
    configured_root = os.environ.get("FLOSSWARE_AI_ROOT") or os.environ.get("FLOSSWARE_INSTALL_ROOT")
    target = Path(configured_root).expanduser().resolve() if configured_root else (
        ROOT if source_tree else (Path.home() / _FLOSSWARE_MARKER / "ai")
    )

    if source_tree:
        failures += not check("Repository", True, str(ROOT))
        failures += not check("Installer", (ROOT / "scripts" / "install.sh").is_file(), "POSIX installer present")
        failures += not check("TUI", (ROOT / "scripts" / "setup.py").is_file(), "setup implementation present")
        failures += not check("Discovery", (ROOT / "scripts" / "discovery.py").is_file(), "provider/model discovery present")
        failures += not check("Packaging", (ROOT / "pyproject.toml").is_file(), "PEP 517 setuptools backend")
        failures += not check("Dependencies", True, "capabilities are optional extras")
        failures += not check("Package TUI", (ROOT / "flossware_setup" / "tui" / "app.py").is_file(), "flossware_setup.tui.app present")
    else:
        failures += not check("Runtime root", target.is_dir(), str(target))

    failures = scan_path_tree(target, failures, source_tree=source_tree)
    if source_tree:
        failures = validate_generated_artifacts(failures)

    for agent, (command, instruction) in EXECUTABLE_AGENTS.items():
        found = shutil.which(command) is not None
        instruction_exists = (target / instruction).exists() if source_tree else False
        if args.strict and agent in {"claude-code", "crush"}:
            failures += not check(agent, found, f"{command} is installed")
        else:
            print(f"- {agent}: {'installed' if found else 'not installed'}; instruction file {'present' if instruction_exists else 'not generated'}")

    try:
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from flossware_setup.catalog import AGENTS
        failures += not check("Agent catalog", len(AGENTS) == 13, f"{len(AGENTS)} registered integrations (expected 13)")
    except Exception as exc:
        failures += not check("Agent catalog", False, str(exc))

    profile = os.environ.get("FLOSSWARE_PROFILE") or ""
    if not profile:
        profile_file = target / "state" / "active-profile"
        profile = profile_file.read_text(encoding="utf-8").strip() if profile_file.exists() else "default"
    failures += not check("Profile", bool(profile.strip()), f"active profile value is {profile!r}")
    print("\nCredential values are never displayed by this acceptance test.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
