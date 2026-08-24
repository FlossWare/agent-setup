# Security and credential handling

`coding-agent-setup` generates agent instructions and configuration. It is not a secret store and must never turn provider credentials into project artifacts.

## Credential boundary

- Provider credentials are optional configuration inputs.
- The setup tool may detect whether supported credential environment variables are set, but must never print their values.
- Generated `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.flossware-ai.json`, and `ai_config.py` must contain no credential material.
- Do not persist API keys in source control, templates, manifests, screenshots, logs, or generated documentation.
- Prefer OS credential stores, CI secret stores, provider-specific secret managers, or the routing layer's secure credential mechanism.
- Environment variables are supported for users who intentionally choose them. Treat the environment as sensitive and do not copy it into generated files.

## Agent/runtime boundary

`coding-agent-setup` prepares configuration. `coding-agent-ai` is responsible for untrusted worker execution, command policy, filesystem confinement, and credential isolation during agent work. Setup configuration must not weaken those runtime controls.

## Installer safety

The installer:

1. Requires Python 3.11+ and Git.
2. Fails with a non-zero exit code when required dependencies fail.
3. Does not claim successful installation after partial failure.
4. Supports an explicit `FLOSSWARE_RELEASE_REF` for reproducible release/tag installation.
5. Never writes provider credentials into the target project.
6. Reports credential status as metadata only.

Inspect `scripts/install.sh` before using a remote bootstrap command. For production or enterprise use, prefer a pinned release and a reviewed copy of the installer.

## Security invariant

Credential values must never cross into generated project artifacts, logs, screenshots, or manifests. Only configuration and capability metadata may cross from setup into generated project artifacts.
