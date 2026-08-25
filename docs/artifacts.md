# Artifact-first installation

FlossWare setup follows the engineering-standard rule that source and configuration are authoritative and build artifacts are reproducible derived outputs.

## Installation order

For a component release, setup follows:

```text
compatible released artifact
        |
        +-- available --> install artifact
        |
        +-- unavailable --> explicit source fallback
        |
        +-- impossible --> actionable failure
```

A normal consumer installation should not clone a Git repository merely to build a wheel when a compatible released artifact exists.

## Why `/tmp` appears during source installs

Python packaging tools commonly create temporary directories such as `/tmp/pip-install-*` while cloning and building source distributions. Those directories are ephemeral build machinery, not FlossWare state.

The managed FlossWare environment is persistent under the user FlossWare directory. A source-build fallback may use `/tmp` internally, but it must not depend on files remaining there after installation.

## Reinstall and cleanup

The installer owns the managed installation and provides lifecycle operations such as reinstall and clean. Users should not need to manually remove `/tmp/pip-*` directories or the managed FlossWare directory to recover from an installation.

Cleanup must not remove credentials, agent-native authentication, or unrelated project files.

## Release expectations

A distributable component should provide a reproducible build and release artifact appropriate to its language/runtime. Python projects should publish wheels and source distributions when appropriate. CI should validate installation in a clean environment before a release is considered consumable.

Artifact registries are distribution mechanisms, not sources of truth. Registry choice may vary by deployment.

## Local development

Editable/source installs remain supported for contributors. They are deliberately different from the normal consumer installation path and are useful when developing a FlossWare component itself.
