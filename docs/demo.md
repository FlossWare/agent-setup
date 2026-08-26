# Holy Crap Demo

The intended showcase command is:

```text
flossware-ai demo
```

The demo must be deterministic, offline-safe, and cost-free. It demonstrates the configuration contract before it demonstrates optimization.

## Demo sequence

1. Load the built-in configuration contract.
2. Resolve layered configuration and display provenance.
3. Display ordering constraints and the resolved menu order.
4. Validate the resulting configuration and policy.
5. Show a synthetic optimization search space.
6. Run deterministic genetic optimization.
7. Run deterministic Thompson Sampling over candidate configurations.
8. Display the selected configuration, reward, and decision explanation.

A future `--live` mode may use real agents and models, but the default demo must never require credentials, network access, or paid APIs.

## Design goal

The demo should prove that the same declarative contract drives configuration, ordering, policy validation, optimization, and explainability. It should not be a static screenshot masquerading as functionality.
