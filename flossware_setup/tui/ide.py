"""Turbo C++ inspired full-screen configuration IDE with persistent overlays."""
from __future__ import annotations

import curses
from pathlib import Path

from flossware_setup.config_control import available_profiles, effective_config, state_dir
from flossware_setup.tui.input import enable_mouse, mouse_event
from flossware_setup.tui.widgets import add, palette

MENU = ("File", "Edit", "View", "Config", "Models", "Agents", "Optimize", "Help")
MENU_ITEMS = {
    "File": ("Save", "Exit"), "Edit": ("Reorder menus", "Reset layout"),
    "View": ("Profiles", "Configuration", "Status"), "Config": ("Profiles", "Validate", "Explain"),
    "Models": ("Discover models", "Refresh models"), "Agents": ("Agent configuration",),
    "Optimize": ("Thompson Sampling", "Genetic Optimizer"), "Help": ("Keyboard and mouse", "About"),
}
MENU_KEYS = {"f":"File","e":"Edit","v":"View","c":"Config","m":"Models","a":"Agents","o":"Optimize","h":"Help"}

def _profile_path() -> Path: return state_dir() / "profile"

def load_active_profile() -> str:
    profiles = available_profiles()
    try: value = _profile_path().read_text(encoding="utf-8").strip()
    except OSError: value = "personal"
    return value if value in profiles else "personal"

def save_active_profile(name: str) -> None:
    if name not in available_profiles(): raise ValueError(f"unknown profile: {name}")
    _profile_path().parent.mkdir(parents=True, exist_ok=True); _profile_path().write_text(name+"\n", encoding="utf-8")

def _shadow(win, top, left, height, width):
    h,w=win.getmaxyx(); sx,sy=left+2,top+1
    for y in range(sy,min(h,top+height+1)):
        try: win.addstr(y,sx," "*max(0,min(width,w-sx-1)),curses.A_DIM)
        except curses.error: pass

def _popup(win, top, left, height, width, title):
    _shadow(win,top,left,height,width); popup=curses.newwin(height,width,top,left); popup.keypad(True); popup.bkgd(" ")
    try: popup.box(); popup.addstr(0,2,f" {title} ",curses.A_BOLD)
    except curses.error: pass
    return popup

def _menu_x_positions():
    x,result=1,[]
    for name in MENU: start=x; x+=len(name)+2; result.append((name,start,x-1))
    return result

def _popup_menu(win,name,x):
    items=MENU_ITEMS.get(name,()); h,w=win.getmaxyx(); width=min(max((len(i) for i in items),default=10)+6,max(14,w-x-2)); height=min(len(items)+2,max(3,h-3))
    popup=_popup(win,1,x,height,width,name); cursor=0
    while True:
        for i,item in enumerate(items[:height-2]):
            try: popup.addstr(1+i,1," "+item.ljust(width-3)[:width-3],curses.A_REVERSE if i==cursor else 0)
            except curses.error: pass
        popup.noutrefresh(); curses.doupdate(); key=popup.getch()
        if key==curses.KEY_MOUSE:
            event=mouse_event()
            if event:
                mx,my,bstate=event
                if bstate & (getattr(curses,"BUTTON1_CLICKED",0)|getattr(curses,"BUTTON1_PRESSED",0)):
                    if x<=mx<x+width and 2<=my<2+len(items): return items[my-2]
                    return None
        elif key in (curses.KEY_UP,ord("k")): cursor=(cursor-1)%max(1,len(items))
        elif key in (curses.KEY_DOWN,ord("j")): cursor=(cursor+1)%max(1,len(items))
        elif key in (10,13,curses.KEY_ENTER): return items[cursor] if items else None
        elif key in (27,ord("q"),ord("Q")): return None

def profile_selector(win):
    profiles=available_profiles()
    if not profiles: return None
    current=load_active_profile(); cursor=profiles.index(current) if current in profiles else 0; h,w=win.getmaxyx(); height=min(len(profiles)+4,max(7,h-4)); width=min(max(34,max(map(len,profiles))+10),max(20,w-6)); top,left=max(2,(h-height)//2),max(2,(w-width)//2); popup=_popup(win,top,left,height,width,"Select Profile")
    while True:
        for i,profile in enumerate(profiles[:height-4]):
            try: popup.addstr(2+i,2,("> " if i==cursor else "  ")+profile.replace("-"," ").title(),curses.A_REVERSE if i==cursor else 0)
            except curses.error: pass
        try: popup.addstr(height-2,2,"Enter Select   Esc Cancel   Mouse",curses.A_DIM)
        except curses.error: pass
        popup.noutrefresh(); curses.doupdate(); key=popup.getch()
        if key==curses.KEY_MOUSE:
            event=mouse_event()
            if event:
                _x,y,bstate=event
                if bstate & (getattr(curses,"BUTTON1_CLICKED",0)|getattr(curses,"BUTTON1_PRESSED",0)):
                    local=y-top-2
                    if 0<=local<min(len(profiles),height-4): save_active_profile(profiles[local]); return profiles[local]
        elif key in (curses.KEY_UP,ord("k")): cursor=(cursor-1)%len(profiles)
        elif key in (curses.KEY_DOWN,ord("j")): cursor=(cursor+1)%len(profiles)
        elif key in (10,13,curses.KEY_ENTER): save_active_profile(profiles[cursor]); return profiles[cursor]
        elif key in (27,ord("q"),ord("Q")): return None

def _effective_profile_config(profile):
    try: return effective_config(profile).resolve()
    except Exception: return {}

def _draw_main(win,menu_cursor=-1):
    add(win,0,0," "+"  ".join(MENU),1,curses.A_BOLD)
    if 0<=menu_cursor<len(MENU):
        name,lx,_rx=_menu_x_positions()[menu_cursor]; add(win,0,lx,name,2,curses.A_REVERSE|curses.A_BOLD)
    add(win,1,0,"-"*max(1,win.getmaxyx()[1]-1),1)

def _draw_box(win,top,left,bottom,right,title):
    try:
        win.addch(top,left,curses.ACS_ULCORNER); win.hline(top,left+1,curses.ACS_HLINE,max(0,right-left-1)); win.addch(top,right,curses.ACS_URCORNER); win.vline(top+1,left,curses.ACS_VLINE,max(0,bottom-top-1)); win.vline(top+1,right,curses.ACS_VLINE,max(0,bottom-top-1)); win.addch(bottom,left,curses.ACS_LLCORNER); win.hline(bottom,left+1,curses.ACS_HLINE,max(0,right-left-1)); win.addch(bottom,right,curses.ACS_LRCORNER); add(win,top,left+2,f" {title} ",1,curses.A_BOLD)
    except curses.error: pass

def _run_menu_action(win,action):
    if action in {"Profiles","Profile"}: return profile_selector(win)
    if action=="Exit": return "__EXIT__"
    return None

def run(win):
    palette(); win.keypad(True); enable_mouse(); active=load_active_profile(); profile_cursor=0; menu_cursor=-1
    while True:
        win.erase(); h,w=win.getmaxyx(); config=_effective_profile_config(active); _draw_main(win,menu_cursor); left=max(20,min(29,w//4)); _draw_box(win,2,1,max(3,h-5),left,"Profiles"); profiles=available_profiles(); profile_cursor=min(profile_cursor,max(0,len(profiles)-1))
        for i,profile in enumerate(profiles):
            if 4+i>=h-5: break
            add(win,4+i,3,f"{'>' if profile==active else ' '} {profile.replace('-',' ').title()}",2 if profile==active else 5,curses.A_REVERSE if i==profile_cursor else 0)
        panel_left=left+2; _draw_box(win,2,panel_left,max(3,h-5),max(panel_left+2,w-2),"Configuration"); fields=[("Provider",config.get("provider","unknown")),("Budget",f"${float(config.get('budget.monthly',0)):.2f} / month"),("Optimizer",config.get("optimization.strategy","unknown")),("Personal accounts","allowed" if config.get("policy.allow_personal_accounts") else "blocked"),("Provider fallback","allowed" if config.get("policy.allow_provider_fallback") else "blocked")]
        for i,(name,value) in enumerate(fields): add(win,4+i,panel_left+3,f"{name:<22} {value}",5)
        add(win,h-4,2,f"Profile: {active.upper()}   |   Provider: {config.get('provider','unknown')}   |   READY",1,curses.A_BOLD); add(win,h-3,2,"Alt+letter menu   Arrows navigate   Enter select   Mouse click",6); add(win,h-2,2,"F-keys optional   |   Esc/Q Exit",6); win.refresh(); key=win.getch()
        if key==curses.KEY_MOUSE:
            event=mouse_event()
            if event:
                x,y,bstate=event; clicked=getattr(curses,"BUTTON1_CLICKED",0)|getattr(curses,"BUTTON1_PRESSED",0)
                if bstate&clicked:
                    if y==0:
                        for idx,(menu_name,lx,rx) in enumerate(_menu_x_positions()):
                            if lx<=x<=rx:
                                menu_cursor=idx; chosen=_run_menu_action(win,_popup_menu(win,menu_name,lx)); menu_cursor=-1
                                if chosen=="__EXIT__": return
                                if chosen: active=chosen
                                break
                    elif 4<=y<4+len(profiles) and 2<=x<left: profile_cursor=y-4; chosen=profile_selector(win); active=chosen or active
                    elif h-4<=y<=h-3: chosen=profile_selector(win); active=chosen or active
            continue
        if key in (ord("q"),ord("Q")): return
        if key==27:
            win.nodelay(True); nxt=win.getch(); win.nodelay(False)
            if nxt in (ord("q"),ord("Q")): return
            menu_name=MENU_KEYS.get(chr(nxt).lower()) if nxt!=-1 else None
            if menu_name:
                idx=MENU.index(menu_name); menu_cursor=idx; chosen=_run_menu_action(win,_popup_menu(win,menu_name,_menu_x_positions()[idx][1])); menu_cursor=-1
                if chosen=="__EXIT__": return
                if chosen: active=chosen
            continue
        if key in (curses.KEY_UP,ord("k")): profile_cursor=(profile_cursor-1)%max(1,len(profiles))
        elif key in (curses.KEY_DOWN,ord("j")): profile_cursor=(profile_cursor+1)%max(1,len(profiles))
        elif key in (10,13,curses.KEY_ENTER) and profiles: save_active_profile(profiles[profile_cursor]); active=profiles[profile_cursor]
        elif key in (ord("p"),ord("P")): chosen=profile_selector(win); active=chosen or active
        elif key==curses.KEY_F7: chosen=profile_selector(win); active=chosen or active
        elif key==curses.KEY_F6: _popup_menu(win,"Models",_menu_x_positions()[MENU.index("Models")][1])
        elif key==curses.KEY_F8: _popup_menu(win,"Optimize",_menu_x_positions()[MENU.index("Optimize")][1])
        elif key==curses.KEY_F10:
            chosen=_popup_menu(win,"File",_menu_x_positions()[0][1])
            if chosen in {"Exit","__EXIT__"}: return

def main():
    curses.wrapper(run); return 0
