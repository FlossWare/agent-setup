# FlossWare AI state root

FlossWare AI setup has one canonical persistent state root:

```text
~/.FlossWare/ai/
```

The root is owned by `agent-setup` and is shared by setup-managed components. Git repositories remain source-code locations and are not persistent FlossWare state stores.

## Override

For tests, CI, containers, and unusual installations, set:

```bash
export FLOSSWARE_AI_HOME=/absolute/path/to/flossware-ai
```

The override redirects the complete FlossWare AI state root. It must be an absolute path.

## State categories

```text
~/.FlossWare/ai/
├── profiles/       # user policy profiles and bindings
├── providers/      # provider metadata where applicable
├── accounts/       # account metadata where applicable
├── models/         # model metadata where applicable
├── credentials/    # references/presence metadata only
├── config/         # setup configuration
├── crush/          # setup-managed Crush integration state
├── cache/          # disposable, regenerable data
└── state/          # runtime selections and markers
```

The exact physical layout may use existing implementation abstractions. The ownership boundary does not change: persistent AI state remains below the canonical root.

## Credentials

Credential values are never part of FlossWare configuration migration. API keys, OAuth tokens, passwords, and similar secrets remain in environment variables, native credential stores, or agent-owned authentication stores. State may contain references or presence metadata where the configuration contract requires it.

## Legacy migration

Older installations may use `~/.flossware/ai`. The installer migrates supported setup configuration/state into `~/.FlossWare/ai` without deleting the legacy directory.

Migration is:

- **non-destructive:** existing legacy state is retained;
- **idempotent:** destination entries are never overwritten;
- **selective:** only known setup-managed configuration/state paths are copied;
- **credential-safe:** credential stores are excluded from automatic migration;
- **conflict-aware:** an existing destination entry wins and the legacy entry remains available for operator review.

Do not manually delete the legacy directory until the new installation has been verified and all required account, provider, model, and profile metadata is present.

## Cleanup

It is safe to remove `cache/` when space is needed. Do not remove the whole `~/.FlossWare/ai` tree merely to clean Git repositories or rebuild installed code. Use the installer `--clean` operation when the managed installation itself is intentionally being removed; native agent/provider credentials are not touched.
