"""Context-sensitive status text for TUI selections."""

from __future__ import annotations


def item_status(name: str, description: str = "") -> str:
    """Return concise, non-secret status text for a menu item.

    This deliberately uses catalog labels/descriptions only. It never inspects
    or renders credential values.
    """
    label = name.strip()
    detail = description.strip()
    if not label:
        return "STATUS: ready"
    if label.lower() == "exit":
        return "STATUS: Exit | leave Setup Control Center"
    if label.lower().startswith("review"):
        return "STATUS: Review | inspect persisted project configuration | secret-free"
    if label.lower().startswith("configure"):
        return "STATUS: Configure | agents + capabilities + budget + project"
    if label.lower().startswith("provider credentials"):
        return "STATUS: Credentials | source presence only | secret values hidden"
    if detail:
        return f"STATUS: {label} | {detail}"
    return f"STATUS: {label} | available"
