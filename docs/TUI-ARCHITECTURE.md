# TUI Architecture

Low-level curses input and reusable widget interaction belong in `curses-themes`; `agent-setup` owns setup-specific workflows and state.

PR #89 is intentionally retained as the application integration/regression layer while reusable mouse/input behavior is extracted to `curses-themes`.
