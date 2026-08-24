# coding-agent-setup

Interactive TUI builder and Fedora installer for configuring AI coding agents with [FlossWare](https://github.com/FlossWare) AI libraries.

The current dogfood milestone supports **Fedora Linux as the Tier-1 installation target**. The setup layer is provider-neutral and pricing-neutral. Provider/model selection is runtime policy driven.

## Quick Start on Fedora

```bash
# From a checkout of this repository
./scripts/install.sh

# Launch the interactive TUI
~/.local/bin/flossware-setup
```

For reproducibility, pin a reviewed release or commit:

```bash
FLOSSWARE_RELEASE_REF=<reviewed-ref> ./scripts/install.sh
```

See [docs/platforms/fedora.md](docs/platforms/fedora.md) for the complete installation and dogfood procedure.

## Interactive TUI

The TUI walks through:

1. **Select Agents** — choose from the supported coding-agent adapters
2. **FlossWare AI Capabilities** — Pick composable libraries
3. **Budget Policy** — Strict, light, medium, or custom policy
4. **Project Directory** — Where to generate configs
5. **Provider Credentials** — Metadata-only status check for configured providers

Credentials are optional. The TUI never displays or writes credential values.

## Supported Coding Agents

The agent selector is backed by an adapter registry rather than hard-coded TUI behavior. Each adapter declares the project-local instruction/configuration target it supports.

| Agent | Project target | Purpose |
|-------|----------------|---------|
| Claude Code | `CLAUDE.md` | Claude Code project instructions |
| Cursor | `.cursorrules` | Cursor project rules |
| OpenCode | `AGENTS.md` | Shared agent instructions |
| Crush | `AGENTS.md` | Shared project context |
| Codex | `AGENTS.md` | Codex project instructions |
| Aider | `CONVENTIONS.md` + `.aider.conf.yml` | Read-only conventions loaded by Aider |
| Cline | `.clinerules/FlossWare.md` | Project rules |
| Roo Code | `.roo/rules/FlossWare.md` | Project rules |
| Gemini CLI | `GEMINI.md` | Project instructions |
| GitHub Copilot | `.github/copilot-instructions.md` | Repository custom instructions |
| Windsurf | `.windsurfrules` | Windsurf project rules |
| Amazon Q Developer | `.amazonq/rules/FlossWare.md` | Project rules |
| Kiro | `.kiro/steering/FlossWare.md` | Workspace steering |

Shared `AGENTS.md` consumers intentionally use one common project instruction file. The setup tool does not create competing copies for OpenCode, Crush, and Codex.

Existing user-owned instruction/configuration files are preserved. Generated files are created only when absent, making setup safe to rerun.

### Generated Files

| Agent | File | Contents |
|-------|------|----------|
| Claude Code | `CLAUDE.md` | AI stack, routing, providers, usage guidance |
| Cursor | `.cursorrules` | Libraries, providers, guidelines |
| OpenCode / Crush / Codex | `AGENTS.md` | Stack, providers, install guidance |
| Aider | `CONVENTIONS.md`, `.aider.conf.yml` | Conventions and automatic read configuration |
| Cline | `.clinerules/FlossWare.md` | Stack, providers, install guidance |
| Roo Code | `.roo/rules/FlossWare.md` | Stack, providers, install guidance |
| Gemini CLI | `GEMINI.md` | Stack, providers, install guidance |
| GitHub Copilot | `.github/copilot-instructions.md` | Stack, providers, install guidance |
| Windsurf | `.windsurfrules` | Stack, providers, install guidance |
| Amazon Q Developer | `.amazonq/rules/FlossWare.md` | Stack, providers, install guidance |
| Kiro | `.kiro/steering/FlossWare.md` | Always-on workspace steering |
| All | `ai_config.py` | Python configuration wiring selected capabilities |
| All | `.flossware-ai.json` | Build manifest for reproducibility |

Generated files contain configuration and instructions only. **API keys and other credential values are never written to generated project files, manifests, templates, logs, or documentation.**

## FlossWare AI Libraries

| Library | What it does | Default |
|---------|-------------|---------|
| [model-router-ai](https://github.com/FlossWare/model-router-ai) | LLM routing, provider failover, capability and cost awareness | Yes |
| [resilience-ai](https://github.com/FlossWare/resilience-ai) | Retry, circuit breaker, timeout patterns | Yes |
| [structured-output-ai](https://github.com/FlossWare/structured-output-ai) | Schema-validated JSON from LLMs | Yes |
| [consensus-ai](https://github.com/FlossWare/consensus-ai) | Multi-model voting for critical decisions | No |
| [evaluation-ai](https://github.com/FlossWare/evaluation-ai) | Quality scoring, adversarial verification | No |
| [observability-ai](https://github.com/FlossWare/observability-ai) | Structured logging, metrics, cost tracking | No |
| [security-ai](https://github.com/FlossWare/security-ai) | Input validation, secrets masking, audit logging | No |
| [rag-ai](https://github.com/FlossWare/rag-ai) | Document retrieval and hybrid search | No |
| [genetic-optimizer-ai](https://github.com/FlossWare/genetic-optimizer-ai) | Parameter tuning via genetic algorithms | No |

## Provider Credentials

Provider credentials are **optional**. The setup tool does not require or prefer any provider, vendor, hosting topology, or pricing tier.

Supported provider environment variables currently include:

| Provider | Variable |
|----------|----------|
| Cohere | `COHERE_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |
| Gemini | `GEMINI_API_KEY` |
| Groq | `GROQ_API_KEY` |
| Cerebras | `CEREBRAS_API_KEY` |
| HuggingFace | `HUGGINGFACE_API_KEY` |

The installer reports only whether a variable is **set**. It never prints the credential value. Prefer the provider/router's supported authentication mechanism, an existing authenticated CLI session where available, or an OS/CI secret store. Do not put keys in `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.flossware-ai.json`, `ai_config.py`, source control, or logs.

## Architecture

```text
request
  -> policy / model router
  -> provider-neutral contract
  -> cross-cutting decorators
  -> provider adapter
  -> model/runtime
```

Cost is a routing attribute, not an architectural identity. Provider-specific integrations remain behind provider contracts.

## Themes

10 themes via [FlossWare/curses-themes](https://github.com/FlossWare/curses-themes):

`dark` `light` `default` `borland-3d` `dos` `dbase-III` `dbase-IV` `dbase-IV-3d` `ti-99-4a` `trs-80`

Theme support is optional. The TUI has a built-in fallback palette and does not install a theme package during startup.

## Related

- [FlossWare/coding-agent-ai](https://github.com/FlossWare/coding-agent-ai) — Provider-neutral worker/arbiter coding-agent runtime
- [FlossWare/curses-themes](https://github.com/FlossWare/curses-themes) — Terminal UI theming

## License

MIT
