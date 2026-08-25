# Setup architecture

The interactive setup implementation is split so domain data, persistence,
credentials, artifact generation, and the TUI are independently maintainable.

```
scripts/setup.py          thin compatibility entry point
flossware_setup/
  catalog.py              agents, capabilities, providers, budgets (static data)
  config.py               Config model, project state load/review (no secrets)
  credentials.py          env presence checks only
  artifacts.py            generated project files and pip package refs
  installer.py            capability package installation
  tui.py                  curses control center (keyboard + mouse)
```

## Invariants

- **Thirteen agent integrations** are defined once in `catalog.AGENTS`.
- **Neutral default profile**: the public repository ships `profile = "default"`.
  Personal, Red Hat, or other organizational profiles are local policy only.
- **Credentials**: modules may report whether a provider env var is set. They
  never read secret values into generated files or review screens.
- **Entry points**: `python scripts/setup.py` and `flossware-ai tui` remain the
  supported CLI/TUI paths. `scripts/setup.py` must stay a thin wrapper.
- **Control center**: the TUI always offers **Review Current Configuration**,
  Configure / Change Setup, Provider Credentials, and Exit.
- **Mouse and keyboard**: selection screens support both. Keyboard operation is
  never removed when mouse reporting is unavailable.

## Tests

```bash
pytest -q
python scripts/dogfood.py
```

TUI smoke coverage lives in `tests/test_entry.py` and imports the entry point
without requiring an interactive terminal.
