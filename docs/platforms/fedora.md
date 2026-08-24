# Fedora + Podman Installation and Dogfood Guide

Fedora Linux is the Tier-1 installation target for the current FlossWare coding-agent dogfood milestone. **Podman is the primary acceptance path.** Native installation remains available for development and debugging. Other operating systems are intentionally out of scope for this acceptance gate.

## Primary dogfood path: Podman

Install Podman on Fedora:

```bash
sudo dnf install -y podman git
```

Clone the setup repository:

```bash
git clone https://github.com/FlossWare/coding-agent-setup.git
cd coding-agent-setup
```

Run the complete containerized acceptance path:

```bash
bash scripts/podman-dogfood.sh
```

The runner:

1. Verifies Podman and the Git project.
2. Builds a Fedora container image from `Containerfile`.
3. Installs Python and native build dependencies inside the image.
4. Installs `coding-agent-ai[all,tui]` and its dependency graph.
5. Copies the current `coding-agent-setup` checkout into the image.
6. Compiles and smoke-checks the setup TUI and `pa` command.
7. Runs a credential-boundary smoke test with a sentinel value.
8. Starts the TUI interactively with the project mounted at `/workspace`.

The image contains **no credential values**. Credentials, when explicitly configured, are runtime environment inputs only.

### Reproducibility

Pin both repositories to a reviewed ref:

```bash
FLOSSWARE_RELEASE_REF=<reviewed-ref> bash scripts/podman-dogfood.sh
```

For an isolated image name:

```bash
FLOSSWARE_IMAGE=localhost/flossware-coding-agent:my-test bash scripts/podman-dogfood.sh
```

### Credential behavior

The runner does not require credentials for the installation or offline smoke tests.

If credentials are already exported in the Fedora shell, the runner passes only the supported provider variables into the disposable container. Values are never baked into the image or generated configuration.

Do not put keys in `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.flossware-ai.json`, `ai_config.py`, Git, or container build arguments.

## Container acceptance sequence

First prove the credential-free path:

```text
Fedora
  -> Podman
  -> Containerfile
  -> coding-agent-ai
  -> coding-agent-setup
  -> TUI
  -> generated configuration
```

Then, and only then, run an authenticated coding task:

```text
runtime credential
  -> Podman environment
  -> coding-agent-ai (`pa`)
  -> routing / policy
  -> provider-neutral contract
  -> cross-cutting decorators
  -> provider adapter
  -> model/runtime
```

Use a disposable Git worktree and begin with a small read-only task. Do not enable automatic commits until the first execution and test results have been reviewed.

## Native Fedora installation

Native installation remains available when debugging the container or developing the setup repository:

```bash
./scripts/install.sh
```

It installs Fedora prerequisites, creates `~/.flossware/venv`, installs `coding-agent-ai`, validates the TUI and `pa`, and installs `~/.local/bin/flossware-setup`.

Pin a reviewed ref when reproducibility matters:

```bash
FLOSSWARE_RELEASE_REF=<reviewed-ref> ./scripts/install.sh
```

## Architecture

```text
Fedora
  -> Podman
  -> FlossWare runtime image
  -> coding-agent-setup
  -> coding-agent-ai (`pa`)
  -> routing / policy
  -> provider-neutral contract
  -> cross-cutting decorators
  -> provider adapter
  -> model/runtime
```

Provider selection is a runtime/deployment policy decision. Cost is one possible routing attribute; it is not an architectural identity.

## Troubleshooting

### Podman is unavailable

```bash
sudo dnf install -y podman
podman --version
```

### Build fails

Run:

```bash
podman build --no-cache -t localhost/flossware-coding-agent:dogfood -f Containerfile .
```

Preserve the first failing package or Python traceback. Do not install random dependencies on the host to compensate for an image failure.

### TUI will not start

Verify the terminal is interactive. The runner uses `podman run --rm -it`. The TUI also has a built-in fallback palette and does not install a theme package during startup.

### Authentication fails

Installation success does not imply provider authentication. Configure an authorized provider/router capability separately. Do not paste credentials into project configuration or image build arguments.
