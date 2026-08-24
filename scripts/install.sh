#!/usr/bin/env bash
# Non-interactive installer for FlossWare AI coding-agent configs.
#
# Usage:
#   ./scripts/install.sh [--agent claude|cursor|opencode|all] [--repo /path/to/project]
#
# Review this script before running it. It installs pinned release artifacts when
# available, copies integration templates, and reports provider-key presence only.

set -euo pipefail

AGENT="all"
REPO_DIR="."
SETUP_REPO="https://github.com/FlossWare/coding-agent-setup.git"
FLOSSWARE_BASE="https://github.com/FlossWare"
CORE_LIBS=(model-router-ai resilience-ai structured-output-ai)
PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=11

usage() {
    cat <<'EOF'
Usage: install.sh [--agent claude|cursor|opencode|all] [--repo /path/to/project]

Options:
  --agent, -a   Agent to configure (claude, cursor, opencode, all). Default: all
  --repo, -r    Git project directory. Default: current directory
  --help, -h    Show this help

This installer never writes provider credentials to project files and only
reports whether supported credential variables are present.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent|-a)
            [[ $# -ge 2 ]] || { echo "ERROR: --agent requires a value" >&2; exit 2; }
            AGENT="$2"; shift 2 ;;
        --repo|-r)
            [[ $# -ge 2 ]] || { echo "ERROR: --repo requires a path" >&2; exit 2; }
            REPO_DIR="$2"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) echo "ERROR: Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

case "$AGENT" in
    claude|cursor|opencode|all) ;;
    *) echo "ERROR: Unknown agent '$AGENT'. Use: claude, cursor, opencode, or all" >&2; exit 2 ;;
esac

if [[ ! -d "$REPO_DIR" ]]; then
    echo "ERROR: project directory does not exist: $REPO_DIR" >&2
    exit 1
fi
REPO_DIR="$(cd "$REPO_DIR" && pwd)"
if [[ ! -d "$REPO_DIR/.git" ]]; then
    echo "ERROR: $REPO_DIR is not a git repository." >&2
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Install Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+ first." >&2
    exit 1
fi
PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "ERROR: Python $PYTHON_VERSION found; Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+ is required." >&2
    exit 1
fi

PIP_CMD=""
if python3 -m pip --version >/dev/null 2>&1; then
    PIP_CMD="python3 -m pip"
else
    echo "ERROR: pip is not available for Python $PYTHON_VERSION." >&2
    exit 1
fi

if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git is required." >&2
    exit 1
fi

# Keep the installer deterministic when a release/version is provided by the
# environment. Otherwise install from the repository's current default branch.
# CI should exercise a pinned RELEASE_REF rather than relying on moving HEAD.
RELEASE_REF="${FLOSSWARE_RELEASE_REF:-main}"

echo "=== FlossWare AI — Coding Agent Setup ==="
echo "Agent:   $AGENT"
echo "Project: $REPO_DIR"
echo "Python:  $PYTHON_VERSION"
echo "Ref:     $RELEASE_REF"
echo ""

echo "[1/3] Installing FlossWare AI libraries..."
FAILED=()
for lib in "${CORE_LIBS[@]}"; do
    if ! $PIP_CMD install --quiet "git+${FLOSSWARE_BASE}/${lib}.git@${RELEASE_REF}"; then
        FAILED+=("$lib")
    else
        echo "  $lib: installed"
    fi
done
if (( ${#FAILED[@]} > 0 )); then
    echo "ERROR: required libraries failed to install: ${FAILED[*]}" >&2
    echo "No successful installation is reported. Fix the failures and rerun." >&2
    exit 1
fi

echo "[2/3] Setting up agent integration..."
SETUP_TMPDIR="$(mktemp -d)"
trap 'rm -rf "$SETUP_TMPDIR"' EXIT
if ! git clone --depth 1 --branch "$RELEASE_REF" --quiet "$SETUP_REPO" "$SETUP_TMPDIR/setup"; then
    echo "ERROR: Could not clone $SETUP_REPO at ref '$RELEASE_REF'" >&2
    exit 1
fi

copy_no_clobber() {
    local src="$1" dst="$2"
    if [[ ! -e "$dst" ]]; then
        cp -- "$src" "$dst"
        return 0
    fi
    return 1
}

copy_integration() {
    local agent="$1"
    local src="$SETUP_TMPDIR/setup/templates/$agent"
    [[ -d "$src" ]] || { echo "ERROR: Missing template for '$agent'" >&2; return 1; }
    case "$agent" in
        claude-code)
            copy_no_clobber "$src/CLAUDE.md" "$REPO_DIR/CLAUDE.md" && echo "  Created CLAUDE.md" || echo "  CLAUDE.md already exists (skipped)" ;;
        cursor)
            copy_no_clobber "$src/.cursorrules" "$REPO_DIR/.cursorrules" && echo "  Created .cursorrules" || echo "  .cursorrules already exists (skipped)" ;;
        opencode)
            copy_no_clobber "$src/AGENTS.md" "$REPO_DIR/AGENTS.md" && echo "  Created AGENTS.md" || echo "  AGENTS.md already exists (skipped)" ;;
    esac
}

case "$AGENT" in
    claude) copy_integration claude-code ;;
    cursor) copy_integration cursor ;;
    opencode) copy_integration opencode ;;
    all)
        copy_integration claude-code
        copy_integration cursor
        copy_integration opencode
        ;;
esac

echo "[3/3] Checking API-key presence (values are never printed)..."
FOUND=0
for var in COHERE_API_KEY OPENROUTER_API_KEY GEMINI_API_KEY GROQ_API_KEY CEREBRAS_API_KEY HUGGINGFACE_API_KEY; do
    if [[ -n "${!var:-}" ]]; then
        echo "  $var: set"
        FOUND=$((FOUND + 1))
    else
        echo "  $var: not set"
    fi
done

echo ""
if [[ $FOUND -eq 0 ]]; then
    echo "No provider credentials are configured. This is allowed; configure credentials through your chosen secure provider/router mechanism."
else
    echo "$FOUND provider credential variable(s) detected. Values were not displayed or persisted."
fi

echo ""
echo "=== Done! ==="
echo "Full interactive experience: python3 scripts/setup.py"
echo "Docs: https://github.com/FlossWare/coding-agent-setup"
