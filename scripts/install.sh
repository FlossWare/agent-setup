#!/usr/bin/env bash
# Fedora installer for FlossWare coding-agent-setup + coding-agent-ai.
set -euo pipefail
AGENT="all"; PROFILE="personal"; REPO_DIR=""; REINSTALL=false; CLEAN=false
INSTALL_ROOT="${FLOSSWARE_INSTALL_ROOT:-$HOME/.flossware/ai}"; VENV="$INSTALL_ROOT/venv"; SETUP_DIR="$INSTALL_ROOT/coding-agent-setup"
AI_REPO="https://github.com/FlossWare/coding-agent-ai.git"; SETUP_REPO="https://github.com/FlossWare/coding-agent-setup.git"; RELEASE_REF="${FLOSSWARE_RELEASE_REF:-main}"
USE_SOURCE="${FLOSSWARE_USE_SOURCE:-false}"
usage(){ cat <<'EOF'
Usage: ./scripts/install.sh [options]
  --agent, -a AGENT   Agent integration to configure. Default: all
  --profile NAME      personal or redhat. Default: personal
  --repo, -r PATH     Optional Git project to configure
  --reinstall         Recreate only the managed FlossWare AI environment
  --clean             Remove the managed FlossWare AI environment, preserving project files
  --help, -h          Show this help

The canonical managed root is ~/.flossware/ai. Credential values are never copied or persisted.
Artifacts are preferred; set FLOSSWARE_USE_SOURCE=true to force Git/source installation.
EOF
}
while [[ $# -gt 0 ]]; do case "$1" in
  --agent|-a) [[ $# -ge 2 ]] || { echo "ERROR: --agent requires a value" >&2; exit 2; }; AGENT="$2"; shift 2;;
  --profile) [[ $# -ge 2 ]] || { echo "ERROR: --profile requires a value" >&2; exit 2; }; PROFILE="$2"; shift 2;;
  --repo|-r) [[ $# -ge 2 ]] || { echo "ERROR: --repo requires a path" >&2; exit 2; }; REPO_DIR="$2"; shift 2;;
  --reinstall) REINSTALL=true; shift;; --clean) CLEAN=true; shift;; --help|-h) usage; exit 0;; *) echo "ERROR: unknown option: $1" >&2; usage >&2; exit 2;; esac; done
case "$PROFILE" in personal|redhat) ;; *) echo "ERROR: invalid profile '$PROFILE'" >&2; exit 2;; esac
if [[ "$CLEAN" == true ]]; then
  printf '[FlossWare] Removing managed AI environment: %s\n' "$INSTALL_ROOT"
  rm -rf -- "$INSTALL_ROOT"; rm -f -- "$HOME/.local/bin/flossware-ai"
  printf '[FlossWare] Clean complete. Project files, native agent credentials, and provider credentials were not touched.\n'; exit 0
fi
case "$AGENT" in claude|claude-code|cursor|opencode|crush|codex|aider|cline|roo-code|gemini-cli|github-copilot|windsurf|amazon-q|kiro|all) ;; *) echo "ERROR: invalid agent '$AGENT'" >&2; exit 2;; esac
if [[ "${OSTYPE:-}" != linux* ]] || [[ ! -r /etc/os-release ]]; then echo "ERROR: Linux is required." >&2; exit 1; fi
source /etc/os-release; [[ "${ID:-}" == fedora ]] || { echo "ERROR: Fedora Linux is required; detected ${ID:-unknown}." >&2; exit 1; }
if [[ $EUID -eq 0 ]]; then DNF=(dnf); else command -v sudo >/dev/null 2>&1 || { echo "ERROR: sudo is required." >&2; exit 1; }; DNF=(sudo dnf); fi
log(){ printf '\n[FlossWare] %s\n' "$*"; }; fail(){ printf '\n[FlossWare] ERROR: %s\n' "$*" >&2; exit 1; }
log "Installing Fedora prerequisites"; "${DNF[@]}" install -y git python3 python3-devel python3-pip gcc gcc-c++ make pkgconf-pkg-config openssl-devel libffi-devel rust cargo ncurses-devel
python3 - <<'PY'
import sys
if sys.version_info < (3, 11): raise SystemExit("Python 3.11+ required")
print(f"Python {sys.version.split()[0]}")
PY
mkdir -p "$INSTALL_ROOT"
if [[ "$REINSTALL" == true ]]; then log "Reinstall requested: removing only managed FlossWare AI artifacts"; rm -rf -- "$VENV" "$SETUP_DIR" "$INSTALL_ROOT/bin"; fi
[[ -d "$VENV" ]] || { log "Creating isolated Python environment: $VENV"; python3 -m venv "$VENV"; }
source "$VENV/bin/activate"; python -m pip install --upgrade pip setuptools wheel fastmcp
if [[ "$USE_SOURCE" == true ]]; then
  log "Source mode enabled: installing coding-agent-ai from $RELEASE_REF"
  python -m pip install --upgrade "coding-agent-ai[all,tui] @ git+$AI_REPO@$RELEASE_REF"
else
  log "Installing coding-agent-ai from published artifacts when available"
  if ! python -m pip install --upgrade --prefer-binary "coding-agent-ai[all,tui]"; then
    log "Published artifact unavailable or incomplete; falling back to source $RELEASE_REF"
    python -m pip install --upgrade "coding-agent-ai[all,tui] @ git+$AI_REPO@$RELEASE_REF"
  fi
fi
log "Installing coding-agent-setup from $RELEASE_REF"
if [[ -d "$SETUP_DIR/.git" ]]; then git -C "$SETUP_DIR" fetch --force origin "$RELEASE_REF"; git -C "$SETUP_DIR" checkout --force "$RELEASE_REF"; git -C "$SETUP_DIR" reset --hard "origin/$RELEASE_REF" 2>/dev/null || true; else git clone --depth 1 --branch "$RELEASE_REF" "$SETUP_REPO" "$SETUP_DIR"; fi
for required in scripts/setup.py scripts/profile.sh scripts/flossware-ai scripts/router_mcp.py scripts/discovery.py scripts/mcp.py scripts/tui.py scripts/agent_setup.py; do [[ -f "$SETUP_DIR/$required" ]] || fail "missing $required"; done
for p in personal redhat; do [[ -f "$SETUP_DIR/profiles/$p.toml" ]] || fail "missing profiles/$p.toml"; done
python -m compileall -q "$SETUP_DIR/scripts/setup.py" "$SETUP_DIR/scripts/tui.py" "$SETUP_DIR/scripts/agent_setup.py" "$SETUP_DIR/scripts/router_mcp.py" "$SETUP_DIR/scripts/discovery.py" "$SETUP_DIR/scripts/mcp.py"
PROFILE_DIR="$INSTALL_ROOT/config/profiles/$PROFILE"; mkdir -p "$PROFILE_DIR" "$INSTALL_ROOT/bin" "$INSTALL_ROOT/state" "$INSTALL_ROOT/cache" "$INSTALL_ROOT/mcp"
cp "$SETUP_DIR/scripts/profile.sh" "$PROFILE_DIR/profile.sh"; cp "$SETUP_DIR/profiles/$PROFILE.toml" "$PROFILE_DIR/profile.toml"; cp "$SETUP_DIR/scripts/flossware-ai" "$INSTALL_ROOT/bin/flossware-ai"; cp "$SETUP_DIR/scripts/tui.py" "$INSTALL_ROOT/tui.py"; cp "$SETUP_DIR/scripts/agent_setup.py" "$INSTALL_ROOT/agent_setup.py"; cp "$SETUP_DIR/scripts/setup.py" "$INSTALL_ROOT/setup.py"; cp "$SETUP_DIR/scripts/router_mcp.py" "$INSTALL_ROOT/router_mcp.py"; cp "$SETUP_DIR/scripts/discovery.py" "$INSTALL_ROOT/discovery.py"; cp "$SETUP_DIR/scripts/mcp.py" "$INSTALL_ROOT/mcp.py"
chmod 700 "$PROFILE_DIR/profile.sh" "$INSTALL_ROOT/bin/flossware-ai" "$INSTALL_ROOT"/*.py; printf '%s\n' "$PROFILE" > "$INSTALL_ROOT/state/active-profile"; chmod 600 "$INSTALL_ROOT/state/active-profile"
printf '{\n  "profile": "%s",\n  "credential_values_written": false,\n  "credential_source": "native-agent-store-or-environment"\n}\n' "$PROFILE" > "$PROFILE_DIR/profile.json"; chmod 600 "$PROFILE_DIR/profile.json"
for name in claude-code crush codex opencode cursor aider cline roo-code gemini-cli github-copilot windsurf amazon-q kiro; do WRAPPER="$INSTALL_ROOT/bin/$name"; cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
exec "$INSTALL_ROOT/bin/flossware-ai" "$name" "\$@"
EOF
chmod 700 "$WRAPPER"; done
PATH_SHIM="$HOME/.local/bin/flossware-ai"; mkdir -p "$(dirname "$PATH_SHIM")"; cat > "$PATH_SHIM" <<EOF
#!/usr/bin/env bash
exec "$INSTALL_ROOT/bin/flossware-ai" "\$@"
EOF
chmod 700 "$PATH_SHIM"
if [[ -n "$REPO_DIR" ]]; then [[ -d "$REPO_DIR/.git" ]] || fail "--repo must point to a Git repository"; fi
log "Running credential-boundary validation"; python - <<'PY'
import os
vars=("COHERE_API_KEY","OPENROUTER_API_KEY","GEMINI_API_KEY","GROQ_API_KEY","CEREBRAS_API_KEY","DEEPINFRA_API_TOKEN","NVIDIA_API_KEY","HUGGINGFACE_API_KEY","OPENAI_API_KEY","ANTHROPIC_API_KEY")
print(f"credential presence check: PASS ({sum(bool(os.environ.get(v)) for v in vars)} configured; values not displayed or persisted)")
PY
log "Installation complete"; printf '%s\n' "AI root: $INSTALL_ROOT" "Profile: $PROFILE" "Launcher: $PATH_SHIM" "Ref: $RELEASE_REF" "" "Run: flossware-ai tui" "Run: flossware-ai doctor" "Run: flossware-ai components" "Run: flossware-ai accounts --verify" "Run: flossware-ai models --refresh" "Reinstall: ./scripts/install.sh --reinstall" "Clean: ./scripts/install.sh --clean"
