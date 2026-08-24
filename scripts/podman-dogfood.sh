#!/usr/bin/env bash
# Build and run the Fedora Podman dogfood environment.
set -euo pipefail

IMAGE="${FLOSSWARE_IMAGE:-localhost/flossware-coding-agent:dogfood}"
REF="${FLOSSWARE_RELEASE_REF:-main}"
PROJECT="${FLOSSWARE_PROJECT_DIR:-$PWD}"

fail(){ printf '[FlossWare] ERROR: %s\n' "$*" >&2; exit 1; }
log(){ printf '\n[FlossWare] %s\n' "$*"; }

command -v podman >/dev/null 2>&1 || fail "Podman is required. Install it with: sudo dnf install -y podman"
[[ -f Containerfile ]] || fail "Run this script from the coding-agent-setup repository root."
[[ -d "$PROJECT/.git" ]] || fail "FLOSSWARE_PROJECT_DIR must point to a Git repository: $PROJECT"

PROJECT="$(cd "$PROJECT" && pwd)"

log "Building $IMAGE"
podman build \
  --build-arg FLOSSWARE_RELEASE_REF="$REF" \
  --build-arg CODING_AGENT_AI_REF="$REF" \
  -t "$IMAGE" \
  -f Containerfile .

log "Running offline image smoke test"
podman run --rm --entrypoint /opt/flossware/venv/bin/python "$IMAGE" \
  -m compileall -q /opt/flossware/coding-agent-setup/scripts/setup.py
podman run --rm --entrypoint /opt/flossware/venv/bin/pa "$IMAGE" --help >/dev/null

log "Running credential-boundary smoke test"
SENTINEL="FLOSSWARE_TEST_SECRET_DO_NOT_PERSIST_$(date +%s)"
OUTPUT="$(podman run --rm \
  -e "COHERE_API_KEY=$SENTINEL" \
  -e "OPENROUTER_API_KEY=$SENTINEL" \
  --entrypoint /opt/flossware/venv/bin/python "$IMAGE" \
  -c 'import os; print("credential-present=" + str(bool(os.environ.get("COHERE_API_KEY"))))')"
[[ "$OUTPUT" == "credential-present=True" ]] || fail "Credential injection smoke test failed"

log "Launching TUI in disposable Fedora container"
printf '%s\n' "No credentials are mounted by default." "Project: $PROJECT" "Image:   $IMAGE"
exec podman run --rm -it \
  --env-file <(env | grep -E '^(COHERE_API_KEY|OPENROUTER_API_KEY|GEMINI_API_KEY|GROQ_API_KEY|CEREBRAS_API_KEY|HUGGINGFACE_API_KEY)=' || true) \
  -v "$PROJECT:/workspace:Z" \
  -w /workspace \
  "$IMAGE"
