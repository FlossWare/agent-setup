# Operator guide

This is the canonical end-to-end guide for `coding-agent-setup`.

## 1. Install

Linux/Termux:

```bash
./scripts/install.sh
```

Windows:

```powershell
.\scripts\install.ps1
```

The installer prefers released artifacts and uses source installation only as an explicit fallback. Managed state is isolated under the platform-appropriate FlossWare user-data directory.

## 2. Launch the Setup Control Center

```bash
flossware-ai tui
```

The TUI is the operator/configuration interface. It is not Loom's optional TUI.

The main control center provides access to configuration, credentials, review, and diagnostics. The current UI is intentionally organized around stable IDs rather than positional catalog indexes, so catalog ordering can change without corrupting persisted selections.

### Status line

Selectable menus provide a contextual status line immediately above the key legend. Move with the arrow keys or hover with the mouse. The status line follows the current item and explains what that item represents or what safe state is known about it.

For example:

```text
STATUS: Crush | Shared project context
```

or:

```text
STATUS: Provider Credentials | source presence only | secret values hidden
```

Status is informational. Hovering does not change configuration. Enter/Space or a supported primary mouse click performs the actual selection/action. Status rendering never displays credentials or PII.

## 3. Configure an agent

Use the TUI or:

```bash
flossware-ai agents
flossware-ai agents setup crush
```

Supported registry entries include Claude Code, Cursor, OpenCode, Crush, Codex, Aider, Cline, Roo Code, Gemini CLI, GitHub Copilot, Windsurf, Amazon Q Developer, and Kiro. Actual integration capability is detected per agent.

## 4. Configure capabilities

```bash
flossware-ai components
flossware-ai components model-router-ai
```

Capabilities can run as local libraries, through MCP, or as part of Loom. Loom is optional.

## 5. Configure accounts and models

FlossWare stores credential-source references, not credential values. Use:

```bash
flossware-ai providers
flossware-ai accounts --verify
flossware-ai models --refresh
```

The active profile determines which discovered resources are permitted.

## 6. Choose execution runtime

```bash
flossware-ai runtime list
flossware-ai runtime status
flossware-ai runtime auto
```

Podman, Docker, and native execution are supported according to platform capabilities.

## 7. Review

Review should operate on the explicitly active project context rather than assuming the current shell directory is the configured project. Review output is intended to show policy/configuration state without exposing credentials.

## 8. Mouse and keyboard

The TUI supports normal curses keyboard navigation plus primary mouse clicks where the terminal exposes mouse events. Mouse movement can move the current cursor and update the contextual status line. SSH clients, multiplexers, and terminal emulators may differ.

Common keys:

- Arrow keys: navigate and update status
- Enter: activate/confirm
- Space: toggle
- Mouse movement: hover/navigate without changing configuration
- Primary click: select/toggle/activate
- `a`: select all where offered
- `n`: select none where offered
- Escape: back/cancel
- `q`: quit where offered

## 9. Profiles

The repository ships only `default`. Create local policy profiles for personal, work, Red Hat, government, client, or other environments. The public code does not assume any employer or organization.

See [`profile-schema.md`](profile-schema.md).

## 10. Validate

```bash
flossware-ai doctor
flossware-ai dogfood --strict
```

Strict dogfood requires Claude Code and Crush on `PATH`. It does not print credentials.

CI additionally exercises clean Fedora and Debian installation boundaries. CI is not a substitute for authenticated operator dogfood.

## 11. Reinstall or remove managed state

```bash
./scripts/install.sh --reinstall
./scripts/install.sh --clean
```

Cleanup removes only FlossWare-managed installation state. Native agent credentials, project instruction files, and unrelated user data are outside that boundary.

## Related references

- [CLI reference](cli-reference.md)
- [Profile schema](profile-schema.md)
- [Provider/account/model discovery](discovery.md)
- [Agent integrations](agent-integrations.md)
- [Troubleshooting](troubleshooting.md)
- [Platform support](platforms.md)
- [Security](SECURITY.md)
- [Privacy](privacy.md)
- [Architecture](architecture.md)
