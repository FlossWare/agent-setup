"""Deterministic layered configuration resolver."""
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ConfigLayer:
    id: str
    priority: int
    values: dict[str, Any]

class ConfigResolver:
    def __init__(self) -> None: self._layers: list[ConfigLayer] = []
    def add_layer(self, layer: ConfigLayer) -> None: self._layers.append(layer)
    def resolve(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for layer in sorted(self._layers, key=lambda x: (x.priority, x.id)): result.update(layer.values)
        return result
    def provenance(self, key: str) -> list[tuple[str, Any]]:
        return [(l.id, l.values[key]) for l in sorted(self._layers, key=lambda x: (x.priority, x.id)) if key in l.values]
    def explain(self, key: str) -> str:
        h = self.provenance(key)
        if not h: return f"{key}: not configured"
        return "\n".join([key, "", *[f"  {layer}: {value!r}" for layer, value in h], f"  effective: {h[-1][1]!r}"])
