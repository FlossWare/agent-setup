# Interactive TUI Setup Guide

`coding-agent-setup` configures coding agents to use FlossWare capabilities. It is provider-neutral and pricing-neutral. Provider, account, model, profile, and budget selection are runtime policy decisions.

The public project is designed to be reusable by individuals, teams, enterprises, government environments, and other organizations. It does **not** assume a Red Hat, personal, or other organization-specific profile. The repository ships a neutral `default` profile; users create named profiles such as `personal`, `work`, `redhat`, or `government` as local policy requires.

## Mouse and keyboard interaction

The Setup TUI supports **mouse clicks when the terminal exposes curses mouse events**. Keyboard operation remains fully supported and is never replaced by mouse input.

On selection screens:

- **Left-click a row** to move the cursor and select/toggle that row.
- For multi-select screens, clicking toggles the checkbox immediately.
- For single-select screens, clicking a row selects it immediately and advances to the next step.
- `Enter` confirms the current selection when using the keyboard.
- `↑`/`↓` and `j`/`k` navigate by keyboard.
- `Space` toggles a multi-select row.
- `a` selects all and `n` clears all on multi-select screens.
- `q` or `Esc` quits/cancels where applicable.

Mouse support depends on the terminal emulator, multiplexer, and curses implementation. If mouse reporting is unavailable, the TUI automatically remains keyboard-only.

## Current installation model

The setup project provides:

- a shared FlossWare configuration/control plane;
- coding-agent integrations;
- provider/account/model discovery;
- user-defined profiles and policy boundaries;
- credential-source references without storing credential values;
- FlossWare capability selection;
- MCP integration;
- runtime selection and health reporting;
- the `flossware-ai` CLI and Setup TUI.

Loom AI is optional. The setup project can configure and use FlossWare capabilities without requiring Loom.

## Install

Linux/macOS-style environments:

```bash
./scripts/install.sh
```

For a reviewed/reproducible installer reference:

```bash
FLOSSWARE_RELEASE_REF=<reviewed-ref> ./scripts/install.sh
```

On Windows, use the repository's PowerShell installer where provided.

The installer creates the managed FlossWare runtime under the platform-appropriate user data directory. It does not require manually deleting that directory for reinstallation or cleanup.

## Launch

The canonical operator interface is:

```bash
flossware-ai tui
```

If the launcher is not on `PATH`, use the launcher installed by the current installer/runtime location. Do not assume the historical `flossware-setup` path is present.

The TUI can also be exercised directly from a repository checkout when the development environment is installed.

## Requirements

Requirements vary by platform. The current dogfood target is Fedora Linux, with Debian-family Linux, FreeBSD, Termux, and Windows documented separately where supported.

For the Fedora dogfood path, use Python 3.11+, Git, and a terminal with curses support. Optional TUI themes use `curses-themes`; the TUI retains a built-in fallback and does not require a theme package merely to start.

## TUI walkthrough

### Welcome

The welcome screen identifies the setup as provider-neutral and explains that credentials are optional and budget is a policy. Press `Enter` or click to begin; `q` or `Esc` exits/cancels where applicable.

### Coding agents

The setup layer supports the agent integrations documented by the current CLI. These include Claude Code, Cursor, OpenCode, Crush, Codex, Aider, Cline, Roo Code, Gemini CLI, GitHub Copilot, Windsurf, Amazon Q Developer, and Kiro. Availability can vary by platform and installed agent.

Each selected integration is configured using the agent's supported mechanism. Shared project instructions use the appropriate common instruction file where supported rather than copying secrets between agents.

### FlossWare capabilities

Core capabilities include model routing, resilience, and structured-output handling. Optional capabilities include consensus, evaluation, observability, security, retrieval, optimization, and other installed FlossWare components.

### Profiles

Profiles are policy boundaries. The public repository provides only a neutral `default` starting profile. A profile can restrict providers, accounts, models, local models, credentials, and FlossWare capabilities.

Example local configuration:

```text
~/.flossware/ai/profiles/
├── default.toml
├── personal.toml
└── work.toml
```

`work.toml` could represent Red Hat policy for one user, Acme policy for another, or any other organizational boundary. The profile name has no built-in semantics.

### Accounts and credentials

A provider may have multiple accounts. Account identity is separate from provider identity, and the active profile determines which accounts are permitted.

The setup layer records credential **sources/references**, never credential values. Environment variables, native credential stores, and agent-owned authentication can remain authoritative. Credential values must not be written to generated agent files, configuration, MCP definitions, logs, or source control.

### Models and providers

Provider/model selection is policy-driven. The setup layer does not treat paid providers as inherently preferred or free providers as inherently preferred. Availability depends on account authentication, active profile policy, provider capabilities, platform support, and budget/cost policy.

### Budget policy

Budget is a policy input, not a provider category. Routing can consider a monthly ceiling, token/cost accounting, provider availability, and model capability. A budget policy must not silently turn credentials into unrestricted access to every configured provider.

### Container runtime

The runtime selector can use Auto, Podman, Docker, or Native execution where supported. Health and version information are reported rather than assuming a runtime exists.

## Generated configuration

Depending on the selected agents and capabilities, the setup layer may generate or update files such as `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `ai_config.py`, and `.flossware-ai.json`. The exact generated set is agent/version dependent.

Generated files contain configuration and guidance, not credential values.

## Architecture

```text
agent
  -> profile / policy
  -> account + model selection
  -> FlossWare capability
  -> cross-cutting decorators
  -> provider adapter
  -> model/runtime
```

## CLI

Useful commands include:

```bash
flossware-ai agents
flossware-ai agents setup crush
flossware-ai components
flossware-ai components model-router-ai
flossware-ai accounts --verify
flossware-ai models --refresh
flossware-ai providers
flossware-ai runtime list
flossware-ai runtime status
flossware-ai runtime select podman
flossware-ai runtime select docker
flossware-ai runtime auto
flossware-ai doctor
flossware-ai tui
```

## Themes

The TUI can use themes from `FlossWare/curses-themes` when available. A built-in fallback palette keeps the TUI usable without the optional theme package. Themes control presentation; mouse interaction remains owned by the Setup TUI.

## Privacy and security invariants

FlossWare managed configuration is secret-free and non-identifying. API keys, OAuth tokens, passwords, cookies, email addresses, employee/customer identifiers, phone numbers, and similar PII must not be persisted in managed profiles, generated agent files, MCP definitions, logs, or diagnostics.

See [`privacy.md`](privacy.md), [`SECURITY.md`](SECURITY.md), and [`credentials-and-accounts.md`](credentials-and-accounts.md).

## Documentation authority

Use this guide for the operator workflow, the repository README for project architecture and quick start, and platform-specific documentation for installation details. CLI help and the running TUI are authoritative when an agent/version-specific option differs from a static example.

## Project state file safety

- **Do not commit `.flossware-ai.json` to version control** unless your team explicitly accepts local paths and agent selections in the repository. Prefer gitignore.
- The file is designed to be secret-free (presence flags and env-var names only). If a credential was ever pasted into it by hand, rotate that credential, delete the file, and re-run setup.
- Recovery: `rm .flossware-ai.json` in the project, ensure secrets live only in the environment or OS/agent store, then run `flossware-ai` configure again.

## Git is optional

FlossWare works against any directory. A `.git` directory enables Git-aware features when present; its absence is reported as `Git: not a repository` rather than an error.

Project **state and metadata** are stored under the managed FlossWare root (default `~/.flossware/ai/projects/<id>/`), not as `.flossware-ai.json` inside the project tree. Optional agent instruction files (`CLAUDE.md`, `AGENTS.md`, …) are written into the project only when you configure agents for that directory.
