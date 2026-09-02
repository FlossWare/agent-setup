# Termux Installation and Dogfood Guide

This is the supported bootstrap path for running FlossWare coding-agent tooling directly in Termux on Android.

## 1. Prerequisites

Install the current Termux from a trusted distribution source, then open Termux and run:

```bash
pkg update -y
pkg upgrade -y
pkg install -y git python clang make pkg-config libffi openssl rust
```

Verify:

```bash
python --version
git --version
```

Python 3.11 or newer is required by the current setup path.

## 2. Install agent-setup

The repository includes a dedicated Termux bootstrapper:

```bash
git clone https://github.com/FlossWare/agent-setup.git
cd agent-setup
bash scripts/install-termux.sh
```

The installer creates an isolated environment under `~/.flossware/venv`, checks out the requested release ref, installs the required FlossWare libraries, and installs the `flossware-setup` launcher into Termux's `$PREFIX/bin`.

For reproducibility, pin a release/tag or commit instead of using the moving default branch:

```bash
FLOSSWARE_RELEASE_REF=<reviewed-release> bash scripts/install-termux.sh
```

## 3. Launch the TUI

```bash
flossware-setup
```

The TUI is provider-neutral. Do not select a provider because it is free or paid. Select capabilities and policy. Provider/model selection belongs to the routing layer.

If the terminal is too small, resize the terminal and relaunch. A graphical desktop is not required.

## 4. Credentials

The installer does **not** collect or persist API keys.

Do not paste credentials into:

- `CLAUDE.md`
- `AGENTS.md`
- `.cursorrules`
- `.flossware-ai.json`
- `ai_config.py`
- shell history
- Git repositories
- logs

Use the provider's supported CLI authentication, Android/Termux secret mechanism, environment variables, or another secure credential store appropriate to your environment.

The setup layer should consume an already-authorized capability where the provider/CLI exposes one. It should not require duplicate signups merely to configure the project.

## 5. Smoke test

Before real dogfooding, generate configuration into a disposable Git repository:

```bash
mkdir -p ~/flossware-smoke
cd ~/flossware-smoke
git init
flossware-setup
```

Choose the agents and capabilities needed for the test. After generation:

```bash
find . -maxdepth 2 -type f -print
python -m compileall .
```

Inspect generated configuration and verify that it contains provider names/environment-variable identifiers only, never credential values.

A useful secret-value check is to inspect the generated files manually rather than piping the entire shell environment into a log. Never run `env` into a committed file.

## 6. Runtime dogfood

The setup repository prepares the project. The runtime/orchestration layer is `FlossWare/agent-ai`.

The intended architecture is:

```text
Termux
  -> agent-setup
  -> generated agent configuration
  -> agent-ai
  -> policy / model router
  -> provider-neutral contract
  -> decorators
  -> provider adapter
  -> model/runtime
```

Decorators may provide resilience, security, observability, evaluation, structured-output validation, token/cost accounting, and other cross-cutting behavior. They must not encode a provider or pricing preference.

## 7. Troubleshooting

### `python` is missing

```bash
pkg install -y python
```

### Native Python dependency fails to build

Install the build toolchain:

```bash
pkg install -y clang make pkg-config libffi openssl rust
```

Then rerun the installer.

### Terminal colors or theme look wrong

The TUI has a built-in fallback palette. Optional FlossWare theme support can be installed separately. The setup process must not silently install a remote theme package merely to start the UI.

### Git checkout fails

Check connectivity and, for a moving branch, rerun without `FLOSSWARE_RELEASE_REF`. For production dogfood, use a reviewed tag/commit.

## 8. Security rule

A successful installation means the tooling is installed. It does **not** mean credentials are configured. Authentication and authorization remain explicit capabilities and must be kept outside generated source/configuration artifacts.
