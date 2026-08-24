# Fedora Installation and Dogfood Guide

Fedora Linux is the Tier-1 installation target for the current FlossWare coding-agent dogfood milestone. Other operating systems are intentionally out of scope for this acceptance gate.

## One-command installation

From a checkout of `coding-agent-setup`:

```bash
./scripts/install.sh
```

The installer:

1. Verifies Fedora Linux.
2. Installs the required Fedora build/runtime packages.
3. Creates an isolated Python environment under `~/.flossware/venv`.
4. Installs `coding-agent-ai` and its optional FlossWare capabilities.
5. Checks out `coding-agent-setup` at the selected ref.
6. Compiles and smoke-checks the setup TUI and `pa` command.
7. Installs `~/.local/bin/flossware-setup`.
8. Performs a credential-presence check without displaying values.

## Reproducible installation

Use a reviewed tag or commit when reproducibility matters:

```bash
FLOSSWARE_RELEASE_REF=<reviewed-ref> ./scripts/install.sh
```

Override the installation root if required:

```bash
FLOSSWARE_INSTALL_ROOT=/opt/flossware ./scripts/install.sh
```

The installation root must be writable by the invoking user. Use a user-owned location for normal development.

## Launch the TUI

```bash
~/.local/bin/flossware-setup
```

If `~/.local/bin` is on `PATH`, simply:

```bash
flossware-setup
```

The TUI is provider- and pricing-neutral. Credentials are optional. Budget is an explicit policy input.

## Configure a project

The project must be a Git repository because generated agent configuration is intended to be version-controlled and reviewable.

```bash
cd ~/src/my-project
git status
flossware-setup
```

Select the agent integration, capabilities, budget policy, and project directory. Existing provider credentials are reported only as present/not present. Values are never displayed or written to generated artifacts.

## Runtime smoke test

After installation:

```bash
source ~/.flossware/venv/bin/activate
pa --help
python -m compileall ~/.flossware/coding-agent-setup
```

For a real dogfood run, use a disposable branch or worktree and a deliberately small coding task first:

```bash
pa "Inspect this repository and identify one small correctness improvement. Do not make changes." --repo . --investigate
```

Then perform a controlled change with explicit test commands:

```bash
pa "Fix the identified issue and run the existing tests." --repo . --commands pytest --max-iter 3
```

Do not use `--commit` for the first run. Review the diff and test results before allowing an automatic commit.

## Architecture

```text
Fedora
  -> coding-agent-setup
  -> generated agent integration
  -> coding-agent-ai (`pa`)
  -> routing / policy
  -> provider-neutral contract
  -> cross-cutting decorators
  -> provider adapter
  -> model/runtime
```

Provider selection is a runtime/deployment policy decision. Cost is one possible routing attribute; it is not an architectural identity.

## Credential safety

Never put credential values in source or generated agent files. The setup layer may detect environment-variable presence, but must not print or persist the value.

Use the provider's supported authentication mechanism, an existing authenticated CLI session where available, environment variables, or an appropriate OS/CI secret store.

## Troubleshooting

### `sudo` is unavailable

Install and configure `sudo`, or run the installer as root. Normal development should use a regular user and a user-owned `~/.flossware` installation.

### Python is too old

The current runtime requires Python 3.11 or newer. Update Fedora and install the current `python3` package.

### Native dependency compilation fails

The installer includes GCC, development headers, OpenSSL/libffi development packages, Rust/Cargo, and the Python development package. Rerun the installer after resolving any repository/package-manager failure.

### TUI will not start

Verify terminal capabilities:

```bash
echo "$TERM"
tput colors
```

The TUI has a built-in fallback palette and does not install a theme package during startup.

### `pa` cannot authenticate

Installation success does not imply provider authentication. Configure an authorized provider/router capability separately. Do not paste credentials into project configuration.
