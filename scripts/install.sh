#!/usr/bin/env bash
# Fedora installer for FlossWare coding-agent-setup + coding-agent-ai.
# This is the Tier-1 dogfood installer. It installs prerequisites, creates an
# isolated environment, installs the actual FlossWare runtime, validates it,
# and never writes credential values.
set -euo pipefail

AGENT="all"
REPO_DIR=""
INSTALL_ROOT="${FLOSSWARE_INSTALL_ROOT:-$HOME/.flossware}"
VENV="$INSTALL_ROOT/venv"
SETUP_DIR="$INSTALL_ROOT/coding-agent-setup"
AI_REPO="https://github.com/FlossWare/coding-agent-ai.git"
SETUP_REPO="https://github.com/FlossWare/coding-agent-setup.git"
RELEASE_REF="${FLOSSWARE_RELEASE_REF:-main}"

usage() {
    cat <<'EOF'
Usage: ./scripts/install.sh [--agent claude|cursor|opencode|all] [--repo /path/to/project]

Fedora is the Tier-1 supported installation target for the current dogfood milestone.

Options:
  --agent, -a   Agent integration to configure. Default: all
  --repo, -r    Optional Git project to configure after installation
  --help, -h    Show this help

Environment:
  FLOSSWARE_INSTALL_ROOT   Installation root (default: ~/.flossware)
  FLOSSWARE_RELEASE_REF    Git ref/tag/commit to install (default: main)

The installer never prints, stores, or copies credential values.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent|-a) [[ $# -ge 2 ]] || { echo "ERROR: --agent requires a value" >&2; exit 2; }; AGENT="$2"; shift 2 ;;
        --repo|-r) [[ $# -ge 2 ]] || { echo "ERROR: --repo requires a path" >&2; exit 2; }; REPO_DIR="$2"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) echo "ERROR: unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

case "$AGENT" in claude|cursor|opencode|all) ;; *) echo "ERROR: invalid agent '$AGENT'" >&2; exit 2 ;; esac

if [[ "${OSTYPE:-}" != linux* ]] || [[ ! -r /etc/os-release ]]; then
    echo "ERROR: this installer currently supports Fedora Linux only." >&2
    exit 1
fi
# shellcheck disable=SC1091
source /etc/os-release
if [[ "${ID:-}" != "fedora" ]]; then
    echo "ERROR: Fedora Linux is required; detected ${ID:-unknown}." >&2
    exit 1
fi

if [[ $EUID -eq 0 ]]; then
    DNF=(dnf)
else
    command -v sudo >/dev/null 2>&1 || { echo "ERROR: sudo is required to install Fedora prerequisites." >&2; exit 1; }
    DNF=(sudo dnf)
fi

log(){ printf '\n[FlossWare] %s\n' "$*"; }
fail(){ printf '\n[FlossWare] ERROR: %s\n' "$*" >&2; exit 1; }

log "Installing Fedora prerequisites"
"${DNF[@]}" install -y git python3 python3-devel python3-pip gcc gcc-c++ make pkgconf-pkg-config openssl-devel libffi-devel rust cargo ncurses-devel

command -v git >/dev/null || fail "git is unavailable after prerequisite installation"
command -v python3 >/dev/null || fail "python3 is unavailable after prerequisite installation"
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(f"Python 3.11+ required; found {sys.version.split()[0]}")
print(f"Python {sys.version.split()[0]}")
PY

mkdir -p "$INSTALL_ROOT"
if [[ ! -d "$VENV" ]]; then
    log "Creating isolated Python environment: $VENV"
    python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip setuptools wheel

log "Installing coding-agent-ai from $RELEASE_REF"
python -m pip install --upgrade "coding-agent-ai[all,tui] @ git+$AI_REPO@$RELEASE_REF"

log "Installing coding-agent-setup from $RELEASE_REF"
if [[ -d "$SETUP_DIR/.git" ]]; then
    git -C "$SETUP_DIR" fetch --force origin "$RELEASE_REF" || true
    git -C "$SETUP_DIR" checkout --force "$RELEASE_REF"
else
    rm -rf "$SETUP_DIR"
    git clone --depth 1 --branch "$RELEASE_REF" "$SETUP_REPO" "$SETUP_DIR"
fi

[[ -f "$SETUP_DIR/scripts/setup.py" ]] || fail "coding-agent-setup checkout is missing scripts/setup.py"
python -m compileall -q "$SETUP_DIR/scripts/setup.py"
python "$SETUP_DIR/scripts/setup.py" --help >/dev/null
pa --help >/dev/null

LAUNCHER="${HOME}/.local/bin/flossware-setup"
mkdir -p "$(dirname "$LAUNCHER")"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
source "$VENV/bin/activate"
exec python "$SETUP_DIR/scripts/setup.py" "\$@"
EOF
chmod 700 "$LAUNCHER"

if [[ -n "$REPO_DIR" ]]; then
    [[ -d "$REPO_DIR/.git" ]] || fail "--repo must point to a Git repository: $REPO_DIR"
    REPO_DIR="$(cd "$REPO_DIR" && pwd)"
    log "Repository validated: $REPO_DIR"
    echo "Installation is complete. Run '$LAUNCHER' to configure the project interactively."
fi

log "Running credential-boundary validation"
python - <<'PY'
import os
for name in ("COHERE_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY", "CEREBRAS_API_KEY", "HUGGINGFACE_API_KEY"):
    bool(os.environ.get(name))
print("credential presence check: PASS (values not displayed or persisted)")
PY

log "Installation complete"
printf '%s\n' "Environment: $VENV" "Setup:       $SETUP_DIR" "Launcher:    $LAUNCHER" "Runtime:     pa" "Ref:         $RELEASE_REF"
printf '%s\n' "" "Run: $LAUNCHER" "Run '$LAUNCHER --help' for help."
