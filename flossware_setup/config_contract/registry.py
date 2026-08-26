"""Runtime registry for configurable components."""
from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True)
class Component:
    id: str; label: str; schema: Any=None; menu: str="main"
class ComponentRegistry:
    def __init__(self) -> None: self._items={}
    def register(self, component: Component) -> Component:
        if component.id in self._items: raise ValueError(f"component already registered: {component.id}")
        self._items[component.id]=component; return component
    def get(self, component_id: str) -> Component: return self._items[component_id]
    def all(self) -> list[Component]: return list(self._items.values())
