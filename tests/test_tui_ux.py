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


def test_shared_interaction_primitives_are_used():
    from curses_tui import Menu, MenuItem, Rect, Window, WindowManager
    from flossware_setup.tui import ux

    assert ux.Menu is Menu
    assert ux.MenuItem is MenuItem
    assert ux.Rect is Rect
    assert ux.Window is Window
    assert ux.WindowManager is WindowManager

    menu = Menu([MenuItem("Free", action=lambda: "free", accelerator="1")])
    assert menu.rendered_labels() == ["Free  [1]"]
    assert menu.handle_key(ord("1")) == "free"

    manager = WindowManager(80, 24)
    window = manager.add(Window("Profiles", Rect(10, 5, 30, 10)))
    assert manager.active is window
    assert manager.hit_test(10, 5) is window
