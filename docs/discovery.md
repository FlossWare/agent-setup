# Provider, account, and model discovery

FlossWare treats a provider, an account, and a model as separate concepts.

```text
provider
  -> account
      -> advertised models
          -> active profile policy
              -> available
                  -> ready / active
```

## Lifecycle

1. **Configured**: a credential source is present for an account/provider alias.
2. **Verified**: credential validation succeeds where the provider supports verification.
3. **Discovered**: the authenticated provider exposes account/model information.
4. **Available**: discovered resources are permitted by the active profile.
5. **Ready**: credentials, policy, and connectivity checks pass.
6. **Active**: the resource is selected for the current workload.
7. **Blocked**: policy or platform prevents use.

A resource can be configured without being verified, and discovered without being available. These states are intentionally distinct so the TUI and diagnostics do not confuse authentication with policy.

## Multiple accounts

An account is an opaque local alias associated with a provider and a credential-source reference. Multiple accounts may use the same provider.

Example conceptual state:

```text
provider: openai
  account: openai-account-1 -> environment:OPENAI_API_KEY
  account: openai-account-2 -> native credential store
```

The actual secret values are never copied into managed configuration.

## Refreshing discovery

```bash
flossware-ai accounts --verify
flossware-ai models --refresh
flossware-ai providers
```

The TUI exposes the same information through its Credentials, Configure, and Review areas.

## Native agent authentication

A coding agent may have its own authentication and model catalog. FlossWare does not assume that a model visible to an agent is automatically usable by the FlossWare router. Router availability is determined independently by provider/account discovery plus the active profile.

## Privacy

Discovery metadata must remain non-identifying. Credential source references are safe metadata; credential values, tokens, cookies, passwords, email addresses, and other PII are not persisted in profiles, generated agent files, MCP definitions, logs, or diagnostics.
