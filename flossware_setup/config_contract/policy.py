"""Policy constraints applied after configuration resolution."""
from typing import Any
class PolicyError(ValueError): pass
class Policy:
    def __init__(self, *, allowed: dict[str, list[Any]] | None = None) -> None: self.allowed=allowed or {}
    def validate(self, config: dict[str, Any]) -> None:
        for key, permitted in self.allowed.items():
            if key in config and config[key] not in permitted: raise PolicyError(f"{key}: {config[key]!r} is not permitted")
