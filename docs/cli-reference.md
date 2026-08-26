# CLI reference

`flossware-ai` is the supported installed CLI. The repository's setup behavior is implemented by the same `flossware_setup` package used by the TUI.

## Core commands

| Command | Purpose |
|---|---|
| `flossware-ai tui` | Open the interactive Setup Control Center |
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
