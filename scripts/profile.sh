#!/usr/bin/env bash
# FlossWare provider-profile isolation. Policy only, never secrets.
# The public repository ships only the neutral "default" profile.
# User-defined local profiles are allowed without hard-coded Personal/Red Hat rules.
set -euo pipefail
FLOSSWARE_PROFILE="${1:-default}"
PROFILE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export FLOSSWARE_PROFILE
export FLOSSWARE_PROFILE_CONFIG="$PROFILE_ROOT/profile.toml"
case "$FLOSSWARE_PROFILE" in
  default)
    export FLOSSWARE_PROFILE_POLICY="default-neutral"
    ;;
  *)
    # Local/user-defined profile: load toml if present; no secret mutation in public code.
    export FLOSSWARE_PROFILE_POLICY="user-defined"
    ;;
esac
