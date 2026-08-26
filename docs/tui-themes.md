# TUI themes

Selectable visual themes for the FlossWare setup IDE. Theme choice is stored under the **central** FlossWare state directory (`~/.flossware/ai/theme`), never in project trees.

## Available themes

| Id | Label |
|----|--------|
| `turbo` | Turbo C++ inspired (blue/cyan) |
| `dbase4` | dBASE IV inspired (green phosphor) |
| `classic` | Classic DOS (white on black) |
| `monochrome` | Modern / default terminal colors |

Aliases: `modern` / `default` → `monochrome`; `dbase` / `dbase-iv` → `dbase4`.

## Selection

- IDE menu: **Theme** (applies immediately without restart when practical)
- CLI: `flossware-ai tui --theme turbo`
- API: `save_theme("dbase4")` / `load_theme()`

## Adding a theme

1. Add pair definitions in `flossware_setup/tui/themes.py` (`_THEME_PAIRS`).
2. Add a label in `THEME_LABELS`.
3. Append the id to `THEMES` in `flossware_setup/config_control.py`.
4. Extend tests in `tests/test_themes.py`.

Terminals with fewer than 8 colors fall back to default pairs automatically.
