#!/usr/bin/env bash
# FlossWare provider-profile isolation. Policy only, never secrets.
set -euo pipefail
FLOSSWARE_PROFILE="${1:-personal}"
PROFILE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "$FLOSSWARE_PROFILE" in
  personal)
    export FLOSSWARE_PROFILE=personal
    export FLOSSWARE_PROFILE_POLICY="personal-all-configured"
    ;;
  redhat)
    export FLOSSWARE_PROFILE=redhat
    export FLOSSWARE_PROFILE_POLICY="redhat-anthropic-only"
    for var in OPENAI_API_KEY OPENROUTER_API_KEY GEMINI_API_KEY GROQ_API_KEY CEREBRAS_API_KEY COHERE_API_KEY HUGGINGFACE_API_KEY HF_TOKEN GOOGLE_API_KEY GOOGLE_APPLICATION_CREDENTIALS VERTEXAI_PROJECT VERTEXAI_LOCATION AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_PROFILE AWS_BEARER_TOKEN_BEDROCK AZURE_OPENAI_API_ENDPOINT AZURE_OPENAI_API_KEY AZURE_OPENAI_API_VERSION; do
      unset "$var"
    done
    ;;
  *)
    echo "ERROR: unsupported FlossWare profile: $FLOSSWARE_PROFILE" >&2
    echo "Supported profiles: personal, redhat" >&2
    return 2 2>/dev/null || exit 2
    ;;
esac
export FLOSSWARE_PROFILE_CONFIG="$PROFILE_ROOT/profile.toml"
