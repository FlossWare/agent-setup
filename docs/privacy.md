# Privacy and secret-handling invariant

FlossWare AI setup configuration is intentionally **non-identifying and secret-free**.

## Never persist

The managed FlossWare state, profiles, generated agent configuration, MCP configuration, logs, and declarative policy must never persist:

- API keys or API key values
- OAuth access or refresh tokens
- passwords or cookies
- email addresses
- legal names or usernames when they identify a person
- employee/customer identifiers
- phone numbers
- other PII

Credential values remain in the environment, native OS credential store, or the credential system owned by the relevant coding agent/provider.

## Account identifiers

Multiple accounts for the same provider are supported using opaque, user-chosen local aliases. An alias is an identifier for configuration, not a person's identity.

Good:

```text
openai-personal-1
openai-alt-2
groq-free-1
```

Bad:

```text
scot.floess@redhat.com
Scot Floess
employee-12345
```

The setup UI and CLI should reject or warn on obvious identity-bearing account labels. The invariant is stronger than the warning: account labels are never treated as proof of provider identity.

## Profiles

Profiles express policy and capability boundaries. They do not represent human identities. `personal` and `redhat` are policy names, not storage locations for personal or corporate identity data.

A profile may reference a credential mechanism by a non-secret reference such as `environment:OPENAI_API_KEY`. This is a reference to where the secret is obtained, not the secret itself.

## Logs and diagnostics

Diagnostics may report states such as `configured`, `verified`, `discovered`, `available`, `ready`, `active`, and `blocked`. They must not print credential values or identifying account metadata.

When debugging provider authentication, redact request headers, authorization fields, environment values, and provider response fields that contain identity or secret material.

## Generated agent files

Generated `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, and equivalent files contain configuration and behavioral instructions only. They must not contain API keys, tokens, email addresses, employee identifiers, or other PII.

## Tests

Tests should use synthetic provider/account identifiers and fake credentials. Secret-scanning and privacy tests should fail if obvious credential or identity-bearing values are emitted into managed configuration, generated files, or diagnostics.

## Automated regression coverage

- `tests/test_privacy_secrets.py` — secret key/value scanners, state whitelist, artifact generation with live env secrets
- `tests/test_policy_invariant.py` — policy applied after resolve; budget/provider overrides cannot escape policy
- Existing package tests assert `credential_values_written` is always false and env secret values never appear in generated files
