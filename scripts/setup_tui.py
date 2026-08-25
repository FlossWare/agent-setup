#!/usr/bin/env python3
"""Full FlossWare AI setup control-plane TUI."""
from __future__ import annotations
import curses, json, os, subprocess
from pathlib import Path

AGENTS=[("Claude Code","claude-code","CLAUDE.md"),("Cursor","cursor",".cursorrules"),("OpenCode","opencode","AGENTS.md"),("Crush","crush","AGENTS.md"),("Codex","codex","AGENTS.md"),("Aider","aider","CONVENTIONS.md"),("Cline","cline",".clinerules/FlossWare.md"),("Roo Code","roo-code",".roo/rules/FlossWare.md"),("Gemini CLI","gemini-cli","GEMINI.md"),("GitHub Copilot","github-copilot",".github/copilot-instructions.md"),("Windsurf","windsurf",".windsurfrules"),("Amazon Q Developer","amazon-q",".amazonq/rules/FlossWare.md"),("Kiro","kiro",".kiro/steering/FlossWare.md")]
COMPONENTS=[("Model Router","model-router-ai","Routes requests across configured providers, accounts and models."),("Resilience","resilience-ai","Retries, fallbacks, circuit breakers and graceful recovery."),("Structured Output","structured-output-ai","Validates schema-constrained model output."),("Consensus","consensus-ai","Combines independent model responses and confidence."),("Evaluation","evaluation-ai","Scores responses and performs verification."),("Observability","observability-ai","Provides traces, metrics and operational visibility."),("Security","security-ai","Applies validation, policy and security controls."),("RAG","rag-ai","Retrieves relevant knowledge for grounded generation."),("Genetic Optimizer","genetic-optimizer-ai","Optimizes workflow and model parameters.")]
RUNTIMES=[("Auto","auto","Use the first healthy runtime according to platform policy."),("Podman","podman","Preferred container runtime on Linux."),("Docker","docker","Docker Engine or Docker Desktop."),("Native","native","Do not use a container runtime.")]
DECORATORS=[("Security / Policy","security"),("Model Routing","routing"),("Cache","cache"),("Retry","retry"),("Circuit Breaker","circuit-breaker"),("Observability","observability"),("Evaluation","evaluation"),("Cost / Token Accounting","cost-accounting")]
ROOT=Path(os.environ.get("FLOSSWARE_AI_ROOT",Path.home()/".flossware"/"ai")); STATE=ROOT/"state"

def load(path,default):
    try:return json.loads(path.read_text())
    except (OSError,ValueError):return default

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+"\n");os.chmod(path,0o600)

def menu(win,title,items,multi=False):
    cursor=0;selected=set()
    while True:
        win.erase();h,w=win.getmaxyx();win.addnstr(1,2,"="*min(76,w-4),w-4);win.addnstr(2,2,f" FlossWare AI | {title}",w-4,curses.A_BOLD);win.addnstr(3,2,"="*min(76,w-4),w-4)
        for i,item in enumerate(items[:max(1,h-9)]):
            label=item[0] if isinstance(item,tuple) else item;mark=("[x]" if i in selected else "[ ]") if multi else ("●" if i==cursor else "○");win.addnstr(5+i,2,f"{mark} {label}",w-4,curses.A_REVERSE if i==cursor else 0)
        win.addnstr(h-2,2,"↑↓ navigate  Space toggle  Enter select  a all  n none  q back",w-4,curses.A_DIM);win.refresh();k=win.getch()
        if k in(curses.KEY_UP,ord('k')):cursor=max(0,cursor-1)
        elif k in(curses.KEY_DOWN,ord('j')):cursor=min(len(items)-1,cursor+1)
        elif multi and k==ord(' '):selected.symmetric_difference_update({cursor})
        elif multi and k==ord('a'):selected=set(range(len(items)))
        elif multi and k==ord('n'):selected.clear()
        elif k in(10,13,curses.KEY_ENTER):return sorted(selected) if multi else cursor
        elif k in(ord('q'),27):return None

def pause(win,title,lines):
    win.erase();h,w=win.getmaxyx();win.addnstr(1,2,f" FlossWare AI | {title}",w-4,curses.A_BOLD)
    for i,line in enumerate(lines[:h-5]):win.addnstr(3+i,2,str(line),w-4)
    win.addnstr(h-2,2,"Press any key to return",w-4,curses.A_DIM);win.refresh();win.getch()

def agents(win):
    ids=menu(win,"Coding Agents",AGENTS,multi=True)
    if ids is None:return
    win.erase();win.addstr(2,2,"Project repository path [.] : ");curses.echo();win.move(2,29);repo=win.getstr(2,29,240).decode().strip() or ".";curses.noecho()
    py=ROOT/"venv/bin/python";script=ROOT/"agent_setup.py";out=[]
    for i in ids:
        p=subprocess.run([str(py),str(script),AGENTS[i][1],"--repo",repo],capture_output=True,text=True) if script.exists() else None;out.append(f"{AGENTS[i][0]}: {'READY' if p and p.returncode==0 else 'FAILED'}")
    pause(win,"Agent Integration",out)

def decorators(win):
    path=STATE/"decorator-stack.json";default=[x[1] for x in DECORATORS];stack=load(path,default);stack=[x for x in stack if x in default]+[x for x in default if x not in stack];cursor=0
    while True:
        win.erase();h,w=win.getmaxyx();win.addnstr(1,2," FlossWare AI | Decorator Pipeline",w-4,curses.A_BOLD);win.addnstr(3,2,"Outer → Inner",w-4,curses.A_DIM)
        for i,key in enumerate(stack[:h-8]):label=next(x[0] for x in DECORATORS if x[1]==key);win.addnstr(5+i,2,f"{i+1:2}. {label}",w-4,curses.A_REVERSE if i==cursor else 0)
        win.addnstr(h-4,2,"VALID: unique, complete decorator stack",w-4,curses.A_BOLD);win.addnstr(h-2,2,"↑↓ select  ←→ reorder  s save  r reset  q back",w-4,curses.A_DIM);win.refresh();k=win.getch()
        if k in(curses.KEY_UP,ord('k')):cursor=max(0,cursor-1)
        elif k in(curses.KEY_DOWN,ord('j')):cursor=min(len(stack)-1,cursor+1)
        elif k==curses.KEY_LEFT and cursor:stack[cursor-1],stack[cursor]=stack[cursor],stack[cursor-1];cursor-=1
        elif k==curses.KEY_RIGHT and cursor<len(stack)-1:stack[cursor+1],stack[cursor]=stack[cursor],stack[cursor+1];cursor+=1
        elif k==ord('r'):stack=default.copy();cursor=0
        elif k==ord('s'):save(path,stack);pause(win,"Decorator Pipeline",["Saved.","Outer → Inner order is preserved."])
        elif k in(ord('q'),27):return

def runtime(win):
    idx=menu(win,"Container Runtime",RUNTIMES)
    if idx is None:return
    py=ROOT/"venv/bin/python";script=ROOT/"runtime.py";value=RUNTIMES[idx][1];out=[f"Preference: {value}"]
    if script.exists():
        subprocess.run([str(py),str(script),"select",value],capture_output=True,text=True);p=subprocess.run([str(py),str(script),"status"],capture_output=True,text=True)
        try:d=json.loads(p.stdout);out += [f"Effective: {d.get('effective','unknown')}",f"Podman: {d.get('runtimes',{}).get('podman',{}).get('status','unknown')}",f"Docker: {d.get('runtimes',{}).get('docker',{}).get('status','unknown')}"]
        except ValueError:out.append(p.stdout or p.stderr)
    pause(win,"Container Runtime",out)

def discovery(win,cmd,title):
    p=subprocess.run([str(ROOT/"venv/bin/python"),str(ROOT/"discovery.py"),*cmd],capture_output=True,text=True);pause(win,title,(p.stdout or p.stderr or "No output").splitlines())

def main():
    def app(win):
        curses.curs_set(0);win.keypad(True)
        while True:
            profile=(STATE/"active-profile").read_text().strip() if (STATE/"active-profile").exists() else "personal"
            items=[("Profile","profile"),("Agents","agents"),("Components","components"),("Cross-Cutting Behavior","decorators"),("Container Runtime","runtime"),("Accounts / Models","accounts"),("Doctor","doctor"),("Exit","exit")]
            idx=menu(win,f"Setup Control Plane | profile: {profile}",items)
            if idx is None or idx==7:return
            key=items[idx][1]
            if key=="profile":
                p=menu(win,"Profile",[("Personal","personal"),("Red Hat","redhat")]);
                if p is not None:STATE.mkdir(parents=True,exist_ok=True);(STATE/"active-profile").write_text(("personal","redhat")[p]+"\n")
            elif key=="agents":agents(win)
            elif key=="components":pause(win,"Components",["Select components from the CLI for installation:","flossware-ai components","The TUI controls the setup policy; artifacts are preferred."])
            elif key=="decorators":decorators(win)
            elif key=="runtime":runtime(win)
            elif key=="accounts":discovery(win,["accounts","--verify"],"Accounts / Identities")
            elif key=="doctor":discovery(win,["doctor"],"Doctor")
    curses.wrapper(app)

if __name__=="__main__":main()
