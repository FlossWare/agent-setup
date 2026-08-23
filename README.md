# coding-agent-setup

Interactive TUI builder for configuring AI coding agents with [FlossWare](https://github.com/FlossWare) AI libraries.

Generates custom configs for **Claude Code**, **Cursor**, and **OpenCode/Codex** — wired to model-router-ai, resilience-ai, structured-output-ai, and the rest of the FlossWare AI stack.

## Quick Start

```bash
# Interactive TUI
python3 scripts/setup.py

# With a specific theme
python3 scripts/setup.py --theme borland-3d

# Non-interactive
./scripts/install.sh --agent all --repo /path/to/project
```

Or one-liner install:

```bash
curl -sSL https://raw.githubusercontent.com/FlossWare/coding-agent-setup/main/scripts/install.sh | bash
```

## Interactive TUI

The TUI walks through 5 steps:

```
┌──────────────────────────────────────────────────────────────┐
│ FlossWare AI — Coding Agent Setup                            │
└──────────────────────────────────────────────────────────────┘

  Configure AI coding agents with FlossWare libraries
  github.com/FlossWare/coding-agent-setup
  Theme: dark  (press 't' to change, Enter to start)
```

1. **Select Agents** — Claude Code, Cursor, OpenCode/Codex
2. **FlossWare AI Capabilities** — Pick from 9 composable libraries
3. **Budget** — Free, Light ($10), Medium ($50), Custom
4. **Project Directory** — Where to generate configs
5. **API Keys** — Status check for configured providers

### Generated Files

| Agent | File | Contents |
|-------|------|----------|
| Claude Code | `CLAUDE.md` | AI stack, routing, providers, usage examples |
| Cursor | `.cursorrules` | Libraries, providers, guidelines |
| OpenCode | `AGENTS.md` | Stack, providers, install commands |
| All | `ai_config.py` | Python config wiring selected capabilities |
| All | `.flossware-ai.json` | Build manifest for reproducibility |

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

## API Keys

Set at least one free provider key:

| Provider | Variable | Free Tier |
|----------|----------|-----------|
| Cohere | `COHERE_API_KEY` | Yes |
| OpenRouter | `OPENROUTER_API_KEY` | Yes |
| Gemini | `GEMINI_API_KEY` | Yes |
| Groq | `GROQ_API_KEY` | No |
| Cerebras | `CEREBRAS_API_KEY` | No |
| HuggingFace | `HUGGINGFACE_API_KEY` | No |

## Themes

10 themes via [FlossWare/curses-themes](https://github.com/FlossWare/curses-themes):

`dark` `light` `default` `borland-3d` `dos` `dbase-iii` `dbase-iv` `dbase-iv-3d` `ti-99-4a` `trs-80`

Press `t` on the welcome screen to preview and switch.

## Related

- [FlossWare/personal-agent](https://github.com/FlossWare/personal-agent) — Worker/arbiter coding agent using these libraries
- [FlossWare/curses-themes](https://github.com/FlossWare/curses-themes) — Terminal UI theming

## License

MIT
