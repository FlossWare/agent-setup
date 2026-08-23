# Interactive TUI Setup Guide

The `scripts/setup.py` builder walks you through configuring AI coding agents
with FlossWare libraries. It generates custom config files tailored to your
selected agents, capabilities, budget, and API keys.

## Requirements

- Python 3.11+
- A terminal that supports colors (most do)
- curses-themes (auto-installed on first run)

## Launch

```bash
python3 scripts/setup.py                    # dark theme (default)
python3 scripts/setup.py --theme borland-3d # retro Borland look
python3 scripts/setup.py --theme trs-80     # vintage terminal
```

## Walkthrough

### Welcome Screen

```
┌──────────────────────────────────────────────────────────────┐
│ FlossWare AI — Coding Agent Setup                            │
└──────────────────────────────────────────────────────────────┘

  Configure AI coding agents with FlossWare libraries
  github.com/FlossWare/coding-agent-setup
  Theme: dark  (press 't' to change, Enter to start)
```

Press `t` to preview and switch themes. Press `Enter` to begin.

### Step 1: Select Coding Agents

```
┌──────────────────────────────────────────────────────────────┐
│ 1/5  Select Coding Agents                                    │
└──────────────────────────────────────────────────────────────┘

 > [x] Claude Code       Terminal, desktop, web, IDE extensions
   [x] Cursor            AI-native IDE with built-in models
   [x] OpenCode / Codex  Terminal-based coding agents

  Space:toggle  Enter:confirm  a:all  n:none  q:quit
```

Select which agents you use. Each gets its own config file.

### Step 2: FlossWare AI Capabilities

```
┌──────────────────────────────────────────────────────────────┐
│ 2/5  FlossWare AI Capabilities                               │
└──────────────────────────────────────────────────────────────┘

 > [x] model-router-ai       Smart LLM routing with provider failover
   [x] resilience-ai          Retry, circuit breaker, timeout patterns
   [x] structured-output-ai   Schema-validated JSON from LLMs
   [ ] consensus-ai           Multi-model voting for critical decisions
   [ ] evaluation-ai          Quality scoring and adversarial verification
   [ ] observability-ai       Structured logging, metrics, cost tracking
   [ ] security-ai            Input validation, secrets masking, audit logging
   [ ] rag-ai                 Document retrieval and hybrid search
   [ ] genetic-optimizer-ai   Parameter tuning via genetic algorithms

  Space:toggle  Enter:confirm  a:all  n:none  q:quit
```

The 3 core libraries are pre-selected. Add optional capabilities as needed.

### Step 3: Monthly Budget

```
┌──────────────────────────────────────────────────────────────┐
│ 3/5  Monthly Budget                                          │
└──────────────────────────────────────────────────────────────┘

 > (o) Free only    Cohere, OpenRouter, Gemini free tiers
   ( ) Light        $10/month — adds Groq, Cerebras fast inference
   ( ) Medium       $50/month — adds Claude Haiku, GPT-4o-mini
   ( ) Custom       Set your own monthly budget

  Enter:select  q:quit
```

Budget selection configures model-router-ai's cost awareness.

### Step 4: Project Directory

Enter the path to your project. Must be a git repository.

### Step 5: API Key Status

```
┌──────────────────────────────────────────────────────────────┐
│ API Key Status                                               │
└──────────────────────────────────────────────────────────────┘

  Budget: Free only
  Only free-tier providers shown

 SET  Cohere       $COHERE_API_KEY
 ---  OpenRouter   $OPENROUTER_API_KEY
                   https://openrouter.ai/keys
 SET  Gemini       $GEMINI_API_KEY

  2 provider(s) configured

  Press any key to continue...
```

Shows which API keys are set. Unset keys show signup URLs.

### Build & Summary

The builder installs selected libraries via pip, generates agent-specific
config files, and writes the build manifest (`.flossware-ai.json`).

## Generated Files

| File | Agent | Contents |
|------|-------|----------|
| `CLAUDE.md` | Claude Code | AI stack, routing, providers, code examples |
| `.cursorrules` | Cursor | Libraries, providers, guidelines |
| `AGENTS.md` | OpenCode | Stack, providers, install commands |
| `ai_config.py` | All | Python config wiring selected capabilities |
| `.flossware-ai.json` | All | Build manifest for reproducibility |

## Keyboard Controls

| Key | Action |
|-----|--------|
| `↑` `↓` | Move cursor |
| `Space` | Toggle checkbox |
| `Enter` | Confirm / select |
| `a` | Select all |
| `n` | Select none |
| `t` | Theme picker (welcome screen) |
| `q` | Quit / cancel |

## Themes

10 themes from [FlossWare/curses-themes](https://github.com/FlossWare/curses-themes):

| Theme | Style |
|-------|-------|
| dark | Modern dark terminal |
| light | Light background |
| default | System default colors |
| borland-3d | Blue Borland/Turbo Pascal |
| dos | Classic DOS look |
| dbase-iii | dBASE III monochrome |
| dbase-iv | dBASE IV blue |
| dbase-iv-3d | dBASE IV with 3D borders |
| ti-99-4a | TI-99/4A home computer |
| trs-80 | TRS-80 green phosphor |

## Non-Interactive Alternative

For CI/CD or headless environments:

```bash
./scripts/install.sh --agent all --repo /path/to/project
```

This installs core libraries and copies starter templates without the TUI.
