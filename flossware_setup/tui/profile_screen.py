"""Interactive profile selector for the Setup Control Center."""

from __future__ import annotations

from flossware_setup.config_control import available_profiles
from flossware_setup.tui.widgets import add, menu

# Public baseline is neutral ``default``. Organization templates are examples only
# and appear when the user has installed them under the local profiles directory.
_PROFILE_LABELS = {
    "default": "Neutral public profile | configured providers + local models",
}


def _profile_choices() -> list[tuple[str, str]]:
    choices: list[tuple[str, str]] = []
    for name in available_profiles():
        label = _PROFILE_LABELS.get(name, f"Local profile | {name}")
        choices.append((name, label))
    if not choices:
        choices.append(("default", _PROFILE_LABELS["default"]))
    return choices


def select_profile(win, current: str = "default") -> str | None:
    """Show the profile drop-down/menu and return the selected profile id."""
    profiles = _profile_choices()
    selected = next((i for i, (profile_id, _desc) in enumerate(profiles) if profile_id == current), 0)
    choice = menu(win, "Select Profile", profiles, selected=[selected], multi=False)
    if choice is None:
        return None
    return profiles[int(choice)][0]


def profile_status_line(win, profile: str) -> None:
    """Render the active profile prominently above the main menu."""
    h, _ = win.getmaxyx()
    add(win, h - 3, 2, f"PROFILE: {profile}", 1)
