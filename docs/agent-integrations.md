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

- `AGENTS.md` is the common convention for agents that support it.
- `CLAUDE.md` is used for Claude Code-specific guidance.
- `.cursorrules` is used for Cursor where required.
- Other agent-specific files are generated only when the target agent requires them.

Generated instruction files contain behavior/configuration guidance, never API keys or other secrets.

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

## Testing integrations

`flossware-ai doctor` should report whether an agent was detected, which integration mechanisms are available, whether generated configuration is current, and whether required MCP or credential references are usable.
