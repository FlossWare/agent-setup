#!/usr/bin/env bash
# Cross-platform FlossWare AI installer. Artifact-first; Git is only used for explicit source fallback.
set -euo pipefail
AGENT="all"; PROFILE="default"; REPO_DIR=""; REINSTALL=false; CLEAN=false
INSTALL_ROOT="${FLOSSWARE_INSTALL_ROOT:-$HOME/.flossware/ai}"; VENV="$INSTALL_ROOT/venv"; SETUP_DIR="$INSTALL_ROOT/coding-agent-setup"
AI_REPO="https://github.com/FlossWare/coding-agent-ai.git"; SETUP_REPO="https://github.com/FlossWare/coding-agent-setup.git"; RELEASE_REF="${FLOSSWARE_RELEASE_REF:-main}"; AI_REF="${FLOSSWARE_AI_REF:-main}"; USE_SOURCE="${FLOSSWARE_USE_SOURCE:-false}"
if [[ "$RELEASE_REF" =~ ^[0-9a-f]{40}$ ]]; then SETUP_ARCHIVE="https://codeload.github.com/FlossWare/coding-agent-setup/tar.gz/$RELEASE_REF"; else SETUP_ARCHIVE="https://codeload.github.com/FlossWare/coding-agent-setup/tar.gz/refs/heads/$RELEASE_REF"; fi
usage(){ cat <<'EOF'
Usage: ./scripts/install.sh [options]
  --agent, -a AGENT   Agent integration to configure. Default: all
  --profile NAME      Profile name (default: default). Must have a profile definition.
  --repo, -r PATH     Optional Git project to configure
  --reinstall         Recreate only the managed FlossWare AI environment
  --clean             Remove the managed FlossWare AI environment
  --help, -h          Show this help

Supported platforms: Fedora/RHEL derivatives, Debian/Ubuntu, FreeBSD, Termux/Android.
The normal path downloads published/package artifacts and a GitHub source archive; it does not clone repositories.
Set FLOSSWARE_USE_SOURCE=true to explicitly use Git/source installation for development.
Credentials are never copied or persisted by this installer.
EOF
}
while [[ $# -gt 0 ]]; do case "$1" in
  --agent|-a) [[ $# -ge 2 ]] || { echo "ERROR: --agent requires a value" >&2; exit 2; }; AGENT="$2"; shift 2;;
  --profile) [[ $# -ge 2 ]] || { echo "ERROR: --profile requires a value" >&2; exit 2; }; PROFILE="$2"; shift 2;;
  --repo|-r) [[ $# -ge 2 ]] || { echo "ERROR: --repo requires a path" >&2; exit 2; }; REPO_DIR="$2"; shift 2;;
  --reinstall) REINSTALL=true; shift;; --clean) CLEAN=true; shift;; --help|-h) usage; exit 0;; *) echo "ERROR: unknown option: $1" >&2; usage >&2; exit 2;; esac; done
if [[ -z "$PROFILE" || "$PROFILE" == *"/"* || "$PROFILE" == *".."* ]]; then echo "ERROR: invalid profile name '$PROFILE'" >&2; exit 2; fi
case "$AGENT" in claude|claude-code|cursor|opencode|crush|codex|aider|cline|roo-code|gemini-cli|github-copilot|windsurf|amazon-q|kiro|all) ;; *) echo "ERROR: invalid agent '$AGENT'" >&2; exit 2;; esac
log(){ printf '\n[FlossWare] %s\n' "$*"; }; fail(){ printf '\n[FlossWare] ERROR: %s\n' "$*" >&2; exit 1; }
if [[ "$CLEAN" == true ]]; then rm -rf -- "$INSTALL_ROOT"; rm -f -- "$HOME/.local/bin/flossware-ai"; log "Clean complete. Native agent/provider credentials were not touched."; exit 0; fi
PLATFORM="unknown"
if [[ -n "${TERMUX_VERSION:-}" || "${PREFIX:-}" == /data/data/com.termux/* ]]; then PLATFORM="termux"
elif [[ "${OSTYPE:-}" == freebsd* ]]; then PLATFORM="freebsd"
elif [[ -r /etc/os-release ]]; then source /etc/os-release; case "${ID:-}" in fedora|rhel|rocky|almalinux|ol|centos|nobara) PLATFORM="fedora";; debian|ubuntu|linuxmint|pop) PLATFORM="debian";; esac; fi
[[ "$PLATFORM" != unknown ]] || fail "Unsupported platform. Supported platforms: Fedora/RHEL derivatives, Debian/Ubuntu, FreeBSD, and Termux/Android."
install_prereqs(){
  [[ -x "$VENV/bin/python" ]] && return 0
  case "$PLATFORM" in
    fedora) PM=(dnf); [[ $EUID -eq 0 ]] || PM=(sudo dnf); "${PM[@]}" install -y curl tar git python3 python3-devel python3-pip gcc gcc-c++ make pkgconf-pkg-config openssl-devel libffi-devel rust cargo ncurses-devel;;
    debian) PM=(apt-get); [[ $EUID -eq 0 ]] || PM=(sudo apt-get); "${PM[@]}" update; "${PM[@]}" install -y curl tar git python3 python3-venv python3-dev python3-pip build-essential pkg-config libssl-dev libffi-dev rustc cargo libncurses-dev;;
    freebsd) PM=(pkg); [[ $EUID -eq 0 ]] || { command -v doas >/dev/null 2>&1 && PM=(doas pkg) || PM=(sudo pkg); }; "${PM[@]}" install -y curl tar git python3 py311-pip gcc pkgconf openssl libffi rust;;
    termux) pkg update -y; pkg install -y curl tar git python python-pip clang make pkg-config openssl libffi rust;;
  esac
}
mkdir -p "$INSTALL_ROOT"
if [[ "$REINSTALL" == true ]]; then rm -rf -- "$VENV" "$SETUP_DIR" "$INSTALL_ROOT/bin"; fi
install_prereqs
python3 - <<'PY'
import sys
if sys.version_info < (3,11): raise SystemExit("Python 3.11+ required")
PY
[[ -d "$VENV" ]] || python3 -m venv "$VENV"
source "$VENV/bin/activate"
python -m pip install --upgrade pip setuptools wheel fastmcp
if [[ "$USE_SOURCE" == true ]]; then python -m pip install --upgrade "coding-agent-ai[all,tui] @ git+$AI_REPO@$AI_REF"; else python -m pip install --upgrade --prefer-binary "coding-agent-ai[all,tui]" || python -m pip install --upgrade "coding-agent-ai[all,tui] @ git+$AI_REPO@$AI_REF"; fi
if [[ "$USE_SOURCE" == true ]]; then
  if [[ -d "$SETUP_DIR/.git" ]]; then git -C "$SETUP_DIR" fetch --force --depth 1 origin "$RELEASE_REF"; git -C "$SETUP_DIR" checkout --force FETCH_HEAD; else rm -rf "$SETUP_DIR"; git clone --filter=blob:none "$SETUP_REPO" "$SETUP_DIR"; git -C "$SETUP_DIR" fetch --force --depth 1 origin "$RELEASE_REF"; git -C "$SETUP_DIR" checkout --force FETCH_HEAD; fi
else
  TMP_SETUP="$(mktemp -d)"; trap 'rm -rf "$TMP_SETUP"' EXIT; rm -rf "$SETUP_DIR"; curl -fsSL "$SETUP_ARCHIVE" -o "$TMP_SETUP/setup.tar.gz"; tar -xzf "$TMP_SETUP/setup.tar.gz" -C "$TMP_SETUP"; EXTRACTED="$(find "$TMP_SETUP" -mindepth 1 -maxdepth 1 -type d \( -name 'coding-agent-setup-*' -o -name 'agent-setup-*' \) -print -quit)"; [[ -n "$EXTRACTED" ]] || fail "failed to unpack coding-agent-setup artifact"; mv "$EXTRACTED" "$SETUP_DIR"
fi
for required in scripts/setup.py scripts/profile.sh scripts/write-install-metadata.sh flossware_setup/tui/app.py scripts/flossware-ai scripts/router_mcp.py scripts/discovery.py scripts/mcp.py scripts/tui.py scripts/agent_setup.py scripts/runtime.py scripts/dogfood.py; do [[ -f "$SETUP_DIR/$required" ]] || fail "missing $required"; done
[[ "$PROFILE" == "default" || -f "$SETUP_DIR/profiles/$PROFILE.toml" ]] || fail "profile '$PROFILE' is not defined; refusing to substitute the neutral default profile"
python -m compileall -q "$SETUP_DIR/scripts/setup.py" "$SETUP_DIR/scripts/tui.py" "$SETUP_DIR/scripts/agent_setup.py" "$SETUP_DIR/scripts/router_mcp.py" "$SETUP_DIR/scripts/discovery.py" "$SETUP_DIR/scripts/mcp.py" "$SETUP_DIR/scripts/runtime.py" "$SETUP_DIR/scripts/dogfood.py"
"$VENV/bin/python" -m pip install -e "$SETUP_DIR" --quiet || fail "failed to install coding-agent-setup package into managed venv"
PROFILE_DIR="$INSTALL_ROOT/config/profiles/$PROFILE"; mkdir -p "$PROFILE_DIR" "$INSTALL_ROOT/bin" "$INSTALL_ROOT/state" "$INSTALL_ROOT/cache" "$INSTALL_ROOT/mcp"
cp "$SETUP_DIR/scripts/profile.sh" "$PROFILE_DIR/profile.sh"; cp "$SETUP_DIR/profiles/$PROFILE.toml" "$PROFILE_DIR/profile.toml"
cp "$SETUP_DIR/scripts/flossware-ai" "$INSTALL_ROOT/bin/flossware-ai"; cp "$SETUP_DIR/scripts/tui.py" "$INSTALL_ROOT/tui.py"; cp "$SETUP_DIR/scripts/agent_setup.py" "$INSTALL_ROOT/agent_setup.py"; cp "$SETUP_DIR/scripts/setup.py" "$INSTALL_ROOT/setup.py"; cp "$SETUP_DIR/scripts/router_mcp.py" "$INSTALL_ROOT/router_mcp.py"; cp "$SETUP_DIR/scripts/discovery.py" "$INSTALL_ROOT/discovery.py"; cp "$SETUP_DIR/scripts/mcp.py" "$INSTALL_ROOT/mcp.py"; cp "$SETUP_DIR/scripts/runtime.py" "$INSTALL_ROOT/runtime.py"; cp "$SETUP_DIR/scripts/dogfood.py" "$INSTALL_ROOT/dogfood.py"
chmod 700 "$PROFILE_DIR/profile.sh" "$INSTALL_ROOT/bin/flossware-ai" "$INSTALL_ROOT"/*.py; printf '%s\n' "$PROFILE" > "$INSTALL_ROOT/state/active-profile"; chmod 600 "$INSTALL_ROOT/state/active-profile"
printf '{\n  "profile": "%s",\n  "credential_values_written": false,\n  "credential_source": "native-agent-store-or-environment"\n}\n' "$PROFILE" > "$PROFILE_DIR/profile.json"; chmod 600 "$PROFILE_DIR/profile.json"
PATH_SHIM="$HOME/.local/bin/flossware-ai"; mkdir -p "$(dirname "$PATH_SHIM")"; cat > "$PATH_SHIM" <<EOF
#!/usr/bin/env bash
exec "$INSTALL_ROOT/bin/flossware-ai" "\$@"
EOF
bash "$SETUP_DIR/scripts/write-install-metadata.sh" "$INSTALL_ROOT" "$RELEASE_REF" "$USE_SOURCE" "$PLATFORM" "$PROFILE"
chmod 700 "$PATH_SHIM"
log "Installation complete: $INSTALL_ROOT"; printf '%s\n' "Profile: $PROFILE" "Platform: $PLATFORM" "Source mode: $USE_SOURCE" "Run: flossware-ai tui" "Run: flossware-ai doctor" "Run: flossware-ai dogfood --strict"
