#!/usr/bin/env python3
"""FlossWare AI operator TUI for agent/component/runtime configuration."""
from __future__ import annotations
import curses, json, os, subprocess
from pathlib import Path

def _load_agent_ids():
    import importlib.util
    import sys
    setup_path = Path(__file__).resolve().parent / "setup.py"
    spec = importlib.util.spec_from_file_location("flossware_setup_registry", setup_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return [a.id for a in mod.AGENT_ADAPTERS]


AGENTS = _load_agent_ids()
COMPONENTS=["model-router-ai","resilience-ai","structured-output-ai","consensus-ai","evaluation-ai","observability-ai","security-ai","rag-ai","genetic-optimizer-ai"]
RUNTIMES=["auto","podman","docker","native"]
DECORATORS=["security","routing","cache","retry","circuit-breaker","observability","evaluation","cost-accounting"]
DESCRIPTIONS={
"model-router-ai":"Routes requests across configured models using policy, availability, capability and routing strategy.",
"resilience-ai":"Adds retries, fallbacks, circuit breaking and graceful recovery around AI operations.",
"structured-output-ai":"Produces and validates reliable schema-constrained model output.",
"consensus-ai":"Combines independent model responses and evaluates agreement and confidence.",
"evaluation-ai":"Measures AI responses against configurable quality and evaluation criteria.",
"observability-ai":"Provides traces, metrics and operational visibility into AI workflows.",
"security-ai":"Applies security controls, validation and policy checks to AI operations.",
"rag-ai":"Retrieves relevant knowledge and supplies grounded context to downstream AI agents.",
"genetic-optimizer-ai":"Optimizes model and workflow parameters using evolutionary search strategies.",
"auto":"Prefer Podman on Linux, otherwise the first healthy supported container runtime.",
"podman":"Use Podman when installed and reachable.","docker":"Use Docker when installed and reachable.","native":"Do not use a container runtime.",
}
ROOT=Path(os.environ.get("FLOSSWARE_AI_ROOT",Path.home()/"\.flossware"/"ai"))

def run_menu(stdscr,title,items,multi=True,descriptions=None):
    pos,selected=0,set(); descriptions=descriptions or {}
    while True:
        stdscr.erase(); h,w=stdscr.getmaxyx(); stdscr.addstr(1,2,"="*min(w-4,72)); stdscr.addstr(2,2,f" FlossWare AI | {title}",curses.A_BOLD); stdscr.addstr(3,2,"="*min(w-4,72))
        visible=items[:max(1,h-9)]
        for i,item in enumerate(visible):
            mark="[x]" if i in selected else "[ ]"; attr=curses.A_REVERSE if i==pos else 0; stdscr.addnstr(5+i,2,f"{mark} {item}",w-4,attr)
        desc=descriptions.get(items[pos],"") if items else ""
        if desc: stdscr.addnstr(h-4,2,desc,w-4,curses.A_DIM)
        stdscr.addnstr(h-2,2,"↑/↓ move  Space select  Enter confirm  a all  n none  q back",w-4); stdscr.refresh(); k=stdscr.getch()
        if k in(curses.KEY_UP,ord('k')): pos=max(0,pos-1)
        elif k in(curses.KEY_DOWN,ord('j')): pos=min(len(items)-1,pos+1)
        elif k==ord(' '):
            if multi: selected.symmetric_difference_update({pos})
            else: selected={pos}
        elif k==ord('a') and multi: selected=set(range(len(items)))
        elif k==ord('n') and multi: selected.clear()
        elif k in(10,13,curses.KEY_ENTER): return sorted(selected)
        elif k in(ord('q'),27): return None

def _run_discovery(command):
    """Run the installed discovery CLI without ever exposing credential values."""
    python=ROOT/"venv/bin/python"; script=ROOT/"discovery.py"
    try:
        result=subprocess.run([str(python),str(script),*command],capture_output=True,text=True,timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return f"Discovery failed: {exc}"
    output=result.stdout.strip() or result.stderr.strip() or "No discovery output."
    return output

def discovery_menu(stdscr):
    """Expose the same provider/account/model inventory used by the CLI."""
    choices=["Providers","Accounts","Verified Accounts","All Models","Available Models","Free Models","Doctor"]
    ids=run_menu(stdscr,"Live Account / Model Discovery",choices,multi=False)
    if not ids: return
    commands={0:["providers"],1:["accounts"],2:["accounts","--verify"],3:["models"],4:["models","--available"],5:["models","--free"],6:["doctor"]}
    _pager(stdscr,f"Discovery | {choices[ids[0]]}",_run_discovery(commands[ids[0]]))

def _pager(stdscr,title,text):
    """Display arbitrary discovery output without truncating long model inventories."""
    lines=text.splitlines() or [""]; offset=0
    while True:
        stdscr.erase(); h,w=stdscr.getmaxyx(); stdscr.addnstr(1,2,title,w-4,curses.A_BOLD); usable=max(1,h-5)
        for row,line in enumerate(lines[offset:offset+usable]): stdscr.addnstr(3+row,2,line,w-4)
        footer="↑/↓ scroll  PgUp/PgDn page  q back"
        stdscr.addnstr(h-2,2,footer,w-4,curses.A_DIM); stdscr.refresh(); k=stdscr.getch()
        if k in(ord('q'),27,10,13,curses.KEY_ENTER): return
        if k in(curses.KEY_DOWN,ord('j')): offset=min(max(0,len(lines)-usable),offset+1)
        elif k in(curses.KEY_UP,ord('k')): offset=max(0,offset-1)
        elif k==curses.KEY_NPAGE: offset=min(max(0,len(lines)-usable),offset+usable)
        elif k==curses.KEY_PPAGE: offset=max(0,offset-usable)

def runtime_menu(stdscr):
    try: data=json.loads(subprocess.check_output([str(ROOT/"venv/bin/python"),str(ROOT/"runtime.py"),"status"],text=True))
    except Exception as exc: data={"selected":"auto","effective":"native","runtimes":[],"error":str(exc)}
    ids=run_menu(stdscr,"Container Runtime",RUNTIMES,multi=False,descriptions=DESCRIPTIONS)
    if ids:
        value=RUNTIMES[ids[0]]; subprocess.run([str(ROOT/"venv/bin/python"),str(ROOT/"runtime.py"),"select",value],check=False)
        stdscr.erase(); stdscr.addstr(2,2,f"Runtime preference: {value}"); stdscr.addstr(4,2,f"Effective runtime: {data.get('effective','unknown')}"); stdscr.addstr(6,2,"Press any key..."); stdscr.refresh(); stdscr.getch()

def decorator_menu(stdscr):
    stack_file=ROOT/"state"/"decorator-stack.json"; stack_file.parent.mkdir(parents=True,exist_ok=True)
    try: stack=json.loads(stack_file.read_text())
    except Exception: stack=DECORATORS.copy()
    pos=0
    while True:
        stdscr.erase(); h,w=stdscr.getmaxyx(); stdscr.addstr(2,2,"FlossWare AI | Cross-Cutting Decorator Stack",curses.A_BOLD); stdscr.addstr(4,2,"Outer → Inner",curses.A_DIM)
        for i,name in enumerate(stack): stdscr.addnstr(6+i,2,f"{i+1:2}. {name}",w-4,curses.A_REVERSE if i==pos else 0)
        stdscr.addnstr(h-4,2,"↑/↓ select  ←/→ reorder  s save  q back",w-4); stdscr.refresh(); k=stdscr.getch()
        if k in(curses.KEY_UP,ord('k')): pos=max(0,pos-1)
        elif k in(curses.KEY_DOWN,ord('j')): pos=min(len(stack)-1,pos+1)
        elif k==curses.KEY_LEFT and pos>0: stack[pos-1],stack[pos]=stack[pos],stack[pos-1]; pos-=1
        elif k==curses.KEY_RIGHT and pos<len(stack)-1: stack[pos+1],stack[pos]=stack[pos],stack[pos+1]; pos+=1
        elif k==ord('s'): stack_file.write_text(json.dumps(stack,indent=2)+"\n"); os.chmod(stack_file,0o600)
        elif k in(ord('q'),27): return

def main():
    def app(stdscr):
        curses.curs_set(0); stdscr.keypad(True)
        while True:
            choice=run_menu(stdscr,"Control Plane",["Agents","Components","Cross-Cutting Behavior","Container Runtime","Accounts / Models","Doctor","Exit"],False)
            if choice is None or choice==[6]: return
            if choice==[0]:
                ids=run_menu(stdscr,"Coding Agents",AGENTS)
                if ids: _pause(stdscr,"Selected: "+", ".join(AGENTS[i] for i in ids))
            elif choice==[1]:
                ids=run_menu(stdscr,"Composable FlossWare AI Components",COMPONENTS,descriptions=DESCRIPTIONS)
                if ids: _pause(stdscr,DESCRIPTIONS.get(COMPONENTS[ids[0]],""))
            elif choice==[2]: decorator_menu(stdscr)
            elif choice==[3]: runtime_menu(stdscr)
            elif choice==[4]: discovery_menu(stdscr)
            elif choice==[5]:
                p=subprocess.run([str(ROOT/"venv/bin/python"),str(ROOT/"discovery.py"),"doctor"],capture_output=True,text=True); _pause(stdscr,p.stdout or p.stderr)
    curses.wrapper(app)

def _pause(stdscr,text):
    stdscr.erase(); stdscr.addnstr(2,2,text,max(1,stdscr.getmaxyx()[1]-4)); stdscr.addstr(5,2,"Press any key..."); stdscr.refresh(); stdscr.getch()

if __name__=="__main__": main()
