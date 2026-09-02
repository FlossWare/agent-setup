# Crush setup

`flossware-ai setup crush --free-only` provisions the Crush integration and starts the user-level FlossWare gateway service.

The command is idempotent and keeps Crush integration setup in `agent-setup`; `crush-demo` consumes this setup rather than duplicating it.
