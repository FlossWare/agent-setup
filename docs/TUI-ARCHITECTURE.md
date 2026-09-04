# TUI Architecture

Low-level curses input and reusable widget interaction belong in `curses-tui`; `agent-setup` owns setup-specific workflows and state.

The application integration layer consumes the shared `curses-tui` input, menu, geometry, and window primitives. Mouse/input regression behavior is covered in the application test suite while reusable behavior remains in `curses-tui`.

The language-neutral `FlossWare/tui-schema` 1.0 contract is the next integration boundary: `agent-setup` should consume the canonical JSON contract through `curses-tui` rather than defining a second schema or renderer contract.
