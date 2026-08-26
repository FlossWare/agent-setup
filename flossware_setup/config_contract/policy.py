"""Policy constraints applied after configuration resolution."""

from __future__ import annotations

from typing import Any, Iterable


class PolicyError(ValueError):
    """Raised when resolved configuration violates a policy constraint."""


class Policy:
    """Post-resolution constraints that lower layers cannot escape via override.

    Policy is always evaluated *after* :meth:`ConfigResolver.resolve`. A project
    or user layer may set a higher ``budget.monthly`` during merge, but
    :meth:`validate` still rejects the effective value when it exceeds a
    profile/system maximum or leaves the allowed set.
    """

    def __init__(
        self,
        *,
        allowed: dict[str, list[Any]] | None = None,
        max_values: dict[str, float | int] | None = None,
        required_false: Iterable[str] | None = None,
        required_true: Iterable[str] | None = None,
    ) -> None:
        self.allowed = allowed or {}
        self.max_values = max_values or {}
        self.required_false = tuple(required_false or ())
        self.required_true = tuple(required_true or ())

    def validate(self, config: dict[str, Any]) -> None:
        for key, permitted in self.allowed.items():
            if key in config and config[key] not in permitted:
                raise PolicyError(f"{key}: {config[key]!r} is not permitted")
        for key, ceiling in self.max_values.items():
            if key in config:
                try:
                    value = float(config[key])
                except (TypeError, ValueError) as exc:
                    raise PolicyError(f"{key}: non-numeric value {config[key]!r}") from exc
                if value > float(ceiling):
                    raise PolicyError(
                        f"{key}: {value} exceeds policy maximum {ceiling}"
                    )
        for key in self.required_false:
            if config.get(key):
                raise PolicyError(f"{key}: must be false under this policy")
        for key in self.required_true:
            if not config.get(key):
                raise PolicyError(f"{key}: must be true under this policy")
