# Setup TUI

`flossware-setup`, `flossware-ai setup`, and `flossware-ai tui` launch the same authoritative implementation: `flossware_setup.tui`.

For the complete end-to-end workflow, see [`operator-guide.md`](operator-guide.md). For command syntax see [`cli-reference.md`](cli-reference.md).

## Control center

The TUI opens with four actions:

- **Review Current Configuration**: reads persisted project state for the active project, not merely the process cwd.
- **Configure / Change Setup**: select agents, FlossWare capabilities, budget policy, and target repository using stable IDs.
- **Provider Credentials**: displays detected credential-source names only. Secret values are never shown or written.
- **Exit**: leave the TUI.

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

Keyboard and mouse input are supported when the terminal exposes mouse events. Primary mouse clicks activate selectable menu entries. Terminal emulators, SSH clients, and multiplexers can differ in mouse-event behavior.

Common keys:

- Arrow keys: navigate
- Enter: activate/confirm
- Space: toggle
- `a`: select all where offered
- `n`: select none where offered
- Escape: back/cancel
- `q`: quit where offered

## Entry points

| Command | Role |
| --- | --- |
| `python scripts/setup.py` | Source-tree Setup TUI |
| `python scripts/tui.py` | Same package TUI compatibility entry point |
| `flossware-setup` | Package console script |
| `flossware-ai setup` | Managed-install Setup TUI |
| `flossware-ai tui` | Same managed Setup TUI |

## Privacy

Generated project files (`.flossware-ai.json`, `ai_config.py`, and agent instruction files) never contain credential values. Active-project state stores only non-secret metadata required to reopen the configured project.

Credential references identify sources such as environment variables. They do not contain the corresponding secret values.

## Screenshots

Files under `screenshots/` are documentation renderings, not claims of pixel-identical terminal captures. They are kept synchronized with the current control-center/wizard flow and are labeled as representative where appropriate.
