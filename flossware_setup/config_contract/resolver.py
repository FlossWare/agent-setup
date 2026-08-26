"""Deterministic layered configuration resolver."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from flossware_setup.config_contract.policy import Policy


@dataclass(frozen=True)
class ConfigLayer:
    id: str
    priority: int
    values: dict[str, Any]


class ConfigResolver:
    def __init__(self) -> None:
        self._layers: list[ConfigLayer] = []

    def add_layer(self, layer: ConfigLayer) -> None:
        self._layers.append(layer)

    def resolve(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for layer in sorted(self._layers, key=lambda x: (x.priority, x.id)):
            result.update(layer.values)
        return result

    def resolve_with_policy(self, policy: Policy) -> dict[str, Any]:
        """Merge layers, then enforce *policy* so lower layers cannot escape it."""
        result = self.resolve()
        policy.validate(result)
        return result

    def provenance(self, key: str) -> list[tuple[str, Any]]:
        return [
            (layer.id, layer.values[key])
            for layer in sorted(self._layers, key=lambda x: (x.priority, x.id))
            if key in layer.values
        ]

    def explain(self, key: str) -> str:
        history = self.provenance(key)
        if not history:
            return f"{key}: not configured"
        lines = [key, ""]
        lines.extend(f"  {layer}: {value!r}" for layer, value in history)
        lines.append(f"  effective: {history[-1][1]!r}")
        return "\n".join(lines)
