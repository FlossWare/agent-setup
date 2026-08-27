#!/usr/bin/env bash
# Write non-secret installation provenance into managed state.
set -euo pipefail

INSTALL_ROOT="${1:?usage: write-install-metadata.sh INSTALL_ROOT RELEASE_REF SOURCE_MODE PLATFORM PROFILE}"
RELEASE_REF="${2:?missing release ref}"
SOURCE_MODE="${3:?missing source mode}"
PLATFORM="${4:?missing platform}"
PROFILE="${5:?missing profile}"

mkdir -p "$INSTALL_ROOT/state"
printf '{\n  "setup_release_ref": "%s",\n  "source_mode": "%s",\n  "platform": "%s",\n  "profile": "%s",\n  "credential_values_written": false\n}\n' "$RELEASE_REF" "$SOURCE_MODE" "$PLATFORM" "$PROFILE" > "$INSTALL_ROOT/state/install-metadata.json"
chmod 600 "$INSTALL_ROOT/state/install-metadata.json"
