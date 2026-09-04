# Setup TUI

`flossware-setup`, `flossware-ai setup`, and `flossware-ai tui` launch the same authoritative implementation: `flossware_setup.tui`.

The TUI uses `FlossWare/curses-tui` for low-level terminal interaction primitives. `agent-setup` retains ownership of setup workflows, persistence, profiles, and domain-specific actions.

For the complete end-to-end workflow, see [`operator-guide.md`](operator-guide.md). For command syntax see [`cli-reference.md`](cli-reference.md).

## Control center

The TUI opens with four actions:

- **Review Current Configuration**: reads persisted project state for the active project, not merely the process cwd.
- **Configure / Change Setup**: select agents, FlossWare capabilities, budget policy, and target repository using stable IDs.
- **Provider Credentials**: displays detected credential-source names only. Secret values are never shown or written.
- **Exit**: leave the TUI.

## Contextual status line

Every selectable menu has a status line immediately above the key legend. The status line describes the item currently under the keyboard cursor or mouse pointer.

Examples:

```text
STATUS: Crush | Shared project context
STATUS: Provider Credentials | source presence only | secret values hidden
STATUS: Review | inspect persisted project configuration | secret-free
```

Keyboard navigation and mouse movement update the same status line. **Hovering/moving is informational only.** It never changes configuration. Selection changes only when the operator activates an item with Enter/Space or a supported mouse click.

Status text is deliberately non-secret. It is derived from catalog labels, descriptions, and safe configuration state. Credential values and PII are never rendered into the status line.

The status line is designed to remain useful at narrow terminal widths, and the operator can rely on keyboard navigation when a terminal does not expose mouse-motion events.

## Configuration flow

The Configure / Change Setup wizard currently proceeds through:

1. **Select Coding Agents**
2. **FlossWare AI Capabilities**
3. **Budget Policy**
4. **Project directory**
5. Provider credential status, configuration build, and review

The authoritative agent catalog contains 13 integrations. The wizard stores stable IDs, so catalog ordering can change without invalidating persisted configuration.

## Profiles and discovery

The public repository ships a single neutral **`default`** profile. Users and organizations may create additional local profiles such as `personal`, `work`, `redhat`, or `government`. Those names are local policy, not public repository assumptions.

Provider, account, and model state is deliberately separate. See [`profile-schema.md`](profile-schema.md) and [`discovery.md`](discovery.md).

## Keyboard and mouse

Keyboard and mouse input are supported when the terminal exposes mouse events. Primary mouse clicks activate selectable menu entries, and mouse movement can move the current menu cursor and therefore update the status line. Terminal emulators, SSH clients, and multiplexers can differ in mouse-event behavior.

The profile selector consumes the reusable `Menu`/`MenuItem` accelerator dispatch from `curses-tui`; `1` through `9` select the corresponding visible profile directly. Popup geometry is backed by `Window`/`WindowManager`, so title-bar dragging and border/corner resizing use the shared interaction semantics rather than an application-specific implementation.

Common keys:

- Arrow keys: navigate and update status
- Enter: activate/confirm
- Space: toggle
- `1`-`9`: profile selector accelerators
- Mouse movement: hover/navigate and update status without changing selection
- Primary click: select/toggle/activate
- `a`: select all where offered
- `n`: select none where offered
- Escape: back/cancel
- `q`: quit where offered

## Entry points

| Command | Role |
| --- | --- |
| `python scripts/setup.py` | Source-tree Setup TUI |
| `python scripts/tui.py` | Same package TUI entry point |
| `flossware-setup` | Package console script |
| `flossware-ai setup` | Managed-install Setup TUI |
| `flossware-ai tui` | Same managed Setup TUI |

## Privacy

Generated project files (`.flossware-ai.json`, `ai_config.py`, and agent instruction files) never contain credential values. Active-project state stores only non-secret metadata required to reopen the configured project.

Credential references identify sources such as environment variables. They do not contain the corresponding secret values.

## Screenshots

Files under `screenshots/` are documentation renderings, not claims of pixel-identical terminal captures. They are kept synchronized with the current control-center/wizard flow and status-line behavior, and are labeled as representative where appropriate.
