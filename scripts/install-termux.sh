#!/data/data/com.termux/files/usr/bin/bash
# FlossWare Coding Agent Setup - Termux bootstrap
# Installs prerequisites and creates an isolated Python environment.
# Does NOT request, print, store, or transmit provider credentials.
set -euo pipefail

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
INSTALL_ROOT="${FLOSSWARE_INSTALL_ROOT:-$HOME/.flossware}"
VENV="$INSTALL_ROOT/venv"
SETUP_REPO="https://github.com/FlossWare/agent-setup.git"
SETUP_DIR="$INSTALL_ROOT/agent-setup"
REF="${FLOSSWARE_RELEASE_REF:-main}"

log(){ printf '\n[FlossWare] %s\n' "$*"; }
fail(){ printf '\n[FlossWare] ERROR: %s\n' "$*" >&2; exit 1; }

[[ -d "$PREFIX" ]] || fail "This script is for Termux. PREFIX=$PREFIX was not found."
command -v pkg >/dev/null 2>&1 || fail "Termux pkg was not found."

log "Updating Termux packages"
pkg update -y
pkg upgrade -y

log "Installing required packages"
pkg install -y git python clang make pkg-config libffi openssl rust

command -v python >/dev/null 2>&1 || fail "Python installation failed."
command -v git >/dev/null 2>&1 || fail "Git installation failed."

PYTHON_OK=0
python - <<'PY' || exit 1
import sys
if sys.version_info < (3, 11):
    raise SystemExit(f"Python 3.11+ required; found {sys.version.split()[0]}")
print(f"Python {sys.version.split()[0]}")
PY
PYTHON_OK=1

log "Creating isolated FlossWare environment at $VENV"
mkdir -p "$INSTALL_ROOT"
if [[ ! -d "$VENV" ]]; then
    python -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip setuptools wheel

log "Installing agent-setup from $REF"
if [[ -d "$SETUP_DIR/.git" ]]; then
    git -C "$SETUP_DIR" fetch --tags --force origin
    git -C "$SETUP_DIR" checkout --force "$REF"
    git -C "$SETUP_DIR" reset --hard "origin/$REF" 2>/dev/null || true
else
    git clone --depth 1 --branch "$REF" "$SETUP_REPO" "$SETUP_DIR"
fi

# Verify the repository contains the expected entry point before continuing.
[[ -f "$SETUP_DIR/scripts/setup.py" ]] || fail "agent-setup checkout is missing scripts/setup.py"

log "Installing runtime dependencies"
if [[ -f "$SETUP_DIR/requirements.txt" ]]; then
    python -m pip install -r "$SETUP_DIR/requirements.txt"
fi

log "Installing FlossWare core AI libraries"
for lib in model-router-ai resilience-ai structured-output-ai; do
    python -m pip install "git+https://github.com/FlossWare/$lib.git@$REF"
done

log "Installing Termux launcher"
BIN="$PREFIX/bin/flossware-setup"
cat > "$BIN" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
source "$VENV/bin/activate"
exec python "$SETUP_DIR/scripts/setup.py" "\$@"
EOF
chmod 700 "$BIN"

log "Installation complete"
printf '%s\n' "Environment: $VENV" "Setup:       $SETUP_DIR" "Launcher:    $BIN" "Ref:         $REF"
printf '%s\n' "" "Launch with: flossware-setup" "Help:         flossware-setup --help"
printf '%s\n' "" "Credentials are not collected or stored by this installer. Configure them through your chosen secure mechanism."
