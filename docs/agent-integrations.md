# Coding-agent integrations

FlossWare setup makes individual capabilities usable from coding agents without requiring Loom. Loom remains the complete orchestration platform, but it is optional.

## Agent registry

The setup registry targets:

- Claude Code
- Cursor
- OpenCode
- Crush
- Codex
- Aider
- Cline
- Roo Code
- Gemini CLI
- GitHub Copilot
- Windsurf
- Amazon Q Developer
- Kiro

Support level is capability-based. An agent may support instruction files, MCP, environment configuration, or none of those mechanisms. The Setup TUI shows the integration capabilities it can actually configure.

## Instruction files

FlossWare keeps shared project guidance separate from agent-specific configuration.
Generated files contain behavior/configuration guidance only — never API keys or other secrets.

| Agent | Project file(s) | Notes |
| --- | --- | --- |
| Claude Code | `CLAUDE.md` | Official project memory |
| Cursor | `.cursor/rules/flossware-ai.mdc`, `.cursorrules` | Modern `.mdc` rules preferred; legacy file kept for compatibility |
| OpenCode | `AGENTS.md` | Shared instructions |
| Crush | `AGENTS.md` | Shared context (default init name) |
| Codex | `AGENTS.md` | Official Codex discovery |
| Aider | `CONVENTIONS.md`, `.aider.conf.yml` | Conf sets `read: CONVENTIONS.md` when missing |
| Cline | `.clinerules/FlossWare.md` | Workspace rules directory |
| Roo Code | `.roo/rules/FlossWare.md` | Preferred directory rules |
| Gemini CLI | `GEMINI.md` | Official project context file |
| GitHub Copilot | `.github/copilot-instructions.md`, `AGENTS.md` | Both apply to Copilot coding agent |
| Windsurf | `.windsurfrules` | Project rules file |
| Amazon Q Developer | `.amazonq/rules/FlossWare.md` | Official rules directory |
| Kiro | `.kiro/steering/FlossWare.md` | Workspace steering |

`AGENTS.md` is generated **once** when any shared consumer (OpenCode, Crush, Codex, GitHub Copilot) is selected.
Existing user-owned instruction files without FlossWare markers are left unchanged.

## MCP

Where an agent supports MCP, the Setup TUI can expose selected FlossWare capabilities as MCP servers/tools. MCP is an integration boundary, not the location where the core FlossWare implementation must execute.

A FlossWare capability may therefore be:

```text
agent -> local library
agent -> MCP -> external FlossWare service
agent -> Loom -> full orchestration
```

The choice is configuration-driven and capability-specific.

## Model access

The coding agent may continue to own its native model/account authentication. FlossWare model routing is available independently when the agent or workload is configured to use it. Setup never assumes that a model visible in an agent's native UI is automatically available to the FlossWare router.

## Profiles

Agent configuration is profile-aware. A personal profile can expose personal accounts/models while a Red Hat profile can restrict the effective model/provider set. Secrets are not copied between profiles.

## Dogfood acceptance

Run the repository-level acceptance checks with:

```bash
python scripts/dogfood.py
```

For the real local integration gate, use strict mode on a machine where the primary agents are installed:

```bash
python scripts/dogfood.py --strict
```

Strict mode requires **both Claude Code and Crush** to be present on `PATH`. It does not require or print provider credentials. The checks validate the setup repository, packaging, discovery layer, installer, profile value, and credential-safety invariant, while reporting other detected agents as informational.

The installed CLI exposes the same gate as:

```bash
flossware-ai dogfood --strict
```

`flossware-ai doctor` remains the runtime inventory check. `dogfood` is the acceptance gate for the setup implementation itself.
