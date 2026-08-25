# coding-agent-setup

FlossWare's shared control plane for configuring coding agents and independently usable FlossWare AI capabilities. Fedora Linux is the Tier-1 installation target.

## Quick start

```bash
./scripts/install.sh
flossware-ai tui
```

The managed runtime lives at `~/.flossware/ai`. Reinstallation and cleanup never require manually deleting that directory:

```bash
./scripts/install.sh --reinstall
./scripts/install.sh --clean
```

`--clean` removes only the managed FlossWare AI installation. It does not remove project instruction files, native agent credentials, or provider credentials.

## Architecture

Loom AI is the complete external orchestration platform, but Loom is optional. FlossWare AI libraries remain independently usable from Claude Code, Crush, Codex, OpenCode, Cursor, and other agents.

```text
Agent
  |
  +--> individual FlossWare capability
  |      model-router / RAG / search / evaluation / ...
  |
  +--> Loom AI (complete orchestration platform)
```

The setup layer provides the common configuration, profile, account/model discovery, credential-source references, MCP integration, CLI, and operator TUI. It does not copy provider secrets into generated files.

## CLI

```bash
flossware-ai agents
flossware-ai agents setup crush
flossware-ai components
flossware-ai components model-router-ai
flossware-ai accounts --verify
flossware-ai models --refresh
flossware-ai providers
flossware-ai doctor
flossware-ai tui
```

Supported agents include Claude Code, Cursor, OpenCode, Crush, Codex, Aider, Cline, Roo Code, Gemini CLI, GitHub Copilot, Windsurf, Amazon Q Developer, and Kiro. Shared `AGENTS.md` consumers intentionally use one common project instruction file.

## Profiles and accounts

Profiles currently include `personal` and `redhat`. An account is distinct from a provider, so multiple accounts can reference the same provider. Account metadata stores labels and credential-source references only. Actual credentials remain in environment/native credential stores.

Status vocabulary:

- **configured**: a credential source is present
- **discovered**: an authenticated provider advertised the model/account
- **available**: discovered and permitted by the active profile
- **ready**: credentials, policy, and connectivity checks pass
- **active**: selected for the current workload

## Cross-cutting decorators

FlossWare uses explicitly enabled decorators/interceptors/middleware for cross-cutting behavior such as retries, circuit breaking, observability, auditing, caching, evaluation, security/policy enforcement, structured-output validation, and token/cost accounting. This follows Engineering Standards ADR-0006.

The TUI configures these declaratively under **Components → Cross-Cutting Behavior**. Users can enable/disable decorators, edit their policy settings, and reorder the stack when ordering affects semantics. The runtime translates that policy into the appropriate decorator/interceptor/middleware implementation.

Decorator configuration is provider-neutral and contains no secrets. Profile defaults may supply policy, while component configuration provides explicit opt-in or override. See [`docs/decorators.md`](docs/decorators.md).

## TUI

`flossware-ai tui` is the full operator/configuration TUI. It is separate from Loom's optional `loom-tui` and is intended for using FlossWare capabilities in isolation with coding agents.

Every major TUI selection has a contextual status/description panel explaining what the component does and its current state. Cross-cutting behavior is presented as a configurable policy stack rather than raw implementation details.

Loom itself has a headless core plus its own optional curses-themes-based TUI.

## Credential safety

API keys and other credential values are never written to `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.flossware-ai.json`, generated Python, logs, or MCP definitions. Agent-native authentication remains owned by the agent; FlossWare maintains only safe references and policy metadata.

## Related repositories

- [FlossWare/loom-ai](https://github.com/FlossWare/loom-ai) — complete orchestration platform
- [FlossWare/model-router-ai](https://github.com/FlossWare/model-router-ai) — provider/account/model routing
- [FlossWare/curses-themes](https://github.com/FlossWare/curses-themes) — shared TUI themes
- [FlossWare/coding-agent-ai](https://github.com/FlossWare/coding-agent-ai) — coding-agent runtime

## License

MIT
