#!/usr/bin/env bash
# Canonical FlossWare AI bootstrap entry point.
#
# Consumer path (no clone required):
#   curl -fsSL https://raw.githubusercontent.com/FlossWare/agent-setup/main/install.sh | bash
#
# Local checkout path:
#   ./install.sh
#   ./install.sh --profile default
#
# This script does not implement install logic itself. It always delegates to
# scripts/install.sh (from the local tree or the selected release ref).
set -euo pipefail

REF="${FLOSSWARE_RELEASE_REF:-main}"
REPO="${FLOSSWARE_SETUP_REPO:-FlossWare/agent-setup}"

# When this file lives in a repository checkout, prefer the in-tree installer.
# BASH_SOURCE is empty under some `curl | bash` invocations; guard accordingly.
_SOURCE="${BASH_SOURCE[0]:-}"
if [[ -n "$_SOURCE" && "$_SOURCE" != "bash" && "$_SOURCE" != "-" ]]; then
  _HERE="$(cd "$(dirname "$_SOURCE")" && pwd)"
  if [[ -f "$_HERE/scripts/install.sh" ]]; then
    export FLOSSWARE_RELEASE_REF="$REF"
    export FLOSSWARE_AI_REF="${FLOSSWARE_AI_REF:-main}"
    exec bash "$_HERE/scripts/install.sh" "$@"
  fi
fi

# Remote bootstrap: fetch scripts/install.sh for the selected ref and exec it.
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
INSTALLER_URL="https://raw.githubusercontent.com/${REPO}/${REF}/scripts/install.sh"
if ! curl --proto "=https" --tlsv1.2 -fsSL "$INSTALLER_URL" -o "$TMP_DIR/install.sh"; then
  printf '[FlossWare] ERROR: failed to download installer from %s\n' "$INSTALLER_URL" >&2
  exit 1
fi
chmod +x "$TMP_DIR/install.sh"
export FLOSSWARE_RELEASE_REF="$REF"
export FLOSSWARE_AI_REF="${FLOSSWARE_AI_REF:-main}"
exec bash "$TMP_DIR/install.sh" "$@"
