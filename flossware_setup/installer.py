"""Artifact generation and optional capability installation."""
import subprocess, sys
from pathlib import Path
from .catalog import AGENTS, CAPABILITIES, CAPABILITY_REFS, FLOSSWARE_BASE, PROVIDERS, BUDGET_POLICIES
from .credentials import status as credential_status, environment_names

def pip_packages(indices):
    return [f"git+{FLOSSWARE_BASE}/{CAPABILITIES[i][0]}.git@{CAPABILITY_REFS[CAPABILITIES[i][0]]}" for i in indices]

def install_packages(indices):
    for package in pip_packages(indices):
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", package], capture_output=True, text=True, timeout=180)
        if result.returncode:
            raise RuntimeError(f"Required library failed to install: {package}\n{result.stderr[-1200:]}")

def _write_if_missing(path: Path, content: str):
    if path.exists(): return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def _agent_content(base, agent):
    content = list(base)
    if agent.id == "aider": content += ["", "Aider: load this file as a read-only conventions file."]
    if agent.id == "kiro": content.insert(0, "---\ninclusion: always\n---")
    return "\n".join(content) + "\n"

def generate_artifacts(config):
    repo = Path(config.repo_dir).resolve()
    if not (repo / ".git").exists(): raise ValueError(f"Not a git repository: {repo}")
    policy = BUDGET_POLICIES[config.budget_index]
    budget = config.budget_amount if policy[1] < 0 else policy[1]
    providers = credential_status(); env_vars = environment_names()
    names = [CAPABILITIES[i][0] for i in config.capabilities]
    base = ["## FlossWare AI Integration", "", "This project uses provider-neutral FlossWare AI libraries.", "", "### AI Stack", *[f"- **{CAPABILITIES[i][0]}**: {CAPABILITIES[i][1]}" for i in config.capabilities], "", f"### Budget policy: {policy[0]}", f"Monthly ceiling: ${budget:g}", "", "### Providers", *[f"- {n}: `${env_vars[n]}` ({'configured' if providers[n] else 'not set'})" for n,_,_ in PROVIDERS], "", "Credential values are never stored in generated files.", ""]
    for index in config.agents:
        agent = AGENTS[index]
        for relative in agent.files: _write_if_missing(repo / relative, _agent_content(base, agent))
        if agent.id == "aider": _write_if_missing(repo / ".aider.conf.yml", "# FlossWare AI conventions\nread: CONVENTIONS.md\n")
    (repo / "ai_config.py").write_text(f"# Auto-generated. No credential values are stored.\nMONTHLY_BUDGET = {budget!r}\nBUDGET_POLICY = {policy[0]!r}\nPROVIDER_ENV_VARS = {env_vars!r}\n", encoding="utf-8")
    state = {"tool":"FlossWare/coding-agent-setup", "profile":config.profile, "budget_policy":policy[0], "monthly_budget":budget, "capabilities":names, "providers":providers, "provider_env_vars":env_vars, "credential_values_written":False, "agents":[AGENTS[i].id for i in config.agents], "theme":config.theme}
    (repo / ".flossware-ai.json").write_text(__import__("json").dumps(state, indent=2) + "\n", encoding="utf-8")
