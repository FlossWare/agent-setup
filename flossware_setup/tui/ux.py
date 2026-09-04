"""Small UX fixes layered over the curses IDE."""
from __future__ import annotations

import curses

from curses_tui import Menu, MenuItem, Rect, Window, WindowManager


def install_tui_fixes() -> None:
    """Install profile editing, validation, and reusable TUI primitives."""
    from flossware_setup.config_control import load_active_profile, save_active_profile
    from flossware_setup.tui import ide
    from flossware_setup.tui.input import is_mouse, mouse_event, resolve_list_mouse
    from flossware_setup.tui.profile_editor import edit_profile_tui
    from flossware_setup.tui.validation import validate_popup

    config_items = list(ide.ITEMS.get("Config", ()))
    if "Create Profile" not in config_items:
        try:
            insert_at = config_items.index("Profiles") + 1
        except ValueError:
            insert_at = 0
        config_items.insert(insert_at, "Create Profile")
        ide.ITEMS["Config"] = tuple(config_items)

    ide._validate_popup = validate_popup
    if getattr(ide, "_ux_fixes_installed", False):
        return

    original_popup = ide._popup
    original_close = ide._close
    parents: dict[int, object] = {}
    managed: dict[int, tuple[WindowManager, Window]] = {}

    def popup(win, top, left, height, width, title):
        panel = original_popup(win, top, left, height, width, title)
        parents[id(panel)] = win
        screen_h, screen_w = win.getmaxyx()
        manager = WindowManager(screen_w, screen_h)
        model = manager.add(Window(title, Rect(left, top, width, height)))
        managed[id(panel)] = (manager, model)
        try:
            panel.bkgd(" ", curses.color_pair(5))
            panel.erase()
            panel.noutrefresh()
            curses.doupdate()
            panel.border()
            panel.addstr(0, 2, f" {title} ", curses.A_BOLD)
        except curses.error:
            pass
        return panel

    def sync_popup(panel) -> None:
        state = managed.get(id(panel))
        if state is None:
            return
        _manager, model = state
        try:
            panel.mvwin(model.rect.y, model.rect.x)
            panel.resize(model.rect.height, model.rect.width)
        except (AttributeError, curses.error):
            pass

    def close(panel):
        managed.pop(id(panel), None)
        parent = parents.pop(id(panel), None)
        original_close(panel)
        if parent is not None:
            try:
                parent.touchwin()
                parent.noutrefresh()
                curses.doupdate()
            except curses.error:
                pass

    def profile_selector(win):
        names = list(ide.available_profiles())
        if not names:
            return None
        current = load_active_profile()
        idx = names.index(current) if current in names else 0
        h, w = win.getmaxyx()
        height = min(len(names) + 5, max(8, h - 4))
        width = min(max(44, max(map(len, names)) + 18), w - 4)
        top, left = max(2, (h - height) // 2), max(2, (w - width) // 2)
        panel = popup(win, top, left, height, width, "Profiles")
        manager, model = managed[id(panel)]
        menu = Menu(
            [
                MenuItem(
                    name,
                    action=lambda name=name: name,
                    accelerator=str(i + 1) if i < 9 else None,
                )
                for i, name in enumerate(names)
            ],
            selected=idx,
        )
        while True:
            top, left = model.rect.y, model.rect.x
            height, width = model.rect.height, model.rect.width
            visible = min(len(names), max(0, height - 5))
            idx = min(menu.selected, len(names) - 1)
            panel.erase()
            try:
                panel.border()
                panel.addstr(0, 2, " Profiles ", curses.A_BOLD)
            except curses.error:
                pass
            for i, label in enumerate(menu.rendered_labels()[:visible]):
                ide.add(
                    panel,
                    2 + i,
                    2,
                    ("> " if i == idx else "  ") + label,
                    ide.palette("selected" if i == idx else "normal"),
                )
            try:
                panel.addnstr(
                    height - 2,
                    2,
                    "Enter select | 1-9 accelerator | E edit | Esc close",
                    max(0, width - 4),
                    ide.palette("muted"),
                )
            except curses.error:
                pass
            panel.refresh()
            key = panel.getch()
            if is_mouse(key):
                event = mouse_event()
                if event is not None:
                    manager.handle_mouse(event)
                    sync_popup(panel)
                    top, left = model.rect.y, model.rect.x
                    height, width = model.rect.height, model.rect.width
                    visible = min(len(names), max(0, height - 5))
                    action = resolve_list_mouse(
                        event,
                        origin_y=top + 2,
                        count=len(names),
                        scroll_offset=0,
                        visible=visible,
                    )
                    if action is not None:
                        kind, index = action
                        menu.selected = index
                        if kind == "activate":
                            save_active_profile(names[index])
                            close(panel)
                            return names[index]
                continue
            if key in (ord("e"), ord("E")):
                close(panel)
                edit_profile_tui(
                    win, names[menu.selected], popup, close, ide.add, ide.palette
                )
                return None
            result = menu.handle_key(key)
            if result is not None:
                save_active_profile(str(result))
                close(panel)
                return str(result)
            if key == 27:
                close(panel)
                return None

    ide._popup = popup
    ide._close = close
    ide.profile_selector = profile_selector
    ide._ux_fixes_installed = True
