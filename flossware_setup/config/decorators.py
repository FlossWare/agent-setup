"""Optional Python registration decorators for the common config contract."""

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def configurable(*, id: str, schema: Any = None, menu: str = "main") -> Callable[[T], T]:
    def decorate(obj: T) -> T:
        setattr(obj, "__flossware_config__", {"id": id, "schema": schema, "menu": menu})
        return obj
    return decorate


def menu_item(*, id: str, label: str, before: list[str] | None = None, after: list[str] | None = None) -> Callable[[T], T]:
    def decorate(obj: T) -> T:
        setattr(obj, "__flossware_menu__", {
            "id": id,
            "label": label,
            "before": before or [],
            "after": after or [],
        })
        return obj
    return decorate
