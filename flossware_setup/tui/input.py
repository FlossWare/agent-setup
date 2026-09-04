"""Compatibility imports for the shared curses-themes input primitives."""

from curses_themes import (
    enable_mouse,
    is_cancel,
    is_confirm,
    is_down,
    is_mouse,
    is_primary_click,
    is_up,
    list_index_at,
    mouse_event,
    mouse_position,
    primary_button_mask,
    primary_click,
    resolve_list_mouse,
)

__all__ = [
    "enable_mouse",
    "is_cancel",
    "is_confirm",
    "is_down",
    "is_mouse",
    "is_primary_click",
    "is_up",
    "list_index_at",
    "mouse_event",
    "mouse_position",
    "primary_button_mask",
    "primary_click",
    "resolve_list_mouse",
]
