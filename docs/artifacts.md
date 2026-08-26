# Artifact-first installation

FlossWare setup is designed so a normal consumer can start without cloning the repository.

## Normal consumer path

Use the stable bootstrap script:

```bash
curl -fsSL https://raw.githubusercontent.com/FlossWare/coding-agent-setup/main/install.sh | bash
flossware-ai tui
```

The bootstrap downloads the installer and the installer then:

1. installs/uses the `coding-agent-ai` package artifact when available;
2. downloads the `coding-agent-setup` GitHub source archive for the selected release ref;
3. installs the setup package into the managed virtual environment;
4. creates the neutral `default` profile and managed CLI/TUI;
5. leaves native agent/provider credentials untouched.

**No Git clone is required for the normal consumer path.** The setup archive is downloaded as a tarball and unpacked into the managed installation. Git is not used to obtain the setup repository in this mode.

## Release and ref behavior

The bootstrap defaults to the repository `main` ref until a formal release/tag channel is introduced. `FLOSSWARE_RELEASE_REF` can select a branch/tag when operating a controlled deployment or testing a release candidate.

For production releases, the intended distribution model is:

```text
stable bootstrap
      |
      +--> compatible package artifact
      |
      +--> matching setup source archive/tag
      |
      +--> managed installation
```

The source archive is a distribution artifact of the repository, not a Git checkout. It does not create a `.git` directory in the managed installation.

## Explicit source fallback

Contributors who are developing the setup repository can deliberately opt into a Git checkout:

```bash
FLOSSWARE_USE_SOURCE=true ./scripts/install.sh
```

This is intentionally different from the consumer path. It exists for editable/source development and troubleshooting. Users should not need it to install or operate FlossWare AI.

## Why `/tmp` appears during installs

Python packaging tools commonly create temporary directories such as `/tmp/pip-install-*` while building packages. The bootstrap also uses a temporary directory while unpacking the setup archive. These directories are ephemeral build machinery, not FlossWare state.

The managed FlossWare environment is persistent under the user's FlossWare directory. Installation must not depend on temporary files remaining after the installer exits.

## Reinstall and cleanup

The installer owns the managed installation and provides lifecycle operations such as reinstall and clean. Users should not need to manually remove temporary directories or the managed FlossWare directory to recover from an installation.

Cleanup must not remove credentials, agent-native authentication, or unrelated project files.

## Packaging expectations

A distributable component should provide a reproducible build and release artifact appropriate to its language/runtime. Python projects should publish wheels and source distributions when appropriate. CI should validate installation in a clean environment before a release is considered consumable.

Artifact registries are distribution mechanisms, not sources of truth. Registry choice may vary by deployment.
