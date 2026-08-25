# Setup TUI

`flossware-setup`, `flossware-ai setup`, and `flossware-ai tui` all launch the same
implementation: `flossware_setup.tui`.

## Capabilities

- **Review Current Configuration** — reads persisted project state for the
  **active project** (last configured repository), not merely the process cwd.
- **Configure / Change Setup** — select coding agents, FlossWare capabilities,
  budget policy, and target repository (stable IDs, not list indexes).
- **Provider Credentials** — presence of environment variable **names** only;
  secret values are never shown or written.

## Profiles

The public repository ships a single neutral **`default`** profile
(`profiles/default.toml`). Users and organizations may create additional
local profile directories under the managed install root without requiring
them to be known by this repository. Personal/Red Hat profile assumptions
are not part of the public product.

## Entry points

| Command | Role |
| --- | --- |
| `python scripts/setup.py` | Source-tree setup TUI |
| `python scripts/tui.py` | Same package TUI (compat path) |
| `flossware-setup` | Package console script |
| `flossware-ai setup` | Managed-install setup TUI |
| `flossware-ai tui` | Same managed TUI (unified with setup) |

## Privacy

Generated project files (`.flossware-ai.json`, `ai_config.py`, agent instruction
files) never contain credential values. Active-project state stores only a
filesystem path under the managed root.
