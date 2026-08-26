"""Installation package refs and project artifact generation.

Generated files never contain credential values. Existing user instruction
files are left untouched.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from flossware_setup.catalog import (
    AGENT_BY_ID,
    CAPABILITY_REFS,
    FLOSSWARE_BASE,
    PROVIDERS,
    AgentAdapter,
)
from flossware_setup.config import (
    Config,
    build_state_dict,
    central_project_dir,
    is_git_repository,
    project_state_path,
    resolve_budget,
    set_active_project,
)
from flossware_setup.credentials import (
    assert_no_secret_material,
    credential_status,
    environment_names,
    scan_mapping_for_secrets,
)

_AIDER_CONF = ".aider.conf.yml"
_AIDER_READ_LINE = "read: CONVENTIONS.md"
_AIDER_READ_KEY = re.compile(r"^read\s*:", re.MULTILINE)


def pip_packages(capability_ids: list[str]) -> list[str]:
    """Build pinned git+https install specs for selected capability IDs."""
    packages: list[str] = []
    for name in capability_ids:
        if name not in CAPABILITY_REFS:
            continue
        ref = CAPABILITY_REFS[name]
        packages.append(f"git+{FLOSSWARE_BASE}/{name}.git@{ref}")
    return packages


def _write_if_missing(path: Path, content: str) -> None:
    """Create an instruction file without overwriting user configuration."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_aider_conf(repo: Path) -> None:
    """Ensure Aider loads CONVENTIONS.md without clobbering user config."""
    path = repo / _AIDER_CONF
    if not path.exists():
        path.write_text(
            f"# FlossWare AI conventions\n{_AIDER_READ_LINE}\n",
            encoding="utf-8",
        )
        return
    try:
        body = path.read_text(encoding="utf-8")
    except OSError:
        return
    if _AIDER_READ_KEY.search(body):
        return
    suffix = "" if body.endswith("\n") or not body else "\n"
    path.write_text(
        f"{body}{suffix}# FlossWare AI conventions\n{_AIDER_READ_LINE}\n",
        encoding="utf-8",
    )


def _agent_content(base: list[str], adapter: AgentAdapter) -> str:
    content = list(base)
    if adapter.id == "aider":
        content[0] = "# FlossWare AI Integration"
        content.extend(["", "Aider: load this file as a read-only conventions file.", ""])
    if adapter.id == "kiro":
        content.insert(0, "---\ninclusion: always\n---")
    if adapter.id == "windsurf":
        content.insert(0, "---\ntrigger: always_on\n---")
    return "\n".join(content) + "\n"


def generate_artifacts(config: Config, *, write_agent_files: bool = True) -> dict:
    """Write optional agent instruction files and central FlossWare state.

    Project directories are never used for FlossWare metadata (``.flossware-ai.json``
    and ``ai_config.py`` live under the managed state root). Git is optional.
    """
    repo = Path(config.repo_dir).expanduser().resolve()
    if not repo.is_dir():
        raise ValueError(f"Not a directory: {repo}")

    policy_label, budget = resolve_budget(config)
    provider_status = credential_status()
    env_vars = environment_names()

    install_lines = "\n".join(
        f"python -m pip install {pkg}" for pkg in pip_packages(config.capabilities)
    )
    providers_md = "\n".join(
        f"- {name}: `${env}` ({'configured' if provider_status[name] else 'not set'})"
        for name, env, _ in PROVIDERS
    )
    base = [
        "## FlossWare AI Integration",
        "",
        (
            "This project uses provider-neutral FlossWare AI libraries. Provider selection "
            "and spending are explicit policy decisions, not hard-coded vendor defaults."
        ),
        "",
        "### Capabilities",
        *[f"- {name}" for name in config.capabilities],
        "",
        f"### Budget policy: {policy_label}",
        f"Monthly ceiling: ${budget:g}",
        "",
        "### Providers",
        providers_md,
        "",
        (
            "Credential values are never stored in generated files. Configure them through a "
            "secure environment, OS secret store, CI secret store, or provider/router secret mechanism."
        ),
        "",
        "### Install",
        "```bash",
        install_lines,
        "```",
        "",
    ]

    assert_no_secret_material("\n".join(base), label="artifact body")

    if write_agent_files:
        for agent_id in config.agents:
            adapter = AGENT_BY_ID.get(agent_id)
            if adapter is None:
                continue
            content = _agent_content(base, adapter)
            for relative_path in adapter.files:
                _write_if_missing(repo / relative_path, content)
            if adapter.id == "aider":
                ensure_aider_conf(repo)

    state = build_state_dict(config)
    state_findings = scan_mapping_for_secrets(state)
    if state_findings:
        raise ValueError(
            "refusing to write project state with secret-like material: "
            + "; ".join(state_findings)
        )
    state_json = json.dumps(state, indent=2) + "\n"
    assert_no_secret_material(state_json, label="central project state")

    central = central_project_dir(repo)
    (central / "state.json").write_text(state_json, encoding="utf-8")
    active_providers = (
        "ACTIVE_PROVIDERS = {k: bool(__import__('os').environ.get(v)) "
        "for k, v in PROVIDER_ENV_VARS.items()}\n"
    )
    (central / "ai_config.py").write_text(
        (
            "# Auto-generated by FlossWare/coding-agent-setup. No credential values are stored.\n"
            f"MONTHLY_BUDGET = {budget!r}\n"
            f"BUDGET_POLICY = {policy_label!r}\n"
            f"PROVIDER_ENV_VARS = {env_vars!r}\n"
            f"{active_providers}"
        ),
        encoding="utf-8",
    )
    # Record path identity for rename diagnostics (metadata only).
    (central / "path.txt").write_text(str(repo) + "\n", encoding="utf-8")
    set_active_project(repo)
    return state
