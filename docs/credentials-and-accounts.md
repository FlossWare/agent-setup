# Accounts, identities, and credentials

FlossWare separates **provider**, **account**, **credential source**, **profile**, and **model**. This is required for users who have multiple accounts at the same provider.

```text
Profile
  |
  +-- Account: account-1
  |      +-- Provider: openai
  |      +-- Credential source: environment/native store
  |      +-- Models: discovered
  |
  +-- Account: account-2
         +-- Provider: openai
         +-- Credential source: environment/native store
         +-- Models: discovered
```

## Credential storage

FlossWare stores **references to credentials**, not credential values. Credential sources may be environment variables, native credential stores, or an agent-owned authentication mechanism.

Credential values must never be written to:

- generated `CLAUDE.md` or `AGENTS.md` files;
- `.cursorrules` or equivalent project instructions;
- FlossWare declarative configuration;
- logs;
- MCP definitions;
- source-controlled files.

`~/.FlossWare/ai` is managed application state, not a secret vault. A credential reference or presence metadata may be stored there when necessary, but the secret itself remains in its authoritative credential store.

## Persistent state ownership

The canonical FlossWare AI state root is:

```text
~/.FlossWare/ai/
```

Set `FLOSSWARE_AI_HOME=/absolute/path` to redirect the complete state root for tests, CI, containers, or unusual installations. Git repositories are not state stores and should not be used as an alternative location for provider, account, model, or profile configuration.

The state root may contain profiles, bindings, provider/account/model metadata, setup-managed Crush state, configuration, and runtime state. Disposable cache data belongs under `cache/` and can be regenerated.

Existing installations using the historical `~/.flossware/ai` root are migrated non-destructively during installation. Only supported configuration/state paths are copied, existing destination files are never overwritten, and credential stores are deliberately excluded. The legacy directory is left intact until the operator explicitly removes it.

## Multiple accounts

Account identifiers are unique within the FlossWare configuration even when providers are the same. The active profile determines which accounts are allowed. A model being visible through one account does not imply it is available through another account.

## Verification

The CLI and TUI use explicit states:

- `configured`: a credential source is present;
- `verified`: authentication/credential validation succeeded;
- `discovered`: provider returned account/model information;
- `available`: active policy permits use;
- `ready`: configuration, policy, credentials, and connectivity are valid;
- `active`: selected for the current workload;
- `blocked`: policy or platform prevents use.

Verification should be requested explicitly when it can cause provider API traffic.

## Profiles

Profiles are **user-defined policy boundaries**. The setup project intentionally does not hardcode an employer, organization, compliance regime, or personal identity as a required profile.

The public repository provides a neutral `default` profile as the starting point. Users can create additional profiles such as `personal`, `work`, `redhat`, `government`, `client-a`, or any other name appropriate to their environment.

A profile may define:

- permitted providers;
- permitted accounts;
- permitted models;
- whether local models are allowed;
- credential-source requirements;
- FlossWare capability defaults;
- organization-specific or project-specific policy.

The profile name itself has no built-in semantics. `work`, for example, does not automatically mean Red Hat, and `personal` does not automatically grant access to every provider. Policy is explicit configuration.

Organizational profiles should normally live in the user's local configuration or an organization's private configuration repository rather than in this public repository. This keeps the public project reusable while allowing strict enterprise and government policies without changing the setup engine.

## Agent credentials

Agent-native authentication remains owned by the agent. FlossWare can discover the existence and usable state of an agent account where the integration supports it, but does not copy or extract secret material merely to make another component convenient.
