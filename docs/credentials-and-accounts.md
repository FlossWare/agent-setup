# Accounts, identities, and credentials

FlossWare separates **provider**, **account**, **credential source**, **profile**, and **model**. This is required for users who have multiple accounts at the same provider.

```text
Profile
  |
  +-- Account: personal-openai
  |      +-- Provider: openai
  |      +-- Credential source: environment/native store
  |      +-- Models: discovered
  |
  +-- Account: work-openai
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

`~/.flossware/ai` is managed application state, not a secret vault. A credential reference may be stored there when necessary, but the secret itself remains in its authoritative credential store.

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

The `personal` profile is for personal accounts and services. The `redhat` profile is for organization-approved accounts and models. Profile policy is explicit. FlossWare does not infer employer approval from a provider, model name, or pricing tier.

## Agent credentials

Agent-native authentication remains owned by the agent. FlossWare can discover the existence and usable state of an agent account where the integration supports it, but does not copy or extract secret material merely to make another component convenient.
