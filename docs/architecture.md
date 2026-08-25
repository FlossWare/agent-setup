# Setup architecture

The interactive setup implementation separates domain data, persistence,
credentials, artifact generation, and the TUI into maintainable modules.

```
scripts/setup.py                 thin compatibility entry point
flossware_setup/
  catalog.py                     agents, capabilities, providers, budgets
  config.py                      Config model, project state load/review
  credentials.py                 env presence checks only
  artifacts.py                   generated project files and pip package refs
  installer.py                   capability package installation
  tui/
    __init__.py                  public main/run exports
    app.py                       application lifecycle / navigation
    screens.py                   welcome, review, credentials, wizard, build
    widgets.py                   header, menu, text input, palette
    input.py                     keyboard/mouse event helpers
```

## Entry points

| Command | Role |
| --- | --- |
| `python scripts/setup.py` | Source-tree TUI (compatibility) |
| `flossware-setup` | Package console script (`flossware_setup.tui:main`) |
| `flossware-ai setup` | Managed-install launcher for the same setup TUI |
| `flossware-ai tui` | Managed-install control-panel TUI (`scripts/setup_tui.py`) |

`flossware-ai` is installed by `scripts/install.sh` into the managed runtime.
`flossware-setup` is available after `pip install` of this package.

## Invariants

- **Thirteen agent integrations** are defined once in `catalog.AGENTS`.
- **Neutral default profile**: public baseline is `default`. Organizational
  profiles are local policy, not hard-coded application logic in this package.
- **Credentials**: modules may report whether a provider env var is set. They
  never persist or display secret values.
- **Control center**: Review Current Configuration, Configure / Change Setup,
  Provider Credentials, Exit.
- **Mouse and keyboard**: selection screens support both. Keyboard-only
  terminals remain fully usable.
- **Review screen** reads **persisted** project state (`.flossware-ai.json`),
  not only in-memory wizard selections.

## Tests

```bash
pytest -q
python scripts/dogfood.py
python scripts/setup.py --help
```
