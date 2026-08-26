# Holy Crap Demo

The showcase command is now implemented:

```bash
flossware-ai demo
```

The demo is deterministic, offline-safe, and cost-free. It demonstrates the configuration contract before optimization.

## Demo sequence

1. Load the built-in configuration contract.
2. Resolve layered configuration and display provenance.
3. Display ordering constraints and the resolved menu order.
4. Validate schema and policy.
5. Show a synthetic optimization search space.
6. Run deterministic genetic optimization.
7. Run deterministic Thompson Sampling over candidate configurations.
8. Display the selected configuration and decision metrics.

The implementation uses only the Python standard library. It does not require credentials, network access, model APIs, or paid services.

## CLI examples

```bash
flossware-ai config show
flossware-ai config explain optimization.population
flossware-ai config validate
flossware-ai demo
```

## Production integration

The standalone demo engine is intentionally small and deterministic. Real workloads can integrate the same configuration contract with FlossWare's `genetic-optimizer-ai` and `model-router-ai` capabilities. The contract remains responsible for policy, precedence, provenance, and ordering, while optimization components operate inside the permitted search space.

A future `--live` mode may use real agents and models, but the default demo must remain credential-free and deterministic.

## Acceptance requirements

The demo must remain deterministic for a fixed Python version/seed, return exit code 0, report policy validation as `PASS`, and never print credentials or PII. The test suite includes a repeat-run equality check.
