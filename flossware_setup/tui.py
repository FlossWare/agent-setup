"""Curses presentation and interaction layer."""
import curses
from .catalog import AGENTS, CAPABILITIES, BUDGET_POLICIES, PROVIDERS
from .config import Config, load_state
from .credentials import status as credential_status
from .installer import install_packages, generate_artifacts

def palette():
    curses.start_color(); curses.use_default_colors()
    for i,c in enumerate((curses.COLOR_CYAN,curses.COLOR_GREEN,curses.COLOR_YELLOW,curses.COLOR_RED,curses.COLOR_WHITE,curses.COLOR_MAGENTA),1): curses.init_pair(i,c,-1)

def enable_mouse():
    try:
        mask=curses.ALL_MOUSE_EVENTS | getattr(curses,"REPORT_MOUSE_POSITION",0); curses.mousemask(mask); curses.mouseinterval(200); return True
    except (AttributeError,curses.error): return False

def click():
    try: _,x,y,_,state=curses.getmouse()
    except curses.error: return None
    if state & (getattr(curses,"BUTTON1_CLICKED",0)|getattr(curses,"BUTTON1_PRESSED",0)): return x,y
    return None

def add(win,y,x,text,pair=5,attr=0):
    h,w=win.getmaxyx()
    if 0<=y<h and x<w-1:
        try: win.addnstr(y,max(0,x),text,max(0,w-max(0,x)-1),curses.color_pair(pair)|attr)
        except curses.error: pass

def header(win,title):
    win.erase(); _,w=win.getmaxyx(); line="="*min(max(10,w-4),72); add(win,1,2,line,1); add(win,2,2,f" FlossWare AI | {title} ",1,curses.A_BOLD); add(win,3,2,line,1); return 5

def menu(win,title,items,selected=None,multi=True):
    selected=set(selected or []); cursor=0
    while True:
        y=header(win,title); h,_=win.getmaxyx(); visible=min(len(items),max(0,h-y-3))
        for i,(name,desc) in enumerate(items[:visible]):
            mark="[x]" if i in selected else "[ ]" if multi else "(o)" if i==cursor else "( )"
            add(win,y+i,2,"> " if i==cursor else "  ",1 if i==cursor else 5,curses.A_BOLD if i==cursor else 0); add(win,y+i,5,mark,2 if i in selected or (not multi and i==cursor) else 3); add(win,y+i,10,name,1 if i==cursor else 5,curses.A_BOLD if i==cursor else 0); add(win,y+i,12+len(name),desc)
        add(win,h-2,2,"↑/↓ navigate  Space/click toggle  Enter confirm  a all  n none  q back",6); win.refresh(); key=win.getch()
        if key==curses.KEY_MOUSE:
            pos=click()
            if pos:
                _,cy=pos; i=cy-y
                if 0<=i<visible:
                    cursor=i
                    if multi: selected.remove(i) if i in selected else selected.add(i)
                    else:return cursor
        elif key in (curses.KEY_UP,ord('k')): cursor=max(0,cursor-1)
        elif key in (curses.KEY_DOWN,ord('j')): cursor=min(max(0,len(items)-1),cursor+1)
        elif multi and key==ord(' '): selected.remove(cursor) if cursor in selected else selected.add(cursor)
        elif multi and key==ord('a'): selected=set(range(len(items)))
        elif multi and key==ord('n'): selected.clear()
        elif key in (10,13,curses.KEY_ENTER): return sorted(selected) if multi else cursor
        elif key in (ord('q'),27): return None

def review(win,repo):
    state=load_state(repo); y=header(win,"Review Current Configuration"); h,_=win.getmaxyx()
    if not state: lines=["No generated FlossWare configuration found.","Configure and build the setup first."]
    else:
        lines=[f"Profile: {state.get('profile','default')}",f"Agents: {len(state.get('agents',[]))} of {len(AGENTS)} configured","", "Configured agents:"]+[f"  ✓ {a.name}" for a in AGENTS if a.id in state.get("agents",[])]+["","Capabilities:"]+[f"  ✓ {x}" for x in state.get("capabilities",[])]+["","Providers:"]+[f"  {'✓' if v else '·'} {k}: {'configured' if v else 'not configured'}" for k,v in state.get("providers",{}).items()]+["",f"Budget: {state.get('budget_policy','unknown')}  ${state.get('monthly_budget',0):g}","Credentials: values never displayed or stored","Security: ✓ secret-free generated configuration"]
    for i,line in enumerate(lines[:max(1,h-y-3)]): add(win,y+i,2,line,2 if "✓" in line else 5)
    add(win,h-2,2,"Enter/Esc/q back",6); win.refresh()
    while win.getch() not in (10,13,27,ord('q')): pass

def configure(win):
    cfg=Config(); a=menu(win,"Coding Agents",[(x.name,x.description) for x in AGENTS]);
    if a is None or not a:return None
    cfg.agents=a; c=menu(win,"FlossWare Capabilities",[(x[0],x[1]) for x in CAPABILITIES],[i for i,x in enumerate(CAPABILITIES) if x[2]]); 
    if c is None:return None
    cfg.capabilities=c; b=menu(win,"Budget Policy",[(x[0],x[2]) for x in BUDGET_POLICIES],multi=False)
    if b is None:return None
    cfg.budget_index=b; cfg.budget_amount=BUDGET_POLICIES[b][1] if BUDGET_POLICIES[b][1]>=0 else 50.; cfg.repo_dir="."
    return cfg

def run(stdscr):
    curses.curs_set(0); stdscr.keypad(True); palette(); mouse=enable_mouse();
    while True:
        choice=menu(stdscr,"Setup Control Center",[("Review Current Configuration","Inspect persisted project configuration"),("Configure / Change Setup","Select agents, capabilities and budget"),("Provider Credentials","View detected credential sources"),("Exit","Leave Setup")],multi=False)
        if choice in (None,3): return
        if choice==0: review(stdscr,".")
        elif choice==2:
            y=header(stdscr,"Provider Credentials"); s=credential_status();
            for i,(n,_,_) in enumerate(PROVIDERS): add(stdscr,y+i,2,f"{'SET' if s[n] else '---'}  {n}",2 if s[n] else 3)
            add(stdscr,stdscr.getmaxyx()[0]-2,2,"Enter/q back",6); stdscr.refresh(); stdscr.getch()
        else:
            cfg=configure(stdscr)
            if cfg:
                try: install_packages(cfg.capabilities); generate_artifacts(cfg); review(stdscr,cfg.repo_dir)
                except Exception as exc:
                    y=header(stdscr,"Setup Error"); add(stdscr,y,2,str(exc),4); add(stdscr,y+2,2,"Press any key.",6); stdscr.refresh(); stdscr.getch()

def main():
    curses.wrapper(run)
