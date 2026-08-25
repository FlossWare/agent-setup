# FlossWare Cross-Cutting Decorators in the TUI

FlossWare cross-cutting behavior is explicitly opt-in. The configuration TUI exposes decorators as a **policy stack** around a provider-neutral capability, rather than asking users to edit Python decorator syntax.

This follows Engineering Standards ADR-0006: decorators/interceptors/middleware are mechanisms for cross-cutting behavior, while activation is explicit and provider/model selection remains separate.

## TUI model

Select **Components → Cross-Cutting Behavior** and choose a component or capability. The TUI presents:

- enabled/disabled state
- available decorators
- stack order
- per-decorator configuration
- policy/profile inheritance
- a short contextual description
- validation status

Example:

```text
Cross-Cutting Behavior

> Model Router
  ┌────────────────────────────────────────────────────────────┐
  │ [x] Retry              Retry transient provider failures   │
  │ [x] Circuit Breaker    Stop repeated failing calls        │
  │ [x] Observability      Emit logs, metrics and traces      │
  │ [ ] Evaluation        Evaluate selected requests          │
  │ [ ] Cache              Cache eligible responses            │
  │                                                            │
  │ Stack order                                                │
  │   1. Security / Policy                                    │
  │   2. Retry                                                │
  │   3. Circuit Breaker                                      │
  │   4. Observability                                        │
  │                                                            │
  │ Status: READY                                             │
  └────────────────────────────────────────────────────────────┘

 Retry
 Retries transient failures according to the active policy.
 Attempts: 3   Initial delay: 250ms   Max delay: 5s
 Backoff: exponential   Jitter: enabled
```

The user configures behavior, not implementation details. The runtime converts the policy into decorators/interceptors/middleware registration.

## Configuration shape

The persisted configuration should remain declarative:

```yaml
components:
  model-router:
    decorators:
      - id: retry
        enabled: true
        config:
          max_attempts: 3
          initial_delay_ms: 250
          max_delay_ms: 5000
          backoff: exponential
          jitter: true
      - id: circuit-breaker
        enabled: true
        config:
          failure_threshold: 5
          recovery_timeout_seconds: 30
      - id: observability
        enabled: true
        config:
          tracing: true
          metrics: true
          logging: true
```

The exact serialized format is implementation-defined, but it MUST preserve the same declarative semantics.

## Stack ordering

Ordering is configurable because cross-cutting policies can have materially different semantics. The TUI MUST warn when an ordering has a known policy consequence. It MUST NOT silently reorder user configuration.

Provider-specific behavior stays behind the provider contract. Decorator configuration MUST NOT select a provider, model vendor, or pricing tier.

## Profiles

Profiles can provide defaults for decorator policy:

```text
personal  → conservative cost-aware defaults
redhat    → organization-approved policies
```

Profile defaults are inherited, not copied into every component. A component may explicitly override an allowed setting. Secrets never belong in decorator configuration.

## Safety

The TUI MUST distinguish:

- **configured**: a decorator has a valid configuration
- **enabled**: the decorator is explicitly active
- **ready**: configuration validates against the capability contract
- **active**: it is currently installed in the runtime stack
- **blocked**: policy prevents activation

This is deliberately different from merely displaying a checkbox. Humans deserve to know whether the checkbox actually accomplished anything.
