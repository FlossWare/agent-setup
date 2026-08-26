# CLI reference

`flossware-ai` is the supported installed CLI. The repository's setup behavior is implemented by the same `flossware_setup` package used by the TUI.

## Core commands

| Command | Purpose |
|---|---|
| `flossware-ai tui` | Open the interactive Setup Control Center |
| `flossware-ai config show` | Show effective layered configuration |
| `flossware-ai config explain <key>` | Show configuration provenance for a key |
| `flossware-ai config validate` | Validate effective configuration and policy |
| `flossware-ai config order show` | Show persisted menu/component order |
| `flossware-ai config order move <item> up` | Move an item up if constraints allow it |
| `flossware-ai config order move <item> down` | Move an item down if constraints allow it |
| `flossware-ai demo` | Run the deterministic configuration/optimization showcase |
| `flossware-ai agents` | List registered coding agents and their detected/configurable state |
| `flossware-ai agents setup <id>` | Configure a specific coding agent |
| `flossware-ai components` | List FlossWare capabilities |
| `flossware-ai components <id>` | Inspect/configure a specific capability |
| `flossware-ai accounts` | Inspect configured account metadata and status |
| `flossware-ai accounts --verify` | Verify configured credential sources where supported |
| `flossware-ai models --refresh` | Refresh provider/model discovery |
| `flossware-ai providers` | List provider discovery state |
| `flossware-ai runtime list` | List supported execution backends |
| `flossware-ai runtime status` | Show runtime health/version state |
| `flossware-ai runtime select podman` | Select Podman explicitly |
| `flossware-ai runtime select docker` | Select Docker explicitly |
| `flossware-ai runtime auto` | Return to automatic runtime selection |
| `flossware-ai doctor` | Run environment and runtime diagnostics |
| `flossware-ai dogfood --strict` | Run the real-machine setup acceptance gate |

Run `flossware-ai <command> --help` for command-specific options exposed by the installed version.

## Configuration lifecycle

Configuration is layered in this order: built-in defaults, system, user, profile, project, environment, and CLI. Higher layers override only values they explicitly provide. Policy is evaluated after resolution. See [`configuration-contract.md`](configuration-contract.md).

The public persistent menu order is stored under `~/.flossware/ai/menu-order.json`. It contains only component IDs and ordering metadata, never credentials or PII.

## Interactive reordering

The TUI exposes **Configuration Contract**. It shows the active policy and menu order. Use arrow keys or mouse to select an item, `Ctrl-P` to move it up, `Ctrl-V` to move it down, and Enter to save. Moves that violate declared `before`/`after` constraints are rejected.

The CLI provides the same operation:

```bash
flossware-ai config order show
flossware-ai config order move optimization up
flossware-ai config order move validation down
```

The persisted result is validated again on load, so a malformed or incompatible order falls back to the safe default order.

## Installation lifecycle

```bash
./scripts/install.sh
./scripts/install.sh --reinstall
./scripts/install.sh --clean
```

`--reinstall` refreshes the managed installation without deleting native agent credentials. `--clean` removes only managed FlossWare AI state; it must not remove project instruction files, native credentials, or provider credentials.

## Validation

`doctor` is an environment inventory/diagnostic command. `dogfood` is the acceptance gate for the setup implementation. Strict dogfood requires Claude Code and Crush to be installed and discoverable on `PATH`; credentials are never printed.

For source-tree development:

```bash
python scripts/dogfood.py
python scripts/dogfood.py --strict
```

For an installed runtime:

```bash
flossware-ai dogfood --strict
```
