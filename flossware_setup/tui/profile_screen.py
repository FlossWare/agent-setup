"""Interactive profile selector for the Setup Control Center."""

from __future__ import annotations

from flossware_setup.tui.widgets import header, menu, add

PROFILES = [
    ("default", "Neutral public profile | configured providers + local models"),
    ("redhat-cost-conscious", "Red Hat work template | Anthropic only | hard $300/month ceiling"),
]


def select_profile(win, current: str = "default") -> str | None:
    """Show the profile drop-down/menu and return the selected profile id."""
    selected = next((i for i, (profile_id, _desc) in enumerate(PROFILES) if profile_id == current), 0)
    choice = menu(win, "Select Profile", PROFILES, selected=[selected], multi=False)
    if choice is None:
        return None
    return PROFILES[int(choice)][0]


def profile_status_line(win, profile: str) -> None:
    """Render the active profile prominently above the main menu."""
    h, _ = win.getmaxyx()
    add(win, h - 3, 2, f"PROFILE: {profile}", 1)
