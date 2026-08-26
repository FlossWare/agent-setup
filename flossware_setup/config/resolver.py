"""Deterministic layered configuration resolver."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConfigLayer:
    id: str
    priority: int
    values: dict[str, Any]


class ConfigResolver:
    """Merge layers from lowest to highest priority and retain provenance."""

    def __init__(self) -> None:
        self._layers: list[ConfigLayer] = []

    def add_layer(self, layer: ConfigLayer) -> None:
        self._layers.append(layer)

    def resolve(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for layer in sorted(self._layers, key=lambda item: (item.priority, item.id)):
            result.update(layer.values)
        return result

    def provenance(self, key: str) -> list[tuple[str, Any]]:
        return [
            (layer.id, layer.values[key])
            for layer in sorted(self._layers, key=lambda item: (item.priority, item.id))
            if key in layer.values
        ]

    def explain(self, key: str) -> str:
        history = self.provenance(key)
        if not history:
            return f"{key}: not configured"
        lines = [f"{key}", ""]
        for layer, value in history:
            lines.append(f"  {layer}: {value!r}")
        lines.append(f"  effective: {history[-1][1]!r}")
        return "\n".join(lines)
