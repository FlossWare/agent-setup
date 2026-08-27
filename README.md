# coding-agent-setup

FlossWare's shared control plane for configuring coding agents and independently usable FlossWare AI capabilities. Supported installation targets include Fedora/RHEL derivatives, Debian-family Linux, FreeBSD, Windows, and Termux.

## Quick start

A normal user does **not** need to clone this repository. The bootstrap installer downloads managed artifacts/source archives and installs the control plane into the user's FlossWare directory:

```bash
curl -fsSL https://raw.githubusercontent.com/FlossWare/coding-agent-setup/main/install.sh | bash
flossware-ai tui
```

The control-plane CLI is also available non-interactively:

```bash
flossware-ai config show
flossware-ai config explain optimization.population
flossware-ai config validate
flossware-ai demo
```

The managed runtime lives at `~/.flossware/ai` (or the platform-appropriate user-data location). Reinstallation and cleanup never require manually deleting that directory.

```bash
./scripts/install.sh --reinstall
./scripts/install.sh --clean
```

For a local checkout, contributor build, or explicit source fallback, use the repository's `scripts/install.sh` and set `FLOSSWARE_USE_SOURCE=true` when source checkout behavior is desired.

## Configuration contract

Configuration is **layered and language-neutral**. TOML is the human-editable format; Python decorators or other language metadata are optional adapters, not the contract.

Configuration values resolve in this order, from lowest to highest priority:

```text
built-in defaults
      ↓
system → user → profile → project → environment → CLI
      ↓
effective configuration
      ↓
policy validation + ordering
      ↓
TUI / CLI / agent execution / optimization
```

A directory binding is **not a separate value-merge layer in v1**. Instead, the current directory is matched against centrally stored directory bindings, using the most-specific matching path, to select the profile before the normal configuration layers are resolved. This keeps directory-specific policy without putting `.flossware` state into source trees.

The contract provides schema validation, declarative `before`/`after` ordering with cycle detection, component registration, provenance, and post-resolution policy enforcement.

See [`docs/configuration-contract.md`](docs/configuration-contract.md).

## Profiles and directory bindings

Profiles are user-defined policy boundaries stored centrally under the FlossWare user-data directory. The public repository ships only a neutral `default` profile. Users can create profiles such as `personal`, `work`, `redhat`, `government`, `client-a`, or any other appropriate name.

A directory binding associates a directory tree with a profile. Bindings do not create files in the target directory. When multiple bindings match, the **longest/more-specific path wins**.

For example:

```text
~/Development/redhat                       → redhat
~/Development/redhat/scm/gitlab            → redhat
~/Development/redhat/.../disseminator      → redhat-cost-conscious
```

The same resolved profile is intended to drive configuration inspection and agent launch from that directory.

## Launching coding agents

The control plane can launch supported coding agents using the effective profile for the current directory:

```bash
flossware-ai run claude
flossware-ai run crush
```

Direct agent aliases are also available where installed:

```bash
flossware-ai claude
flossware-ai crush
```

The agent registry covers Claude Code, Crush, Cursor, OpenCode, Codex, Aider, Cline, Roo Code, Gemini CLI, GitHub Copilot, Windsurf, Amazon Q Developer, and Kiro. Actual integration capability is detected per agent/platform.

Git is **not required** for normal use. A directory can be configured and used as an AI working directory even when it is not under source control.

## Optimization

The setup package includes a deterministic, standard-library-only optimization engine used by the offline showcase. It demonstrates genetic search over bounded candidates and Thompson Sampling over candidate arms. The production integration path can delegate to FlossWare's `genetic-optimizer-ai` and `model-router-ai` packages when those optional capabilities are installed.

```bash
flossware-ai demo
```

The demo requires no credentials, network, or paid APIs and is deterministic for reproducible testing.

## Installation model

The consumer path is artifact-first and repository-independent:

```text
curl bootstrap
    |
    +--> managed package/artifacts
    |
    +--> coding-agent-setup source archive
    |
    +--> managed install
    |
    +--> flossware-ai tui / config / demo / doctor / dogfood
```

No Git clone is required for a normal installation. `FLOSSWARE_USE_SOURCE=true` is an explicit contributor/developer escape hatch for source checkout and editable installation.

## TUI

`flossware-ai tui` is a terminal-based operator interface with keyboard and mouse support. It provides configuration, profile, directory-binding, agent, theme, and diagnostic workflows. Hovering a menu row updates the contextual status line. Clicking performs the same action as selecting and confirming that row. Status text is catalog-derived and never renders credential values.

Available themes include Turbo, dBASE IV, Classic DOS, and monochrome. Theme selection is stored centrally and does not modify project directories.

![FlossWare AI Setup TUI preview](screenshots/tui-preview.svg)

The screenshot is a representative terminal-state rendering, not a desktop GUI mockup. Actual appearance varies with terminal size, font, and platform.

## Cross-cutting behavior and ordering

Cross-cutting decorators/interceptors/middleware are explicitly enabled and can be configured through the common contract. Ordering is declarative:

```text
Models → Optimization → Capabilities → Validation
```

The resolver supports `before` and `after` constraints, stable ordering, and cycle rejection. The same contract can be consumed by Python decorators or another language adapter.

## Privacy and credential safety

Managed configuration is **non-identifying and secret-free**. API keys, OAuth tokens, passwords, cookies, email addresses, employee/customer identifiers, phone numbers, and other PII are not persisted in profiles, generated agent files, logs, or diagnostics.

Credential references identify where a secret is obtained; they are not secret values.

## Documentation

- [`docs/operator-guide.md`](docs/operator-guide.md) — canonical operator workflow
- [`docs/configuration-contract.md`](docs/configuration-contract.md) — layered contract, schema, provenance, policy, and ordering
- [`docs/demo.md`](docs/demo.md) — deterministic optimization showcase
- [`docs/cli-reference.md`](docs/cli-reference.md) — CLI commands
- [`docs/setup-tui.md`](docs/setup-tui.md) — TUI behavior, themes, mouse, and status line
- [`docs/architecture.md`](docs/architecture.md) — control-plane architecture
- [`docs/profile-schema.md`](docs/profile-schema.md) — profile schema, bindings, and policy boundaries
- [`docs/discovery.md`](docs/discovery.md) — provider/account/model discovery
- [`docs/troubleshooting.md`](docs/troubleshooting.md) — recovery guidance
- [`docs/privacy.md`](docs/privacy.md) — secret/PII handling
- [`docs/SECURITY.md`](docs/SECURITY.md) — security policy

## Related repositories

- [FlossWare/loom-ai](https://github.com/FlossWare/loom-ai)
- [FlossWare/model-router-ai](https://github.com/FlossWare/model-router-ai)
- [FlossWare/genetic-optimizer-ai](https://github.com/FlossWare/genetic-optimizer-ai)
- [FlossWare/coding-agent-ai](https://github.com/FlossWare/coding-agent-ai)

## License

MIT
