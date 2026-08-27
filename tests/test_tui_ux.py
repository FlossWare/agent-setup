"""Tests for user-visible TUI configuration affordances."""

from __future__ import annotations


def test_profile_creation_is_exposed_and_patch_is_idempotent():
    from flossware_setup.tui import ide
    from flossware_setup.tui.ux import install_tui_fixes

    install_tui_fixes()
    install_tui_fixes()

    assert "Profiles" in ide.ITEMS["Config"]
    assert "Create Profile" in ide.ITEMS["Config"]
    assert ide.ITEMS["Config"].count("Create Profile") == 1
    assert getattr(ide, "_ux_fixes_installed", False)
