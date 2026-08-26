"""Turbo C++ / dBase IV inspired configuration TUI."""
from __future__ import annotations
import curses
from pathlib import Path
from flossware_setup.config_control import (
    THEMES, available_profiles, bind_directory, binding_provenance,
    bindings_grouped_by_profile, effective_config, load_bindings, load_theme,
    profile_for_directory, profiles_dir, save_theme, state_dir, unbind_directory,
)
from flossware_setup.tui.input import enable_mouse, mouse_event
from flossware_setup.tui.widgets import add, palette

MENUS = ("File", "Edit", "View", "Config", "Models", "Agents", "Optimize", "Help")
ITEMS = {
    "File": ("Save", "Exit"),
    "Edit": ("Reorder menus", "Reset layout"),
    "View": ("Profiles", "Directory Bindings", "Configuration", "Status", "Theme"),
    "Config": ("Profiles", "Create Profile", "Directory Bindings", "Validate", "Explain"),
    "Models": ("Discover models", "Refresh models"),
    "Agents": ("Agent configuration", "Run agent with profile"),
    "Optimize": ("Thompson Sampling", "Genetic Optimizer"),
    "Help": ("Keyboard and mouse", "About"),
}
MNEMONICS = {x[0].lower(): i for i, x in enumerate(MENUS)}


def _profile_file(): return state_dir() / "profile"


def save_profile(name: str):
    if name not in available_profiles(): raise ValueError(f"unknown profile: {name}")
    _profile_file().write_text(name + "\n", encoding="utf-8")


def _active():
    profile, source = profile_for_directory()
    if source: return profile, source
    try: manual = _profile_file().read_text(encoding="utf-8").strip()
    except OSError: manual = ""
    return (manual if manual in available_profiles() else "personal"), None


def _shadow(win, top, left, height, width):
    h, w = win.getmaxyx()
    for y in range(top + 1, min(h, top + height + 1)):
        try: win.addstr(y, left + 2, " " * max(0, min(width, w - left - 3)), curses.A_DIM)
        except curses.error: pass


def _popup(win, top, left, height, width, title):
    _shadow(win, top, left, height, width)
    p = curses.newwin(height, width, top, left); p.keypad(True); p.bkgd(" ")
    try: p.box(); p.addstr(0, 2, f" {title} ", curses.A_BOLD)
    except curses.error: pass
    return p


def _menu_positions():
    x = 1; result = []
    for name in MENUS:
        result.append((name, x, x + len(name) - 1)); x += len(name) + 2
    return result


def _close(p): p.erase(); p.noutrefresh(); curses.doupdate()


def profile_selector(win):
    profiles = available_profiles()
    if not profiles: return None
    current, _ = _active(); cur = profiles.index(current) if current in profiles else 0
    h, w = win.getmaxyx(); height = min(len(profiles) + 5, max(8, h - 4)); width = min(max(38, max(map(len, profiles)) + 10), w - 4)
    top, left = max(2, (h - height) // 2), max(2, (w - width) // 2); p = _popup(win, top, left, height, width, "Select Profile")
    while True:
        for i, name in enumerate(profiles[:height - 5]):
            add(p, 2 + i, 2, ("> " if i == cur else "  ") + name.replace("-", " ").title(), 1 if i == cur else 5, curses.A_REVERSE if i == cur else 0)
        p.noutrefresh(); curses.doupdate(); key = p.getch()
        if key == curses.KEY_MOUSE:
            event = mouse_event()
            if event and event[2] & getattr(curses, "BUTTON1_CLICKED", 0):
                i = event[1] - top - 2
                if 0 <= i < min(len(profiles), height - 5): save_profile(profiles[i]); _close(p); return profiles[i]
        elif key in (curses.KEY_UP, ord("k")): cur = (cur - 1) % len(profiles)
        elif key in (curses.KEY_DOWN, ord("j")): cur = (cur + 1) % len(profiles)
        elif key in (10, 13, curses.KEY_ENTER): save_profile(profiles[cur]); _close(p); return profiles[cur]
        elif key == 27: _close(p); return None


def create_profile(win):
    h, w = win.getmaxyx(); width = min(66, w - 4); top, left = max(2, (h - 9) // 2), max(2, (w - width) // 2)
    p = _popup(win, top, left, 9, width, "Create Profile")
    p.addstr(2, 2, "Profile name:"); p.addstr(3, 2, "Provider: auto"); p.addstr(4, 2, "Budget: 0 (unlimited)"); p.addstr(5, 2, "Optimizer: hybrid"); p.addstr(7, 2, "Enter Create   Esc Cancel")
    p.move(2, 16); curses.echo(); curses.curs_set(1)
    try: raw = p.getstr(2, 16, width - 19).decode("utf-8", "ignore").strip()
    finally: curses.noecho(); curses.curs_set(0)
    name = raw.lower().replace(" ", "-")
    if not name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in name) or name in set(available_profiles()): _close(p); return None
    profiles_dir().mkdir(parents=True, exist_ok=True)
    (profiles_dir() / f"{name}.toml").write_text(f'''profile = "{name}"\n\n[model_policy]\nallowed_providers = ["*configured*"]\nallow_local_models = true\nallow_unconfigured_providers = false\nallow_personal_accounts = true\nallow_provider_fallback = true\n\n[optimization]\nenabled = true\nstrategy = "hybrid"\n\n[cost]\nmonthly_limit_usd = 0.0\nhard_limit = false\n''', encoding="utf-8")
    _close(p); return name


def bindings_view(win):
    """Show directory bindings grouped by profile plus current-path provenance."""
    h, w = win.getmaxyx()
    height = min(max(12, h - 4), h - 2)
    width = min(110, w - 4)
    p = _popup(win, max(2, (h - height) // 2), max(2, (w - width) // 2), height, width, "Directory Bindings")
    while True:
        p.erase()
        p.border()
        p.addstr(0, 2, " Directory Bindings ")
        prov = binding_provenance(Path.cwd())
        y = 1
        p.addnstr(y, 2, f"CWD: {prov['directory']}", width - 4); y += 1
        src = prov["source"] or "(default/fallback)"
        p.addnstr(y, 2, f"Effective profile: {prov['effective_profile']}  [{prov['source_kind']}]", width - 4); y += 1
        p.addnstr(y, 2, f"Winning binding: {src}", width - 4); y += 1
        parents = prov.get("parent_bindings") or []
        if parents:
            p.addnstr(y, 2, "Less-specific parents: " + "; ".join(f"{d}->{pr}" for d, pr in parents[:3]), width - 4)
            y += 1
        y += 1
        p.addstr(y, 2, "Bindings by profile:"); y += 1
        grouped = bindings_grouped_by_profile()
        if not grouped:
            p.addstr(y, 2, "  (none — press A to bind CWD)"); y += 1
        for profile, dirs in sorted(grouped.items()):
            p.addnstr(y, 2, f"  [{profile}]", width - 4); y += 1
            if y >= height - 3:
                break
            for directory in dirs:
                p.addnstr(y, 4, directory, width - 6); y += 1
                if y >= height - 3:
                    break
            if y >= height - 3:
                break
        p.addstr(height - 2, 2, "A bind CWD  E edit/rebind CWD  R remove CWD  Esc close")
        p.noutrefresh(); curses.doupdate()
        key = p.getch()
        if key in (27, ord("q")):
            break
        if key in (ord("a"), ord("A"), ord("e"), ord("E")):
            profile = profile_selector(win)
            if profile:
                bind_directory(Path.cwd(), profile)
        elif key in (ord("r"), ord("R")):
            unbind_directory(Path.cwd())
    _close(p)



def theme_selector(win):
    h, w = win.getmaxyx(); p = _popup(win, max(2, (h - 10) // 2), max(2, (w - 42) // 2), 10, 42, "Theme")
    cur = THEMES.index(load_theme())
    while True:
        for i, theme in enumerate(THEMES): p.addstr(2 + i, 2, ("> " if i == cur else "  ") + theme, curses.A_REVERSE if i == cur else 0)
        p.noutrefresh(); curses.doupdate(); key = p.getch()
        if key in (curses.KEY_UP, ord("k")): cur = (cur - 1) % len(THEMES)
        elif key in (curses.KEY_DOWN, ord("j")): cur = (cur + 1) % len(THEMES)
        elif key in (10, 13, curses.KEY_ENTER): save_theme(THEMES[cur]); _close(p); return
        elif key == 27: _close(p); return


def _popup_menu(win, index):
    name = MENUS[index]; items = ITEMS[name]; h, w = win.getmaxyx(); x = _menu_positions()[index][1]
    width = min(max(18, max(map(len, items)) + 5), w - x - 2); height = min(len(items) + 2, h - 3); p = _popup(win, 1, x, height, width, name); cur = 0
    while True:
        for i, item in enumerate(items): p.addstr(1 + i, 1, " " + item.ljust(width - 3)[:width - 3], curses.A_REVERSE if i == cur else 0)
        p.noutrefresh(); curses.doupdate(); key = p.getch()
        if key == curses.KEY_LEFT: _close(p); return "__PREV__"
        if key == curses.KEY_RIGHT: _close(p); return "__NEXT__"
        if key == curses.KEY_MOUSE:
            event = mouse_event()
            if event and event[2] & getattr(curses, "BUTTON1_CLICKED", 0):
                mx, my = event[0], event[1]
                for j, (_n, lx, rx) in enumerate(_menu_positions()):
                    if my == 0 and lx <= mx <= rx: _close(p); return ("__MENU__", j)
                if x <= mx < x + width and 2 <= my < 2 + len(items): _close(p); return items[my - 2]
                _close(p); return None
        elif key in (curses.KEY_UP, ord("k")): cur = (cur - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord("j")): cur = (cur + 1) % len(items)
        elif key in (10, 13, curses.KEY_ENTER): _close(p); return items[cur]
        elif key == 27: _close(p); return None


def _open_menu(win, index):
    while True:
        result = _popup_menu(win, index)
        if result == "__NEXT__": index = (index + 1) % len(MENUS); continue
        if result == "__PREV__": index = (index - 1) % len(MENUS); continue
        if isinstance(result, tuple) and result[0] == "__MENU__": index = result[1]; continue
        if result in ("Profiles", "Profile"): return profile_selector(win)
        if result == "Create Profile": return create_profile(win)
        if result == "Directory Bindings": return bindings_view(win)
        if result == "Theme": return theme_selector(win)
        if result == "Exit": return "__EXIT__"
        return None


def _draw(win, active, source, pc):
    h, w = win.getmaxyx(); win.erase(); add(win, 0, 0, " " + "  ".join(MENUS), 1, curses.A_BOLD); add(win, 1, 0, "-" * max(1, w - 1), 1)
    left = max(27, min(34, w // 4)); _box(win, 2, 1, max(3, h - 5), left, "Profiles"); profiles = available_profiles()
    for i, name in enumerate(profiles):
        if 4 + i >= h - 5: break
        attr = curses.A_REVERSE if name == active else 0; add(win, 4 + i, 3, ("> " if name == active else "  ") + name.replace("-", " ").title(), 2 if name == active else 5, attr)
    pl = left + 2; _box(win, 2, pl, max(3, h - 5), max(pl + 2, w - 2), "Configuration"); cfg = effective_config(active).resolve()
    fields = [("Profile", active), ("Provider", cfg.get("provider", "unknown")), ("Budget", f"${float(cfg.get('budget.monthly', 0)):.2f} / month"), ("Optimizer", cfg.get("optimization.strategy", "unknown")), ("Theme", load_theme())]
    for i, (label, value) in enumerate(fields): add(win, 4 + i, pl + 3, f"{label:<22} {value}", 5)
    add(win, h - 4, 2, f"Profile: {active.upper()} | Source: {source or 'default/personal'} | READY", 1, curses.A_BOLD)
    add(win, h - 3, 2, "Alt+letter menus | Arrows | Enter | Mouse", 6); add(win, h - 2, 2, "←/→ switch menus | F-keys optional | Esc/Q Exit", 6); win.refresh(); return profiles


def _box(win, top, left, bottom, right, title):
    try:
        win.addch(top, left, curses.ACS_ULCORNER); win.hline(top, left + 1, curses.ACS_HLINE, max(0, right - left - 1)); win.addch(top, right, curses.ACS_URCORNER)
        win.vline(top + 1, left, curses.ACS_VLINE, max(0, bottom - top - 1)); win.vline(top + 1, right, curses.ACS_VLINE, max(0, bottom - top - 1)); win.addch(bottom, left, curses.ACS_LLCORNER); win.hline(bottom, left + 1, curses.ACS_HLINE, max(0, right - left - 1)); win.addch(bottom, right, curses.ACS_LRCORNER); add(win, top, left + 2, f" {title} ", 1, curses.A_BOLD)
    except curses.error: pass


def run(win):
    palette(); win.keypad(True); enable_mouse(); pc = 0
    while True:
        active, source = _active(); profiles = _draw(win, active, source, pc); pc = profiles.index(active) if active in profiles else min(pc, max(0, len(profiles) - 1)); key = win.getch()
        if key == curses.KEY_MOUSE:
            event = mouse_event()
            if event and event[2] & getattr(curses, "BUTTON1_CLICKED", 0):
                x, y = event[0], event[1]
                if y == 0:
                    for i, (_n, lx, rx) in enumerate(_menu_positions()):
                        if lx <= x <= rx: result = _open_menu(win, i); break
                    else: result = None
                    if result == "__EXIT__": return
                elif 4 <= y < 4 + len(profiles): save_profile(profiles[y - 4])
                elif y >= win.getmaxyx()[0] - 4: result = profile_selector(win)
            continue
        if key in (27, ord("q"), ord("Q")): return
        if key in (curses.KEY_UP, ord("k")): pc = (pc - 1) % max(1, len(profiles))
        elif key in (curses.KEY_DOWN, ord("j")): pc = (pc + 1) % max(1, len(profiles))
        elif key in (10, 13, curses.KEY_ENTER) and profiles: save_profile(profiles[pc])
        elif key in (ord("p"), ord("P")): profile_selector(win)
        elif 0 <= key < 256 and chr(key).lower() in MNEMONICS:
            result = _open_menu(win, MNEMONICS[chr(key).lower()])
            if result == "__EXIT__": return


def main(): curses.wrapper(run); return 0
