# FlossWare Setup TUI

`flossware-ai tui` is the interactive control plane for configuring FlossWare AI capabilities for coding agents. It is intentionally separate from the Loom operator TUI: Setup configures the system; Loom visualizes and controls live orchestration.

## Navigation

The Setup TUI is organized around these areas:

- **Profiles** — select `personal` or `redhat` and inspect effective policy.
- **Agents** — discover supported coding agents and generate safe integration configuration.
- **Providers & Accounts** — inspect provider accounts, credential sources, verification state, and model discovery.
- **Components** — enable and configure independently usable FlossWare capabilities.
- **Cross-Cutting Behavior** — configure and order decorators/interceptors/middleware.
- **MCP** — inspect and configure FlossWare MCP exposure to supported agents.
- **Execution** — select Native, Auto, Podman, or Docker and inspect runtime health.
- **Installation** — inspect artifact/source state and repair or reinstall managed components.
- **Doctor** — validate configuration, credentials, models, integrations, and runtimes.

Every major selection has a contextual description and status. Status describes the actual state rather than merely reflecting a selected checkbox.

## Agents

The agent registry includes Claude Code, Cursor, OpenCode, Crush, Codex, Aider, Cline, Roo Code, Gemini CLI, GitHub Copilot, Windsurf, Amazon Q Developer, and Kiro. Agent setup generates only the files required by that agent and keeps provider credentials outside generated instruction files.

The TUI distinguishes shared project instructions from agent-specific configuration. `AGENTS.md` is used where an agent supports the shared convention; `CLAUDE.md`, `.cursorrules`, and equivalent files are generated only for agents that require them.

## Profiles

A profile determines the effective provider/model policy, account visibility, allowed capabilities, execution defaults, and cross-cutting policy. Switching profiles does not copy secrets. Profile configuration is declarative and inherits defaults where supported.

The default personal profile is intended for personal accounts and available free/paid services. The Red Hat profile is intended for organization-approved providers and models. The setup layer does not infer organizational approval from price or provider name; approval is represented by explicit profile policy.

## Accounts and credentials

A provider may have multiple accounts. An account has an independent identity/label and credential-source reference. For example, several OpenAI accounts can coexist without overwriting one another.

The TUI reports:

- provider
- account label
- credential source type/reference
- configured state
- verification state
- discovered models
- profile permission
- active selection

Credential values are never displayed or persisted by the setup TUI. Environment variables, native credential stores, and agent-owned authentication remain the secret authority.

## Models

Model discovery is separate from credential configuration. A model can be discovered by an authenticated account but still be unavailable because the active profile does not permit it. The UI distinguishes `configured`, `discovered`, `available`, `ready`, and `active` states.

Refreshing discovery never replaces credentials. Provider/model selection remains provider-neutral and capability-driven.

## Components

FlossWare capabilities are independently usable. Loom is not required for components such as model routing, RAG, semantic search, embeddings, evaluation, observability, resilience, or consensus. The TUI exposes installation and configuration for each capability independently.

Installation is artifact-first. A compatible released artifact is preferred; source installation is an explicit fallback. Generated artifacts are derived outputs and never the source of configuration truth.

## MCP

MCP configuration exposes selected FlossWare capabilities to coding agents that support MCP. The TUI manages server definitions, enabled capabilities, and safe references. Secrets remain outside MCP definitions unless an agent's native secret mechanism explicitly owns them.

## Execution runtimes

The execution backend can be:

- **Auto** — choose a healthy supported runtime according to platform policy.
- **Podman** — preferred on Linux when healthy.
- **Docker** — fully supported.
- **Native** — no container runtime.

The TUI reports installed, reachable, version, selected, and effective state. Selecting Auto never installs a runtime. See `docs/container-runtimes.md`.

## Installation and repair

The managed installation lives under `~/.flossware/ai` on Unix-like systems and the platform-appropriate user data location on Windows. The setup tool owns that directory.

Use the installer for clean lifecycle operations rather than manually deleting files:

```text
install --reinstall
install --clean
```

Cleanup removes managed FlossWare state only. It does not remove agent project files, provider credentials, or native agent authentication.

## Doctor

The Doctor screen is the fastest way to determine why a capability is not usable. It validates configuration, credential references, account verification, model discovery, profile policy, agent integration, MCP configuration, container runtime reachability, and installed component state.

Use the CLI equivalent when a TUI is not available:

```text
flossware-ai doctor
```

## Loom boundary

Loom is the complete external orchestration platform. Its core is headless and may expose a separate curses-themes-based operator TUI. The Setup TUI does not run Loom's live execution dashboard.

The intended relationship is:

```text
Setup TUI
    |
    +-- configure FlossWare capabilities
    +-- configure agents/accounts/models
    +-- configure policies/decorators
    +-- configure MCP and execution
    |
    +---------------------> coding agents
    |
    +---------------------> Loom
                               |
                               +-- orchestration
                               +-- routing
                               +-- retrieval
                               +-- consensus
                               +-- evaluation
                               +-- live operator TUI
```
