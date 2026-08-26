# Profile schema

Profiles are local policy boundaries. The public repository ships only the neutral `default` profile. Users may create any local profile name, including `personal`, `work`, `redhat`, `government`, or client-specific names. Local organizational profiles should not be committed to this public repository.

## Shipped default

```toml
profile = "default"

[model_policy]
allowed_providers = ["*configured*"]
credential_env = []
allow_local_models = true
allow_unconfigured_providers = false

[flossware]
router = true
resilience = true
consensus = true
evaluation = true
observability = true
security = true
```

The default policy allows configured providers, permits local models, and refuses unconfigured providers. No secret value belongs in a profile.

## Policy fields

### `profile`

Human-readable local profile identifier. It should match the profile filename stem and contain no secrets or personal identifiers.

### `[model_policy]`

- `allowed_providers`: provider IDs or policy selectors permitted by the profile. `*configured*` means providers that have a configured credential source.
- `credential_env`: environment-variable names that may be referenced as credential sources. Values are never stored here.
- `allow_local_models`: whether local models may be selected.
- `allow_unconfigured_providers`: whether providers without configured credentials may be offered.

### `[flossware]`

Boolean capability-policy switches for the shared FlossWare components. Current documented switches are `router`, `resilience`, `consensus`, `evaluation`, `observability`, and `security`.

## Precedence

The active profile establishes the workload policy. TUI/component settings can explicitly enable or disable supported component behavior, but must remain within the active profile's policy boundary. Agent-native credentials remain owned by the agent and are not copied into profiles.

## Security invariant

Profiles contain policy and references only. API keys, OAuth tokens, passwords, cookies, email addresses, employee/customer identifiers, and other PII must never be persisted in profile files.

## Examples

```text
~/.flossware/ai/profiles/
├── default.toml
├── personal.toml
└── work.toml
```

A work profile may restrict models to an organization's approved providers. A personal profile may permit a broader set of free or local models. The public setup code does not hard-code either policy.
