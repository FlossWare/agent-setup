"""Small language-neutral configuration schema model."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConfigField:
    key: str
    type: str
    default: Any = None
    minimum: float | None = None
    maximum: float | None = None
    values: tuple[Any, ...] = ()
    description: str = ""

    def validate(self, value: Any) -> None:
        if self.type == "integer" and not isinstance(value, int):
            raise ValueError(f"{self.key}: expected integer")
        if self.type == "float" and not isinstance(value, (int, float)):
            raise ValueError(f"{self.key}: expected number")
        if self.type == "boolean" and not isinstance(value, bool):
            raise ValueError(f"{self.key}: expected boolean")
        if self.minimum is not None and value < self.minimum:
            raise ValueError(f"{self.key}: value below minimum {self.minimum}")
        if self.maximum is not None and value > self.maximum:
            raise ValueError(f"{self.key}: value above maximum {self.maximum}")
        if self.values and value not in self.values:
            raise ValueError(f"{self.key}: invalid value {value!r}")


@dataclass
class ConfigSchema:
    fields: dict[str, ConfigField] = field(default_factory=dict)

    def add(self, item: ConfigField) -> "ConfigSchema":
        self.fields[item.key] = item
        return self

    def validate(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            if key in self.fields:
                self.fields[key].validate(value)
