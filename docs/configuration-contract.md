# Configuration Contract

The Setup Control Center uses a language-neutral configuration model. TOML is the human-editable representation; implementations may expose the same schema through Python, Java, or other language adapters.

## Layers

Layers are merged from lowest to highest priority:

1. `defaults` - built-in safe defaults
2. `system` - machine-wide configuration
3. `user` - user configuration
4. `profile` - selected operating profile
5. `project` - project-local configuration
6. `environment` - environment-derived values
7. `cli` - explicit command-line overrides

Only values present in a layer override lower layers. The resolver records provenance so an effective value can always be explained.

## Contract

A configurable item has a stable key, type, default, optional bounds or enum values, and a description. Ordering is a separate concern from value precedence and should use explicit `before`/`after` constraints with deterministic topological resolution.

Policy is evaluated after configuration resolution. A lower layer cannot use an override to escape a higher-level policy constraint.

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
defaults → system → user → profile → directory → project → environment → CLI → policy
```

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
|--------|--------|
| Profiles, bindings, themes | coding-agent-setup central state |
| Layer merge + policy | `config_contract` (shared) |
| Loom orchestration | Optional; may implement `ConfigurationProvider` without replacing local provider |
| Secret values | Environment / OS / agent stores only |

coding-agent-setup remains fully functional without Loom.
