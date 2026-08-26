#!/usr/bin/env bash
# FlossWare AI bootstrap installer.
# Usage: curl -fsSL https://raw.githubusercontent.com/FlossWare/coding-agent-setup/main/install.sh | bash
set -euo pipefail

REF="${FLOSSWARE_RELEASE_REF:-main}"
BASE_URL="${FLOSSWARE_INSTALL_URL:-https://raw.githubusercontent.com/FlossWare/coding-agent-setup/${REF}}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

curl -fsSL "$BASE_URL/scripts/install.sh" -o "$TMP_DIR/install.sh"
chmod +x "$TMP_DIR/install.sh"
# Propagate ref so scripts/install.sh uses the same setup archive/branch.
export FLOSSWARE_RELEASE_REF="$REF"
export FLOSSWARE_AI_REF="${FLOSSWARE_AI_REF:-main}"
exec "$TMP_DIR/install.sh" "$@"
