# Interactive TUI Setup Guide

The `scripts/setup.py` builder configures AI coding agents with FlossWare libraries. It is provider-neutral and pricing-neutral. Provider/model selection is a runtime policy decision.

For the current dogfood milestone, **Fedora Linux is the Tier-1 installation target**. Start with `./scripts/install.sh` on Fedora, then launch the TUI through `~/.local/bin/flossware-setup`.

## Requirements

- Fedora Linux
- Python 3.11+
- Git
- A terminal that supports curses
- Optional: `curses-themes` for additional themes. The TUI has a built-in fallback palette and never installs a theme package during startup.

## Install

```bash
./scripts/install.sh
```

For reproducibility:

```bash
FLOSSWARE_RELEASE_REF=<reviewed-ref> ./scripts/install.sh
```

## Launch

```bash
~/.local/bin/flossware-setup
```

Or, from the repository checkout:

```bash
python3 scripts/setup.py
python3 scripts/setup.py --theme borland-3d
python3 scripts/setup.py --theme trs-80
```

## Walkthrough

### Welcome Screen

The welcome screen identifies the setup as provider-neutral and explains that credentials are optional and budget is a policy.

Press `Enter` to begin. Press `q` or `Esc` to quit.

### Step 1: Select Coding Agents

The supported integrations are:

- Claude Code
- Cursor
- OpenCode

Each selected agent receives its own integration file.

### Step 2: FlossWare AI Capabilities

The core capabilities are pre-selected:

- `model-router-ai` — routing, provider failover, capability and cost awareness
- `resilience-ai` — retry, circuit breaker, timeout patterns
- `structured-output-ai` — schema-validated model output

Optional capabilities include consensus, evaluation, observability, security, retrieval, and optimization.

### Step 3: Budget Policy

Budget is a **policy input**, not a provider category.

Available policies:

- **Strict budget** — zero-cost ceiling
- **Light** — up to $10/month
- **Medium** — up to $50/month
- **Custom** — explicit monthly ceiling

The TUI does not hide providers because they are paid or elevate providers because they are zero-cost. The routing layer decides what is permitted under the selected policy.

### Step 4: Project Directory

Enter the path to your project. It must be a Git repository.

### Step 5: Provider Credential Status

The TUI reports whether supported environment variables are present. It does not display credential values and does not provide signup instructions.

Example:

```text
 SET  Cohere       $COHERE_API_KEY
 ---  OpenRouter   $OPENROUTER_API_KEY
 SET  Gemini       $GEMINI_API_KEY

  2 provider credential(s) detected
  Credentials are optional. Values are never displayed or written.
```

### Build & Summary

The builder installs selected FlossWare libraries into the active Python environment and generates agent-specific configuration files plus the build manifest.

## Generated Files

| File | Agent | Contents |
|------|-------|----------|
| `CLAUDE.md` | Claude Code | AI stack, routing, providers, code guidance |
| `.cursorrules` | Cursor | Libraries, providers, guidelines |
| `AGENTS.md` | OpenCode | Stack, providers, install guidance |
| `ai_config.py` | All | Python configuration wiring selected capabilities |
| `.flossware-ai.json` | All | Build manifest for reproducibility |

Credential values are never written to these files.

## Architecture

```text
request
  -> policy / model router
  -> provider-neutral contract
  -> cross-cutting decorators
  -> provider adapter
  -> model/runtime
```

Decorators implement cross-cutting behavior such as resilience, security, observability, evaluation, structured-output validation, and token/cost accounting. They must not encode provider or pricing preferences.

## Keyboard Controls

| Key | Action |
|-----|--------|
| `↑` `↓` | Move cursor |
| `Space` | Toggle checkbox |
| `Enter` | Confirm / select |
| `a` | Select all |
| `n` | Select none |
| `t` | Theme picker on welcome screen |
| `q` | Quit / cancel |

## Themes

10 themes from [FlossWare/curses-themes](https://github.com/FlossWare/curses-themes):

`dark` `light` `default` `borland-3d` `dos` `dbase-iii` `dbase-iv` `dbase-iv-3d` `ti-99-4a` `trs-80`

Theme support is optional and the TUI has a built-in fallback palette.

## Non-Interactive Installation

The Fedora installer is the canonical non-interactive installation path:

```bash
./scripts/install.sh
```

It installs the actual `coding-agent-ai` runtime, creates an isolated environment, validates the TUI and `pa` command, and installs the `flossware-setup` launcher.

For complete Fedora dogfood instructions, see [platforms/fedora.md](platforms/fedora.md).
