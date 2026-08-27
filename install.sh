#!/usr/bin/env bash
# FlossWare AI bootstrap installer.
# Usage: curl -fsSL https://raw.githubusercontent.com/FlossWare/coding-agent-setup/main/install.sh | bash
set -euo pipefail

REF="${FLOSSWARE_RELEASE_REF:-main}"
BASE_URL="${FLOSSWARE_INSTALL_URL:-https://raw.githubusercontent.com/FlossWare/coding-agent-setup/${REF}}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# The historical installer at this known-good commit remains the recovery path
# while the full installer is repaired. It installs the requested REF archive,
# so the installed application still comes from the selected current revision.
RECOVERY_REF="e9a4b2692d66cc7c4f9285516ef5eaa1a174cc67"
curl -fsSL "https://raw.githubusercontent.com/FlossWare/coding-agent-setup/${RECOVERY_REF}/scripts/install.sh" -o "$TMP_DIR/install.sh"
# GitHub Contents-created helper scripts may not retain executable mode.
# The recovery installer is patched to invoke the helper through bash.
sed -i 's#"\$SETUP_DIR/scripts/write-install-metadata.sh"#bash "$SETUP_DIR/scripts/write-install-metadata.sh"#' "$TMP_DIR/install.sh"
chmod +x "$TMP_DIR/install.sh"
export FLOSSWARE_RELEASE_REF="$REF"
export FLOSSWARE_AI_REF="${FLOSSWARE_AI_REF:-main}"
exec "$TMP_DIR/install.sh" "$@"
