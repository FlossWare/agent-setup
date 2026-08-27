# TUI themes

Selectable visual themes for the FlossWare setup IDE. Theme choice is stored under the **central** FlossWare state directory (`~/.flossware/ai/theme`), never in project trees.

## Available themes

| Id | Label |
|----|--------|
| `turbo` | Turbo C++ inspired (blue/cyan), **default** |
| `dbase4` | dBASE IV inspired (green phosphor) |
| `classic` | Classic DOS (white on black) |
| `monochrome` | Modern / default terminal colors |

The built-in default is **Turbo C++ inspired**. A missing theme file and the `default` alias both resolve to `turbo`.

Aliases: `modern` → `monochrome`; `default` → `turbo`; `dbase` / `dbase-iv` → `dbase4`.

## Selection

- IDE menu: **Theme** (applies immediately without restart when practical)
- CLI: `flossware-ai tui --theme turbo`
- API: `save_theme("dbase4")` / `load_theme()`

## Adding a theme

`tui/themes.py` is the **only** source of theme ids (`THEME_NAMES` is derived from `_THEME_PAIRS`).

1. Add pair definitions in `flossware_setup/tui/themes.py` (`_THEME_PAIRS`).
2. Add a label in `THEME_LABELS`.
3. Extend tests in `tests/test_themes.py`.

`config_control.THEMES` re-exports `THEME_NAMES` and must not define its own list.

Terminals with fewer than 8 colors fall back to default pairs automatically.
