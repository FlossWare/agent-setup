"""Provision the shared FlossWare Crush integration environment."""
from __future__ import annotations

import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from flossware_setup.state_root import canonical_root

ROOT = canonical_root()
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "crush"
BIN_DIR = Path.home() / ".local" / "bin"
GATEWAY_URL = "https://raw.githubusercontent.com/FlossWare/crush-demo/main/gateway.py"
CODING_AGENT_REPO = "https://github.com/FlossWare/agent-ai.git"


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _write(path: Path, content: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(mode)


def _find_crush() -> str:
    found = shutil.which("crush") or str(Path.home() / "go" / "bin" / "crush")
    if Path(found).is_file() and os.access(found, os.X_OK):
        return found
    go = shutil.which("go")
    if not go:
        raise RuntimeError("Crush is not installed and Go is unavailable")
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["GOBIN"] = str(BIN_DIR)
    _run([go, "install", "github.com/charmbracelet/crush@latest"])
    installed = BIN_DIR / "crush"
    if not installed.is_file():
        raise RuntimeError("Crush installation failed")
    return str(installed)


def setup_crush(*, free_only: bool = True) -> int:
    """Set up Crush against the local FlossWare OpenAI-compatible gateway."""
    if os.name != "posix":
        raise RuntimeError("Crush setup currently requires a POSIX environment")
    python = shutil.which("python3") or shutil.which("python")
    if not python:
        raise RuntimeError("python3 is required")
    if not shutil.which("git"):
        raise RuntimeError("git is required")
    if not shutil.which("curl"):
        raise RuntimeError("curl is required")

    ROOT.mkdir(parents=True, exist_ok=True)
    venv = ROOT / "venv"
    if not (venv / "bin" / "python").is_file():
        _run([python, "-m", "venv", str(venv)])
    py = venv / "bin" / "python"
    _run([str(py), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    _run([str(py), "-m", "pip", "install", "--quiet", f"git+{CODING_AGENT_REPO}"])

    crush = _find_crush()
    gateway = ROOT / "crush-gateway.py"
    with urllib.request.urlopen(GATEWAY_URL, timeout=20) as response:
        gateway.write_bytes(response.read())
    gateway.chmod(0o755)
    _run([str(py), "-m", "py_compile", str(gateway)])

    envfile = ROOT / "provider-env.sh"
    if not envfile.exists():
        envfile.write_text("", encoding="utf-8")
        envfile.chmod(0o600)

    run_gateway = ROOT / "run-crush-gateway.sh"
    _write(run_gateway, f'''#!/usr/bin/env bash
set -euo pipefail
export FLOSSWARE_GATEWAY_HOST=127.0.0.1
export FLOSSWARE_GATEWAY_PORT=8765
if [[ -f "{envfile}" ]]; then
  set -a
  source "{envfile}"
  set +a
fi
exec "{py}" "{gateway}"
''', 0o700)

    service_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "systemd" / "user"
    service = service_dir / "flossware-crush-gateway.service"
    _write(service, f'''[Unit]
Description=FlossWare Personal Crush Gateway
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
ExecStart={run_gateway}
Restart=on-failure
RestartSec=2
[Install]
WantedBy=default.target
''')

    provider_lines = [
        "#!/usr/bin/env bash",
        "option metrics false",
        "option provider-auto-update false",
        "option default-providers false",
        "provider remove anthropic 2>/dev/null || true",
        "provider remove openai 2>/dev/null || true",
        "provider remove redhat 2>/dev/null || true",
        "provider remove ollama 2>/dev/null || true",
        "provider remove hyper 2>/dev/null || true",
        'provider add flossware --name "FlossWare Personal" --type openai-compat --base-url "http://127.0.0.1:8765/v1" --api-key "local" --discover-models false',
        'model add flossware/flossware --name "FlossWare (free/local)" --context-window 128000 --default-max-tokens 16384',
        "model large flossware/flossware",
        "model small flossware/flossware",
        'if [[ -n "${GH_PAT:-}" ]]; then',
        '  mcp add github --type http --url "https://api.githubcopilot.com/mcp/" --header Authorization "Bearer $GH_PAT"',
        'elif command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then',
        '  mcp add github --type http --url "https://api.githubcopilot.com/mcp/" --header Authorization "Bearer $(gh auth token)"',
        "fi",
        "permissions allow view ls grep edit bash",
    ]
    if not free_only:
        raise RuntimeError("Only --free-only is currently supported by the Crush setup")
    _write(CONFIG_DIR / "crushrc", "\n".join(provider_lines) + "\n")

    _write(BIN_DIR / "flossware-crush", f'''#!/usr/bin/env bash
exec env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY -u HYPER_API_KEY "{crush}" "$@"
''', 0o755)
    _write(BIN_DIR / "flossware-models", '''#!/usr/bin/env bash
set -euo pipefail
curl -fsS --max-time 5 http://127.0.0.1:8765/health >/dev/null || { echo 'FlossWare gateway is not running' >&2; exit 1; }
curl -fsS --max-time 5 http://127.0.0.1:8765/v1/models
''', 0o755)

    # The setup command owns gateway lifecycle. Enable and start the user service
    # so a fresh setup is immediately usable and subsequent logins restart it.
    systemctl = shutil.which("systemctl")
    if systemctl:
        _run([systemctl, "--user", "daemon-reload"])
        _run([systemctl, "--user", "enable", "--now", service.name])

    print("Crush setup complete")
    print(f"  Crush: {crush}")
    print(f"  Gateway: {gateway}")
    print(f"  Config: {CONFIG_DIR / 'crushrc'}")
    print("  Policy: free/local-only")
    print("  Gateway service: enabled and started")
    print("  Launch: flossware-crush")
    return 0
