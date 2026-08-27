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

A directory binding first selects the profile for the working directory. The selected profile then participates in the normal configuration merge. Directory selection is **not** a separate value-merge layer in configuration contract v1.

The value layers are, from lowest to highest priority:

```text
defaults → system → user → profile → project → environment → CLI → policy
```

TUI/component settings can explicitly enable or disable supported component behavior, but must remain within the active profile's policy boundary. Agent-native credentials remain owned by the agent and are not copied into profiles.

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

## Project state

Project state is stored centrally under `~/.flossware/ai/projects/<id>/state.json`, not inside the project tree. The control plane does not require or create a `.flossware` configuration file in the working directory.

### Schema (version 1)

| Key | Type | Description |
|-----|------|-------------|
| `schema_version` | number | State schema version (`1`) |
| `tool` | string | Always `FlossWare/coding-agent-setup` |
| `profile` | string | Active profile name (policy name, not a person) |
| `budget_policy_id` | string | Stable budget policy id from the catalog |
| `budget_policy` | string | Human-readable policy label |
| `monthly_budget` | number | Monthly ceiling in USD |
| `capabilities` | string[] | Selected capability ids |
| `agents` | string[] | Selected agent adapter ids |
| `providers` | object | Map of provider display name → **boolean presence only** |
| `provider_env_vars` | object | Map of provider display name → **environment variable name** (never values) |
| `credential_values_written` | boolean | Always `false`; credentials are never written by this tool |
| `theme` | string | TUI theme id |
| `repo_dir` | string | Absolute path of the configured project |

### Safe to persist

Agent ids, capability ids, budget policy ids, theme, provider presence flags, and env-var **names**.

### Must never be persisted

API keys, tokens, passwords, cookies, email addresses, legal names, employee ids, or any other secret/PII. Keys matching credential patterns (`api_key`, `token`, `secret`, …) are rejected. Loaders drop unknown keys so a hand-edited file cannot inject secrets into the TUI review screen.

### Example

```json
{
  "schema_version": 1,
  "tool": "FlossWare/coding-agent-setup",
  "profile": "default",
  "budget_policy_id": "medium",
  "budget_policy": "Medium",
  "monthly_budget": 50.0,
  "capabilities": ["coding-agent-ai"],
  "agents": ["claude-code"],
  "providers": {"OpenAI": true, "Anthropic": false},
  "provider_env_vars": {"OpenAI": "OPENAI_API_KEY", "Anthropic": "ANTHROPIC_API_KEY"},
  "credential_values_written": false,
  "theme": "dark",
  "repo_dir": "/home/you/projects/example"
}
```

## Directory bindings

Directory → profile mappings live in `~/.flossware/ai/profile-bindings.toml` (never in the project). Resolution uses **longest-specific-path** matching: the most specific binding that is a parent of (or equal to) the working directory wins; less-specific parent bindings are still visible in the TUI provenance view.

For example:

```text
~/Development/redhat                       → redhat
~/Development/redhat/scm/gitlab            → redhat
~/Development/redhat/.../disseminator      → redhat-cost-conscious
```

This makes both broad directory policies and narrow exceptions possible without modifying source trees.

### Path moves

`project_identity` is derived from the normalized absolute path. Use `migrate_project_state(old, new)` after a rename so configuration follows the directory; otherwise the new path starts with empty central state.
