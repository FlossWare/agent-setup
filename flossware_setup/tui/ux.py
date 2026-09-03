"""Small UX fixes layered over the curses IDE."""
from __future__ import annotations
import curses

def install_tui_fixes() -> None:
    """Install profile editing, validation, and repaint-safe popup fixes."""
    from flossware_setup.config_control import load_active_profile, save_active_profile
    from flossware_setup.tui import ide
    from flossware_setup.tui.input import is_mouse, mouse_event, resolve_list_mouse
    from flossware_setup.tui.profile_editor import edit_profile_tui
    from flossware_setup.tui.validation import validate_popup
    config_items = list(ide.ITEMS.get("Config", ()))
    if "Create Profile" not in config_items:
        try: insert_at = config_items.index("Profiles") + 1
        except ValueError: insert_at = 0
        config_items.insert(insert_at, "Create Profile"); ide.ITEMS["Config"] = tuple(config_items)
    ide._validate_popup = validate_popup
    if getattr(ide, "_ux_fixes_installed", False): return
    original_popup = ide._popup; original_close = ide._close; parents: dict[int, object] = {}
    def popup(win, top, left, height, width, title):
        panel = original_popup(win, top, left, height, width, title); parents[id(panel)] = win
        try:
            panel.bkgd(" ", curses.color_pair(5)); panel.erase(); panel.noutrefresh(); curses.doupdate(); panel.border(); panel.addstr(0, 2, f" {title} ", curses.A_BOLD)
        except curses.error: pass
        return panel
    def close(panel):
        parent = parents.pop(id(panel), None); original_close(panel)
        if parent is not None:
            try: parent.touchwin(); parent.noutrefresh(); curses.doupdate()
            except curses.error: pass
    def profile_selector(win):
        names = ide.available_profiles()
        if not names: return None
        current = load_active_profile(); idx = names.index(current) if current in names else 0
        h, w = win.getmaxyx(); height = min(len(names) + 5, max(8, h - 4)); width = min(max(44, max(map(len, names)) + 18), w - 4); top, left = max(2, (h-height)//2), max(2, (w-width)//2); panel = popup(win, top, left, height, width, "Profiles")
        while True:
            for i, name in enumerate(names[:height-5]): ide.add(panel, 2+i, 2, ("> " if i == idx else "  ") + name.replace("-", " ").title(), ide.palette("selected" if i == idx else "normal"))
            panel.addnstr(height-2, 2, "Enter select | E edit | Esc close", width-4, ide.palette("muted")); panel.refresh(); key = panel.getch()
            if is_mouse(key):
                # Screen-absolute coordinates from getmouse(); list starts at top+2.
                visible = min(len(names), height - 5)
                action = resolve_list_mouse(
                    mouse_event(),
                    origin_y=top + 2,
                    count=len(names),
                    scroll_offset=0,
                    visible=visible,
                )
                if action is not None:
                    kind, index = action
                    idx = index
                    if kind == "activate":
                        save_active_profile(names[idx])
                        close(panel)
                        return names[idx]
                continue
            elif key in (curses.KEY_UP, ord("k")): idx = (idx-1) % len(names)
            elif key in (curses.KEY_DOWN, ord("j")): idx = (idx+1) % len(names)
            elif key in (10, 13, curses.KEY_ENTER):
                save_active_profile(names[idx]); close(panel); return names[idx]
            elif key in (ord("e"), ord("E")): close(panel); edit_profile_tui(win, names[idx], popup, close, ide.add, ide.palette); return None
            elif key == 27: close(panel); return None
    ide._popup = popup; ide._close = close; ide.profile_selector = profile_selector; ide._ux_fixes_installed = True
