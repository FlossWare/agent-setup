#!/usr/bin/env bash
# FlossWare AI bootstrap installer.
# Usage: curl -fsSL https://raw.githubusercontent.com/FlossWare/coding-agent-setup/main/install.sh | bash
set -euo pipefail

BASE_URL="${FLOSSWARE_INSTALL_URL:-https://raw.githubusercontent.com/FlossWare/coding-agent-setup/main}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

curl -fsSL "$BASE_URL/scripts/install.sh" -o "$TMP_DIR/install.sh"
chmod +x "$TMP_DIR/install.sh"
exec "$TMP_DIR/install.sh" "$@"
