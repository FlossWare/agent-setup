#!/usr/bin/env python3
"""Full FlossWare AI operator TUI for agent/component configuration."""
from __future__ import annotations
import curses, os, subprocess

AGENTS = ["claude-code","cursor","opencode","crush","codex","aider","cline","roo-code","gemini-cli","github-copilot","windsurf","amazon-q","kiro"]
COMPONENTS = ["model-router-ai","resilience-ai","structured-output-ai","consensus-ai","evaluation-ai","observability-ai","security-ai","rag-ai","genetic-optimizer-ai"]


def run_menu(stdscr, title, items, multi=True):
    pos, selected = 0, set()
    while True:
        stdscr.erase(); h,w=stdscr.getmaxyx(); stdscr.addstr(1,2,"="*min(w-4,72)); stdscr.addstr(2,2,f" FlossWare AI | {title}",curses.A_BOLD); stdscr.addstr(3,2,"="*min(w-4,72))
        for i,item in enumerate(items[:max(1,h-7)]):
            mark = "[x]" if i in selected else "[ ]"
            attr=curses.A_REVERSE if i==pos else 0
            stdscr.addnstr(5+i,2,f"{mark} {item}",w-4,attr)
        stdscr.addnstr(h-2,2,"↑/↓ move  Space select  Enter confirm  a all  n none  q back",w-4)
        stdscr.refresh(); k=stdscr.getch()
        if k in (curses.KEY_UP,ord('k')): pos=max(0,pos-1)
        elif k in (curses.KEY_DOWN,ord('j')): pos=min(len(items)-1,pos+1)
        elif k==ord(' '):
            if multi: selected.symmetric_difference_update({pos})
            else: selected={pos}
        elif k==ord('a') and multi: selected=set(range(len(items)))
        elif k==ord('n') and multi: selected.clear()
        elif k in (10,13,curses.KEY_ENTER): return sorted(selected)
        elif k in (ord('q'),27): return None


def main():
    def app(stdscr):
        curses.curs_set(0); stdscr.keypad(True)
        while True:
            choice=run_menu(stdscr,"Control Plane",["Agents","Components","Accounts / Models","Doctor","Exit"],False)
            if choice is None or choice==[4]: return
            if choice==[0]:
                ids=run_menu(stdscr,"Coding Agents",AGENTS)
                if ids:
                    stdscr.erase(); stdscr.addstr(2,2,"Selected: "+", ".join(AGENTS[i] for i in ids)); stdscr.addstr(4,2,"Press any key..."); stdscr.refresh(); stdscr.getch()
            elif choice==[1]:
                ids=run_menu(stdscr,"Composable FlossWare AI Components",COMPONENTS)
                if ids:
                    stdscr.erase(); stdscr.addstr(2,2,"Selected: "+", ".join(COMPONENTS[i] for i in ids)); stdscr.addstr(4,2,"Use CLI for exact configuration: flossware-ai components <name>"); stdscr.addstr(6,2,"Press any key..."); stdscr.refresh(); stdscr.getch()
            elif choice==[2]:
                stdscr.erase(); stdscr.addstr(2,2,"Active profile: "+os.environ.get("FLOSSWARE_PROFILE","personal")); stdscr.addstr(4,2,"Use Accounts / Models from the CLI for live discovery."); stdscr.addstr(6,2,"flossware-ai accounts --verify"); stdscr.addstr(7,2,"flossware-ai models --available"); stdscr.addstr(9,2,"Press any key..."); stdscr.refresh(); stdscr.getch()
            elif choice==[3]:
                stdscr.erase(); stdscr.addstr(2,2,"Running FlossWare AI doctor..."); stdscr.refresh();
                root=os.environ.get("FLOSSWARE_AI_ROOT",os.path.expanduser("~/.flossware/ai")); p=subprocess.run([root+"/venv/bin/python",root+"/discovery.py","doctor"],capture_output=True,text=True); stdscr.addnstr(4,2,p.stdout or p.stderr, max(1,stdscr.getmaxyx()[1]-4)); stdscr.addstr(7,2,"Press any key..."); stdscr.refresh(); stdscr.getch()
    curses.wrapper(app)

if __name__ == "__main__": main()
