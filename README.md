# loom-setup

**Loom installation and runtime configuration for FlossWare.**

`loom-setup` owns installation, environment configuration, backend selection, provider/model-gateway configuration, credentials, endpoints, validation, and deployment-oriented setup for Loom.

It does **not** implement Loom execution and it does not configure individual coding clients. Those responsibilities belong to `loom-ai` and `loom-client-setup` respectively.

## Boundary

```text
loom-setup
    │
    ├── install Loom
    ├── configure runtime/backends
    ├── configure model-gateway resources
    ├── manage setup-time credentials/policy
    └── validate effective configuration
             │
             ▼
          loom-ai
             ▲
             │
   loom-client-setup
```

## Configuration

Setup configuration describes the effective Loom deployment, including selectable storage, queue, graph, embedding, search, and model-gateway implementations. Runtime execution state remains owned by Loom.

Provider credentials and secrets are setup/runtime concerns and must not be embedded in Worker configuration, Intent, evidence, provenance, or MCP responses.

## External clients

Client-specific configuration is intentionally outside this repository. `loom-client-setup` configures Crush, Claude Code, Codex, Cursor, and other clients to consume an already configured Loom instance.

## Migration note

This repository replaces the former `agent-setup` boundary. New documentation, commands, package names, and references should use **Loom** terminology. Historical `agent-ai`/`agent-setup` references are migration compatibility only.

## Development

Use the repository's installer, tests, and validation tooling for development. Setup should remain independently usable without requiring an external coding client.

## License

MIT
