"""Turbo C++ inspired full-screen configuration IDE."""
from __future__ import annotations
import curses
from pathlib import Path
from flossware_setup.config_control import available_profiles, effective_config, profiles_dir, state_dir
from flossware_setup.tui.input import enable_mouse, mouse_event
from flossware_setup.tui.widgets import add, palette

MENU=("File","Edit","View","Config","Models","Agents","Optimize","Help")
MENU_KEYS={"f":0,"e":1,"v":2,"c":3,"m":4,"a":5,"o":6,"h":7}
MENU_ITEMS={"File":("Save","Exit"),"Edit":("Reorder menus","Reset layout"),"View":("Profiles","Configuration","Status"),"Config":("Profiles","Create Profile","Validate","Explain"),"Models":("Discover models","Refresh models"),"Agents":("Agent configuration",),"Optimize":("Thompson Sampling","Genetic Optimizer"),"Help":("Keyboard and mouse","About")}

def _profile_path(): return state_dir()/"profile"
def load_active_profile():
    profiles=available_profiles()
    try: value=_profile_path().read_text(encoding="utf-8").strip()
    except OSError: value="personal"
    return value if value in profiles else "personal"
def save_active_profile(name):
    if name not in available_profiles(): raise ValueError(f"unknown profile: {name}")
    _profile_path().parent.mkdir(parents=True,exist_ok=True); _profile_path().write_text(name+"\n",encoding="utf-8")

def _shadow(win,top,left,height,width):
    h,w=win.getmaxyx()
    for y in range(top+1,min(h,top+height+1)):
        try: win.addstr(y,left+2," "*max(0,min(width,w-left-3)),curses.A_DIM)
        except curses.error: pass

def _popup(win,top,left,height,width,title):
    _shadow(win,top,left,height,width); p=curses.newwin(height,width,top,left); p.keypad(True); p.bkgd(" ")
    try: p.box(); p.addstr(0,2,f" {title} ",curses.A_BOLD)
    except curses.error: pass
    return p

def _menu_x_positions():
    x=1; out=[]
    for n in MENU: out.append((n,x,x+len(n)-1)); x+=len(n)+2
    return out

def create_profile(win):
    h,w=win.getmaxyx(); width=min(58,max(34,w-6)); top=max(2,(h-7)//2); left=max(2,(w-width)//2); p=_popup(win,top,left,7,width,"Create Profile")
    p.addstr(2,2,"Name:"); p.addstr(3,2,"> "); p.move(3,4); curses.curs_set(1); curses.echo()
    try: raw=p.getstr(3,4,width-7).decode("utf-8","ignore").strip()
    finally: curses.noecho(); curses.curs_set(0)
    name=raw.lower().replace(" ","-")
    if not name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in name): return None
    if name in {"default","personal","redhat","redhat-cost-conscious"}: return None
    path=profiles_dir()/f"{name}.toml"
    if path.exists(): return None
    path.write_text(f'''profile = "{name}"\n\n[model_policy]\nallowed_providers = ["*configured*"]\nallow_local_models = true\nallow_unconfigured_providers = false\nallow_personal_accounts = true\nallow_provider_fallback = true\n\n[optimization]\nenabled = true\nstrategy = "hybrid"\n\n[cost]\nmonthly_limit_usd = 0.0\nhard_limit = false\n''',encoding="utf-8")
    return name

def profile_selector(win):
    profiles=available_profiles()
    if not profiles:return None
    cur=profiles.index(load_active_profile()) if load_active_profile() in profiles else 0; h,w=win.getmaxyx(); height=min(len(profiles)+4,max(7,h-4)); width=min(max(34,max(map(len,profiles))+10),max(20,w-6)); top=max(2,(h-height)//2); left=max(2,(w-width)//2); p=_popup(win,top,left,height,width,"Select Profile")
    while True:
        for i,name in enumerate(profiles[:height-4]):
            try:p.addstr(2+i,2,("> " if i==cur else "  ")+name.replace("-"," ").title(),curses.A_REVERSE if i==cur else 0)
            except curses.error:pass
        p.noutrefresh(); curses.doupdate(); key=p.getch()
        if key==curses.KEY_MOUSE:
            e=mouse_event()
            if e:
                _x,y,b=e
                if b&(getattr(curses,"BUTTON1_CLICKED",0)|getattr(curses,"BUTTON1_PRESSED",0)):
                    i=y-top-2
                    if 0<=i<min(len(profiles),height-4):save_active_profile(profiles[i]);return profiles[i]
        elif key in (curses.KEY_UP,ord("k")):cur=(cur-1)%len(profiles)
        elif key in (curses.KEY_DOWN,ord("j")):cur=(cur+1)%len(profiles)
        elif key in (10,13,curses.KEY_ENTER):save_active_profile(profiles[cur]);return profiles[cur]
        elif key in (27,ord("q"),ord("Q")):return None

def _popup_menu(win,index):
    name=MENU[index]; items=MENU_ITEMS[name]; h,w=win.getmaxyx(); x=_menu_x_positions()[index][1]; width=min(max(map(len,items))+6,max(14,w-x-2)); height=min(len(items)+2,max(3,h-3)); p=_popup(win,1,x,height,width,name); cur=0
    while True:
        for i,item in enumerate(items[:height-2]):
            try:p.addstr(1+i,1," "+item.ljust(width-3)[:width-3],curses.A_REVERSE if i==cur else 0)
            except curses.error:pass
        p.noutrefresh(); curses.doupdate(); key=p.getch()
        if key in (curses.KEY_LEFT,curses.KEY_RIGHT): return ("__PREV_MENU__" if key==curses.KEY_LEFT else "__NEXT_MENU__")
        if key==curses.KEY_MOUSE:
            e=mouse_event()
            if e:
                mx,my,b=e
                if b&(getattr(curses,"BUTTON1_CLICKED",0)|getattr(curses,"BUTTON1_PRESSED",0)):
                    for j,(_n,lx,rx) in enumerate(_menu_x_positions()):
                        if my==0 and lx<=mx<=rx:return ("__MENU__",j)
                    if x<=mx<x+width and 2<=my<2+len(items):return items[my-2]
                    return None
        elif key in (curses.KEY_UP,ord("k")):cur=(cur-1)%max(1,len(items))
        elif key in (curses.KEY_DOWN,ord("j")):cur=(cur+1)%max(1,len(items))
        elif key in (10,13,curses.KEY_ENTER):return items[cur] if items else None
        elif key in (27,ord("q"),ord("Q")):return None

def _menu_action(win,action):
    if isinstance(action,tuple) and action[0]=="__MENU__":return action
    if action in {"Profiles","Profile"}:return profile_selector(win)
    if action=="Create Profile":return create_profile(win)
    if action=="Exit":return "__EXIT__"
    return None

def _open_menu(win,index):
    while True:
        result=_popup_menu(win,index)
        if result=="__NEXT_MENU__":index=(index+1)%len(MENU);continue
        if result=="__PREV_MENU__":index=(index-1)%len(MENU);continue
        return _menu_action(win,result)

def _draw_main(win,menu_cursor=-1):
    add(win,0,0," "+"  ".join(MENU),1,curses.A_BOLD)
    if menu_cursor>=0:
        n,lx,_=_menu_x_positions()[menu_cursor];add(win,0,lx,n,2,curses.A_REVERSE|curses.A_BOLD)
    add(win,1,0,"-"*max(1,win.getmaxyx()[1]-1),1)

def _box(win,t,l,b,r,title):
    try:
        win.addch(t,l,curses.ACS_ULCORNER);win.hline(t,l+1,curses.ACS_HLINE,max(0,r-l-1));win.addch(t,r,curses.ACS_URCORNER);win.vline(t+1,l,curses.ACS_VLINE,max(0,b-t-1));win.vline(t+1,r,curses.ACS_VLINE,max(0,b-t-1));win.addch(b,l,curses.ACS_LLCORNER);win.hline(b,l+1,curses.ACS_HLINE,max(0,r-l-1));win.addch(b,r,curses.ACS_LRCORNER);add(win,t,l+2,f" {title} ",1,curses.A_BOLD)
    except curses.error:pass

def run(win):
    palette();win.keypad(True);enable_mouse();active=load_active_profile();pc=0;menu=-1
    while True:
        win.erase();h,w=win.getmaxyx();cfg=effective_config(active).resolve();_draw_main(win,menu);left=max(20,min(29,w//4));_box(win,2,1,max(3,h-5),left,"Profiles");profiles=available_profiles();pc=min(pc,max(0,len(profiles)-1))
        for i,name in enumerate(profiles):
            if 4+i>=h-5:break
            add(win,4+i,3,f"{'>' if i==pc else ' '} {name.replace('-',' ').title()}",2 if i==pc else 5,curses.A_BOLD if i==pc else 0)
        pl=left+2;_box(win,2,pl,max(3,h-5),max(pl+2,w-2),"Configuration");fields=[("Provider",cfg.get("provider","unknown")),("Budget",f"${float(cfg.get('budget.monthly',0)):.2f} / month"),("Optimizer",cfg.get("optimization.strategy","unknown")),("Personal accounts","allowed" if cfg.get("policy.allow_personal_accounts") else "blocked")]
        for i,(n,v) in enumerate(fields):add(win,4+i,pl+3,f"{n:<22} {v}",5)
        add(win,h-4,2,f"Profile: {active.upper()} | Provider: {cfg.get('provider','unknown')} | READY",1,curses.A_BOLD);add(win,h-3,2,"Alt+letter menus | Arrows navigate | Enter select | Mouse click",6);add(win,h-2,2,"F-keys optional | Esc/Q Exit",6);win.refresh();key=win.getch()
        if key==curses.KEY_MOUSE:
            e=mouse_event()
            if e:
                x,y,b=e;clicked=getattr(curses,"BUTTON1_CLICKED",0)|getattr(curses,"BUTTON1_PRESSED",0)
                if b&clicked:
                    if y==0:
                        for i,(_n,lx,rx) in enumerate(_menu_x_positions()):
                            if lx<=x<=rx:
                                menu=i;chosen=_open_menu(win,i);menu=-1
                                if isinstance(chosen,tuple) and chosen[0]=="__MENU__":chosen=_open_menu(win,chosen[1])
                                if chosen=="__EXIT__":return
                                if chosen:active=chosen
                                break
                    elif 4<=y<4+len(profiles) and 2<=x<left:pc=y-4;active=profiles[pc];save_active_profile(active)
                    elif h-4<=y<=h-3:chosen=profile_selector(win);active=chosen or active
            continue
        if key in (27,ord("q"),ord("Q")):return
        if key in (curses.KEY_UP,ord("k")):pc=(pc-1)%max(1,len(profiles))
        elif key in (curses.KEY_DOWN,ord("j")):pc=(pc+1)%max(1,len(profiles))
        elif key in (10,13,curses.KEY_ENTER) and profiles:active=profiles[pc];save_active_profile(active)
        elif key in (ord("p"),ord("P")):chosen=profile_selector(win);active=chosen or active
        elif 0<=key<256 and chr(key).lower() in MENU_KEYS:
            i=MENU_KEYS[chr(key).lower()];menu=i;chosen=_open_menu(win,i);menu=-1
            if chosen=="__EXIT__":return
            if isinstance(chosen,tuple) and chosen[0]=="__MENU__":chosen=_open_menu(win,chosen[1])
            if chosen:active=chosen

def main():curses.wrapper(run);return 0
