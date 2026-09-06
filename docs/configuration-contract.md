# Configuration Contract

The Setup Control Center uses a language-neutral configuration model. TOML is the human-editable representation; implementations may expose the same schema through Python, Java, or other language adapters.

## Layers

**Implemented value-merge layers (v1 local provider):**

1. `defaults` — built-in safe defaults
2. `system` — `state_dir/system.toml` (machine-wide)
3. `user` — `state_dir/user.toml`
4. `profile` — selected operating profile (see directory bindings below)
5. `project` — project-local configuration in central FlossWare state (`projects/<id>/config.toml` when present)
6. `environment` — `FLOSSWARE_PROVIDER`, `FLOSSWARE_BUDGET_MONTHLY`, `FLOSSWARE_OPTIMIZATION_STRATEGY`
7. `cli` — applied by the CLI after merge (caller responsibility)

Only values present in a layer override lower layers. The resolver records provenance so an effective value can always be explained.

**Directory bindings are not a merge layer in v1.** Longest-specific-path bindings select which **profile** is loaded for a working directory; they do not inject independent key/value overrides into the merge. The winning binding path is recorded as `profile_source` / `FLOSSWARE_PROFILE_SOURCE`. Policy runs after the complete merge.

## Contract

A configurable item has a stable key, type, default, optional bounds or enum values, and a description. Ordering is a separate concern from value precedence and should use explicit `before`/`after` constraints with deterministic topological resolution.

Policy is evaluated after configuration resolution. A lower layer cannot use an override to escape a higher-level policy constraint.

## Credential references

Agent-setup manages **credential references**, not secret material. Profiles may persist which credential is needed and which secret backend should resolve it:

```toml
[credentials.anthropic_personal]
ref = "ANTHROPIC_API_KEY"
source = "environment"

[credentials.github_personal]
ref = "github/personal"
source = "keychain"
```

The `ref` is an opaque, secret-free locator. The `source` identifies the credential backend. Supported source identifiers are `environment`, `keychain`, `encrypted_file`, `vault`, `cloud_secret_manager`, and `external`.

The actual secret **must never be stored in the profile**. It remains in the selected credential backend and is resolved only when an authorized operation requires it. `flossware_setup.credential_refs` provides `set_credential_reference()`, `credential_references()`, and `remove_credential_reference()` for setup-managed profile state.

This deliberately supports the current environment-variable workflow without making `.bashrc` the architecture. For example, `ANTHROPIC_API_KEY` may remain in the user's environment today while the profile records only that `anthropic/personal` resolves through that environment variable. A future keychain, Vault, or cloud secret manager can replace the source without changing Loom tasks or model-router contracts.

### Credential boundary

> **Orchestrators and workers request authorized capabilities or account references. They do not manage raw secrets. Credential resolution is performed by the designated credential/provider layer under agent-setup policy.**

- **agent-setup** owns identities, accounts, credential references, authorization policy, budgets, and effective configuration.
- **Loom Orchestrator** requests capabilities and coordinates work; it must not retrieve, distribute, or persist provider secrets.
- **model-router** resolves provider/model/account selection and obtains an authorized credential for provider operations.
- **Credential providers** resolve the actual secret through a deployment-selected backend.
- **Workers** receive only the minimum authorized execution capability required for a task or lease.

Task payloads, leases, persisted task state, logs, normal telemetry, and ordinary API responses must not contain raw API keys, OAuth secrets, passwords, private keys, or equivalent credential material. Authorization should be evaluated before credential resolution wherever practical.

The account, credential-reference, capability, and secret-provider boundaries are language-neutral so future Java implementations can satisfy the same contracts and interoperate with the current Python implementation.

## Example

```toml
[optimization.genetic]
enabled = true
population_size = 50
generations = 100
mutation_rate = 0.05

[optimization.thompson]
enabled = true
algorithm = "beta-bernoulli"
prior_alpha = 1.0
prior_beta = 1.0
```

## Explainability

The resolver must expose provenance. The intended CLI is:

```text
flossware-ai config explain optimization.genetic.population_size
```

which shows each contributing layer and the effective value.

## Design rule

**Schema defines structure. Configuration defines values. Policy defines limits. Algorithms operate inside the resulting permitted search space.**

The contract deliberately does not make Python decorators authoritative. Decorators are optional registration conveniences that emit the same schema metadata.

## Ordering algorithm

Menu and pipeline ordering constraints use topological resolution with cycle detection:

1. Build a directed graph from `before` / `after` constraints registered by components.
2. Detect cycles; if any exist, raise `OrderingError` and keep the previous valid order.
3. Emit a total order that respects every constraint (stable among unconstrained peers).
4. Apply that order to resolver execution and TUI navigation.

Example constraint chain:

```text
providers → agents → models → optimization → validation
```

A user reorder that would violate a constraint is rejected; the UI keeps the last valid order.

## Policy evaluation timing

**Policy is evaluated after configuration resolution.** Layers merge first (higher priority wins). Then `Policy.validate` (or `ConfigResolver.resolve_with_policy`) enforces allowlists, numeric ceilings, and required flags. A project-layer override cannot escape a higher-level policy maximum or forbidden provider list—the effective map is still rejected when it violates policy.

## Shared provider interface (coding-agent-setup and Loom)

Contract id: `flossware.config.v1` (`SCHEMA_VERSION` in `flossware_setup.config_contract.provider`).

### Layer precedence

```text
defaults → system → user → profile → project → environment → CLI → policy
```

A directory binding selects the profile before this merge. It is **not** an additional value layer in v1.

Policy runs **after** merge. Lower-priority layers cannot escape profile/work restrictions.

### Python surface

```python
from flossware_setup.config_contract import (
    ConfigurationProvider,
    LocalConfigurationProvider,
    EffectiveConfiguration,
)

provider: ConfigurationProvider = LocalConfigurationProvider()
cfg: EffectiveConfiguration = provider.resolve("/path/to/workdir")
print(cfg.profile, cfg.values, cfg.provenance.get("provider"))
print(provider.explain("budget.monthly", "/path/to/workdir"))
```

`EffectiveConfiguration` is secret-free: credentials appear only as presence booleans.

### Ownership

| Domain | Owner |
|--------|-------|
| Profiles, bindings, themes | coding-agent-setup central state |
| Layer merge + policy | `config_contract` (shared) |
| Loom orchestration | Optional; may implement `ConfigurationProvider` without replacing local provider |
| Secret values | Environment / OS / agent stores only |

coding-agent-setup remains fully functional without Loom.

## Wire representation (language-neutral)

`EffectiveConfiguration.to_wire()` emits a JSON object suitable for inter-process use. Loom and other tools should treat this shape as the versioned contract surface (`contract_id` = `flossware.config.v1`), not the Python class.

```json
{
  "schema_version": 1,
  "contract_id": "flossware.config.v1",
  "directory": "/abs/path",
  "profile": "default",
  "profile_source": null,
  "values": {
    "provider": "auto",
    "budget.monthly": 0.0,
    "optimization.strategy": "hybrid"
  },
  "provenance": {
    "provider": [["defaults", "auto"], ["profile:default", "auto"]]
  },
  "credentials_present": { "OpenAI": true, "Anthropic": false },
  "theme": "turbo",
  "policy_violations": [],
  "extras": {}
}
```

### Policy semantics

- `resolve()` **does not raise** when policy fails.
- `policy_violations` lists human-readable reasons; empty means `policy_ok`.
- Work-profile restrictions are evaluated **after** layer merge so a project/user layer cannot bypass them by override alone.

### Secret handling

- `values` is intentionally restricted to a fixed v1 safe key set (`SAFE_VALUE_KEYS` in the Python binding: provider, budget, optimization, policy flags). Unknown keys are dropped and reported through `extras.excluded_keys` by the local provider. Expanding the set is a versioned contract change.
- Credential **values** never appear; only `credentials_present` booleans.
- Nested maps/lists are accepted only when the key's `allows_nested` flag is true and the nested structure is secret-free. All v1 keys set `allows_nested=false`.
- Each key's `value_type` (`string` | `number` | `boolean`) is enforced. Python `bool` is **not** accepted as a `number`. `None` is excluded.

## Expanding the values surface (process)

The v1 `values` map is intentionally small. Keys are registered in `flossware_setup/config_contract/keys.py` (`VALUE_KEY_SPECS`). Anything not in that registry is **excluded from `EffectiveConfiguration.values`** and, for the local provider, recorded in `extras.excluded_keys`.

### Currently supported v1 keys

| Key | Domain | Type |
|-----|--------|------|
| `provider` | provider | string |
| `budget.monthly` | budget | number |
| `optimization.population` | optimization | number |
| `optimization.strategy` | optimization | string |
| `policy.allow_personal_accounts` | policy | boolean |
| `policy.allow_unknown_providers` | policy | boolean |
| `policy.allow_provider_fallback` | policy | boolean |
| `policy.hard_budget` | policy | boolean |

### Adding a key without breaking Loom (backward-compatible v1 extension)

1. Add a `ValueKeySpec` with `introduced_in=1` (or the current schema version).
2. Update `tests/fixtures/config_contract/v1_supported_keys.json`.
3. Ensure the key is secret-free.
4. Emit provenance for the key from the resolver layers.
5. Document the key in this file and assign a domain owner in `DOMAIN_OWNERS`.
6. Ship conformance fixtures so Loom can assert support without importing Python.

Consumers **must ignore unknown keys** in `values` for forward compatibility.

### When to bump to `flossware.config.v2`

Require a new major contract id / schema version when any of the following hold:

- Removing or renaming a key
- Changing a key's value type or nested shape
- Allowing nested structures that could carry secrets
- Changing layer order or policy-after-merge semantics
- Changing the meaning of `policy_ok` / `policy_violations`

Additive keys alone do **not** require v2 if existing consumers ignore unknowns and fixtures are updated in lockstep.

### Conformance fixtures

Language-neutral fixtures live under `tests/fixtures/config_contract/`:

- `v1_supported_keys.json` — registry of allowed keys
- `v1_exclusion_behavior.json` — required drop behavior for secrets / unknown keys

Loom and coding-agent-setup can both load these JSON files in CI.

### Domain ownership (as the surface grows)

| Domain | Owner |
|--------|-------|
| provider, budget, optimization | coding-agent-setup profiles + shared contract |
| policy | `config_contract` (shared), enforced post-merge |
| agent | coding-agent-setup (future) |
| routing / context | Loom orchestration (future; never secrets) |
| credentials / accounts / credential references | coding-agent-setup + designated credential providers |
| secret values | Environment / OS / agent stores only — never the wire map |
