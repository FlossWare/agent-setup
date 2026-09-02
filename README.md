# agent-setup

FlossWare's shared control plane for configuring agents and independently usable FlossWare AI capabilities. Supported installation targets include Fedora/RHEL derivatives, Debian-family Linux, FreeBSD, Windows, and Termux.

## Quick start

A normal user does **not** need to clone this repository. The bootstrap installer downloads managed artifacts/source archives and installs the control plane into the user's FlossWare directory:

```bash
curl -fsSL https://raw.githubusercontent.com/FlossWare/agent-setup/main/install.sh | bash
flossware-ai tui
```

The control-plane CLI is also available non-interactively:

```bash
flossware-ai config show
flossware-ai config explain optimization.population
flossware-ai config validate
flossware-ai demo
```

The canonical persistent AI state root is `~/.FlossWare/ai`. Set `FLOSSWARE_AI_HOME=/absolute/path` to override it for tests, CI, containers, or unusual installations. Reinstallation does not require manually deleting the state root, and migration from the historical `~/.flossware/ai` root is non-destructive and credential-safe.

For a local checkout, contributor build, or explicit source fallback, use the repository's `scripts/install.sh` and set `FLOSSWARE_USE_SOURCE=true` when source checkout behavior is desired.

## Profiles and directory bindings

Profiles are stored centrally under the canonical FlossWare AI state root. The public installation ships only the provider-neutral `default` profile; organization-specific examples are not installed as built-ins.

A directory binding selects the profile used while operating in that directory. Bindings are stored centrally, not as `.flossware` files in projects. The most specific matching directory wins.

```bash
flossware-ai config current
flossware-ai config bindings
flossware-ai config show
flossware-ai config validate
```

Git is optional. A directory does not need to be a Git repository to use profiles or launch an agent.

## Launching agents

The control plane resolves the current directory's profile before launching an agent:

```bash
flossware-ai run claude
flossware-ai claude
flossware-ai crush
```

The selected profile is exported to the launched process along with the effective configuration and provenance. Work profiles can restrict which agent executables are permitted.

## Crush setup

The same control plane can provision the FlossWare Crush integration used by the Crush demo. This keeps environment setup in one place rather than duplicating installer logic in `crush-demo`:

```bash
flossware-ai setup crush --free-only
```

The command installs or updates `agent-ai` in the managed environment, installs Crush when needed, provisions the FlossWare local OpenAI-compatible gateway and user service, configures Crush for the `flossware` model, and creates the `flossware-crush` and `flossware-models` convenience commands. The current Crush integration is intentionally free/local-only.

## Configuration precedence

In v1, directory bindings select a profile; they are not an independent value-merge layer. Effective values are resolved in this order:

```text
defaults → system → user → profile → project → environment → CLI
                                      ↓
                                    policy
```

The configuration contract is versioned as `flossware.config.v1`. Unsupported or unsafe values are excluded rather than silently becoming effective configuration.

## Themes

The TUI supports selectable themes, including Turbo and dBASE-style presentation. Theme state is stored centrally under the canonical FlossWare AI state root.

```bash
flossware-ai tui --theme turbo
flossware-ai tui --theme dbase4
```

## Documentation

See `docs/` for the operator guide, profile schema, configuration contract, installation/reproducibility guidance, state-root and migration policy, and architecture decisions. See [`docs/state-root.md`](docs/state-root.md) for the persistent-state contract.
