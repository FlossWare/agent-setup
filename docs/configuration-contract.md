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
