#!/usr/bin/env bash
# Non-interactive installer for FlossWare AI coding-agent configs.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/FlossWare/coding-agent-setup/main/scripts/install.sh | bash
#   # or
#   ./scripts/install.sh [--agent claude|cursor|opencode|all] [--repo /path/to/project]
#
# What it does:
#   1. Installs core FlossWare AI libraries (model-router-ai, resilience-ai, structured-output-ai)
#   2. Copies integration templates for your chosen agent into your project
#   3. Verifies API keys are set

set -euo pipefail

AGENT="all"
REPO_DIR="."
SETUP_REPO="https://github.com/FlossWare/coding-agent-setup.git"
FLOSSWARE_BASE="https://github.com/FlossWare"

CORE_LIBS=(model-router-ai resilience-ai structured-output-ai)

while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent|-a) AGENT="$2"; shift 2 ;;
        --repo|-r)  REPO_DIR="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: install.sh [--agent claude|cursor|opencode|all] [--repo /path/to/project]"
            echo ""
            echo "Options:"
            echo "  --agent, -a   Agent to configure (claude, cursor, opencode, all). Default: all"
            echo "  --repo, -r    Project directory to install into. Default: current directory"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

REPO_DIR="$(cd "$REPO_DIR" && pwd)"

if [[ ! -d "$REPO_DIR/.git" ]]; then
    echo "ERROR: $REPO_DIR is not a git repository."
    exit 1
fi

echo "=== FlossWare AI — Coding Agent Setup ==="
echo "Agent:   $AGENT"
echo "Project: $REPO_DIR"
echo ""

# Step 1: Install core FlossWare AI libraries
echo "[1/3] Installing FlossWare AI libraries..."
PIP_CMD=""
if command -v pip &>/dev/null; then
    PIP_CMD="pip"
elif command -v pip3 &>/dev/null; then
    PIP_CMD="pip3"
else
    echo "ERROR: pip not found. Install Python 3.11+ first."
    exit 1
fi

for lib in "${CORE_LIBS[@]}"; do
    if ! $PIP_CMD install --quiet "git+${FLOSSWARE_BASE}/${lib}.git" 2>&1; then
        echo "WARNING: Failed to install $lib (continuing)"
    fi
done
echo "  Core libraries installed"

# Step 2: Copy integration templates
echo "[2/3] Setting up agent integration..."

SETUP_TMPDIR="$(mktemp -d)"
trap 'rm -rf "$SETUP_TMPDIR"' EXIT
git clone --depth 1 --quiet "$SETUP_REPO" "$SETUP_TMPDIR/setup" || {
    echo "ERROR: Could not clone $SETUP_REPO"
    exit 1
}

copy_no_clobber() {
    local src="$1" dst="$2"
    if [[ ! -e "$dst" ]]; then
        cp "$src" "$dst" && return 0
    fi
    return 1
}

copy_integration() {
    local agent="$1"
    local src="$SETUP_TMPDIR/setup/templates/$agent"

    if [[ ! -d "$src" ]]; then
        echo "  WARNING: No template found for '$agent'"
        return
    fi

    case "$agent" in
        claude-code)
            copy_no_clobber "$src/CLAUDE.md" "$REPO_DIR/CLAUDE.md" && echo "  Created CLAUDE.md" || echo "  CLAUDE.md already exists (skipped)"
            ;;
        cursor)
            copy_no_clobber "$src/.cursorrules" "$REPO_DIR/.cursorrules" && echo "  Created .cursorrules" || echo "  .cursorrules already exists (skipped)"
            ;;
        opencode)
            copy_no_clobber "$src/AGENTS.md" "$REPO_DIR/AGENTS.md" && echo "  Created AGENTS.md" || echo "  AGENTS.md already exists (skipped)"
            ;;
    esac
}

case "$AGENT" in
    claude)   copy_integration "claude-code" ;;
    cursor)   copy_integration "cursor" ;;
    opencode) copy_integration "opencode" ;;
    all)
        copy_integration "claude-code"
        copy_integration "cursor"
        copy_integration "opencode"
        ;;
    *)
        echo "ERROR: Unknown agent '$AGENT'. Use: claude, cursor, opencode, or all"
        exit 1
        ;;
esac

# Step 3: Check API keys
echo "[3/3] Checking API keys..."

FOUND=0
for var in COHERE_API_KEY OPENROUTER_API_KEY GEMINI_API_KEY GROQ_API_KEY CEREBRAS_API_KEY HUGGINGFACE_API_KEY; do
    if [[ -n "${!var:-}" ]]; then
        echo "  $var: set"
        FOUND=$((FOUND + 1))
    fi
done

if [[ $FOUND -eq 0 ]]; then
    echo ""
    echo "  WARNING: No API keys found. Set at least one:"
    echo "    export COHERE_API_KEY=your-key      # recommended"
    echo "    export OPENROUTER_API_KEY=your-key"
    echo "    export GEMINI_API_KEY=your-key"
    echo ""
    echo "  Get free keys at:"
    echo "    Cohere:      https://dashboard.cohere.com/api-keys"
    echo "    OpenRouter:   https://openrouter.ai/keys"
    echo "    Gemini:       https://aistudio.google.com/apikey"
else
    echo "  $FOUND API key(s) configured"
fi

echo ""
echo "=== Done! ==="
echo ""
echo "For the full interactive experience: python3 scripts/setup.py"
echo "Docs: https://github.com/FlossWare/coding-agent-setup"
