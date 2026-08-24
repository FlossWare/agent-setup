# coding-agent-setup

Interactive TUI builder for configuring AI coding agents with [FlossWare](https://github.com/FlossWare) AI libraries.

Generates custom configs for **Claude Code**, **Cursor**, and **OpenCode/Codex** with provider-neutral routing, resilience, structured output, and other FlossWare AI capabilities.

## Quick Start

```bash
# Interactive TUI
python3 scripts/setup.py

# With a specific theme
python3 scripts/setup.py --theme borland-3d

# Non-interactive
./scripts/install.sh --agent all --repo /path/to/project
```

For a convenient bootstrap, inspect `scripts/install.sh` first, then run it. The installer is designed to fail clearly on required setup failures rather than silently producing a partial installation.

## Interactive TUI

The TUI walks through 5 steps:

1. **Select Agents** — Claude Code, Cursor, OpenCode/Codex
2. **FlossWare AI Capabilities** — Pick from composable libraries
3. **Budget** — Configure a spending policy: free, light, medium, or custom
4. **Project Directory** — Where to generate configs
5. **API Keys** — Metadata-only status check for configured providers

### Generated Files

| Agent | File | Contents |
|-------|------|----------|
| Claude Code | `CLAUDE.md` | AI stack, routing, providers, usage examples |
| Cursor | `.cursorrules` | Libraries, providers, guidelines |
| OpenCode | `AGENTS.md` | Stack, providers, install commands |
| All | `ai_config.py` | Python config wiring selected capabilities |
| All | `.flossware-ai.json` | Build manifest for reproducibility |

Generated files contain configuration and instructions only. **API keys and other credential values are never written to generated project files, manifests, templates, logs, or documentation.**

## FlossWare AI Libraries

| Library | What it does | Default |
|---------|-------------|---------|
| [model-router-ai](https://github.com/FlossWare/model-router-ai) | LLM routing, provider failover, cost awareness | Yes |
| [resilience-ai](https://github.com/FlossWare/resilience-ai) | Retry, circuit breaker, timeout patterns | Yes |
| [structured-output-ai](https://github.com/FlossWare/structured-output-ai) | Schema-validated JSON from LLMs | Yes |
| [consensus-ai](https://github.com/FlossWare/consensus-ai) | Multi-model voting for critical decisions | No |
| [evaluation-ai](https://github.com/FlossWare/evaluation-ai) | Quality scoring, adversarial verification | No |
| [observability-ai](https://github.com/FlossWare/observability-ai) | Structured logging, metrics, cost tracking | No |
| [security-ai](https://github.com/FlossWare/security-ai) | Input validation, secrets masking, audit logging | No |
| [rag-ai](https://github.com/FlossWare/rag-ai) | Document retrieval and hybrid search | No |
| [genetic-optimizer-ai](https://github.com/FlossWare/genetic-optimizer-ai) | Parameter tuning via genetic algorithms | No |

## Provider Credentials

Provider credentials are **optional** and depend on the routing policy you choose. The setup tool does not require a free provider and does not assume that free models are the only supported models.

Supported provider environment variables include:

| Provider | Variable |
|----------|----------|
| Cohere | `COHERE_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |
| Gemini | `GEMINI_API_KEY` |
| Groq | `GROQ_API_KEY` |
| Cerebras | `CEREBRAS_API_KEY` |
| HuggingFace | `HUGGINGFACE_API_KEY` |

The installer reports only whether a variable is **set**. It never prints the credential value. For secure credential handling, prefer the provider/router's supported secret-management mechanism or an OS/CI secret store. Do not put keys in `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.flossware-ai.json`, `ai_config.py`, source control, or logs.

## Themes

10 themes via [FlossWare/curses-themes](https://github.com/FlossWare/curses-themes):

`dark` `light` `default` `borland-3d` `dos` `dbase-iii` `dbase-iv` `dbase-iv-3d` `ti-99-4a` `trs-80`

Press `t` on the welcome screen to preview and switch.

## Related

- [FlossWare/coding-agent-ai](https://github.com/FlossWare/coding-agent-ai) — Worker/arbiter coding-agent runtime using these libraries
- [FlossWare/curses-themes](https://github.com/FlossWare/curses-themes) — Terminal UI theming

## License

MIT
