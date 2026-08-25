#!/usr/bin/env python3
"""Container-runtime discovery and selection for FlossWare AI.

This module deliberately does not install Podman/Docker. It only discovers
healthy local runtimes and persists a non-secret preference.
"""
from __future__ import annotations
import json, os, platform, shutil, subprocess
from pathlib import Path

ROOT = Path(os.environ.get("FLOSSWARE_AI_ROOT", Path.home()/".flossware"/"ai"))
STATE = ROOT / "state" / "container-runtime"
PREFERENCE = STATE / "selected"


def _run(cmd: list[str]) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=8, check=False)
        return p.returncode == 0, p.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return False, ""


def inspect(name: str) -> dict:
    executable = shutil.which(name)
    if not executable:
        return {"runtime": name, "installed": False, "reachable": False, "version": None}
    ok, output = _run([name, "version"] if name == "podman" else [name, "version", "--format", "{{.Server.Version}}"])
    if not ok and name == "docker":
        ok, output = _run([name, "version"])
    version = output.splitlines()[0] if output else None
    return {"runtime": name, "installed": True, "reachable": ok, "version": version}


def all_status() -> list[dict]:
    return [inspect("podman"), inspect("docker")]


def selected() -> str:
    try:
        value = PREFERENCE.read_text().strip()
        return value if value in {"auto", "podman", "docker", "native"} else "auto"
    except FileNotFoundError:
        return "auto"


def healthy_preference() -> str:
    statuses = {x["runtime"]: x for x in all_status()}
    if selected() == "native":
        return "native"
    if selected() in statuses and statuses[selected()]["reachable"]:
        return selected()
    if selected() in {"podman", "docker"}:
        return "native"
    # Podman is the preferred Linux backend. Outside Linux, use the first
    # reachable backend rather than asserting a platform-specific preference.
    if platform.system() == "Linux" and statuses["podman"]["reachable"]:
        return "podman"
    if statuses["docker"]["reachable"]:
        return "docker"
    if statuses["podman"]["reachable"]:
        return "podman"
    return "native"


def main(argv: list[str]) -> int:
    command = argv[0] if argv else "status"
    if command in {"list", "status"}:
        data = {"selected": selected(), "effective": healthy_preference(), "platform": platform.system(), "runtimes": all_status()}
        if command == "list":
            for x in data["runtimes"]:
                print(f"{x['runtime']:8} installed={str(x['installed']).lower():5} reachable={str(x['reachable']).lower():5} version={x['version'] or '-'}")
            print(f"selected={data['selected']} effective={data['effective']}")
        else:
            print(json.dumps(data, indent=2))
        return 0
    if command == "select":
        if len(argv) != 2 or argv[1] not in {"auto", "podman", "docker", "native"}:
            print("usage: runtime select auto|podman|docker|native", file=os.sys.stderr)
            return 2
        STATE.mkdir(parents=True, exist_ok=True)
        PREFERENCE.write_text(argv[1] + "\n")
        os.chmod(PREFERENCE, 0o600)
        print(f"Container runtime preference: {argv[1]}")
        return 0
    if command == "effective":
        print(healthy_preference())
        return 0
    print("usage: runtime list|status|select auto|podman|docker|native|effective", file=os.sys.stderr)
    return 2

if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
