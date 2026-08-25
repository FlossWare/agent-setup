"""Configuration state and persistence."""
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path

@dataclass
class Config:
    agents: list[int] = field(default_factory=list)
    capabilities: list[int] = field(default_factory=list)
    budget_index: int = 2
    budget_amount: float = 50.0
    repo_dir: str = "."
    theme: str = "dark"
    profile: str = "default"


def state_path(repo: str | Path) -> Path:
    return Path(repo).resolve() / ".flossware-ai.json"


def load_state(repo: str | Path):
    path = state_path(repo)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_state(repo: str | Path, state: dict) -> None:
    state_path(repo).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
