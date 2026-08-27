"""Policy-aware coding-agent launcher for the TUI."""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass

from flossware_setup.catalog import AGENTS
from flossware_setup.config_control import effective_config


@dataclass(frozen=True)
class AgentOption:
    id: str
    name: str
    command: str


def _command_for(agent) -> str | None:
    for attr in ("command", "executable", "binary"):
        value = getattr(agent, attr, None)
        if isinstance(value, str) and value:
            return value.split()[0]
    commands = getattr(agent, "commands", None)
    if isinstance(commands, (list, tuple)):
        for value in commands:
            if isinstance(value, str) and value:
                return value.split()[0]
    return None


def available_agents() -> list[AgentOption]:
    result = []
    for agent_id, agent in AGENTS.items():
        command = _command_for(agent)
        if command and shutil.which(command):
            result.append(AgentOption(agent_id, getattr(agent, "name", agent_id), command))
    return result


def launch_agent(agent: AgentOption, cwd: str | None = None) -> int:
    directory = cwd or os.getcwd()
    config = effective_config(directory)
    if not config:
        raise RuntimeError("unable to resolve effective configuration")
    env = os.environ.copy()
    env["FLOSSWARE_PROFILE"] = str(getattr(config, "profile", ""))
    env["FLOSSWARE_AGENT"] = agent.id
    return subprocess.call([agent.command], cwd=directory, env=env)
