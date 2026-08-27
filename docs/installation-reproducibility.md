# Installation reproducibility

Consumer installs resolve setup content from `FLOSSWARE_RELEASE_REF` (default: `main`).

- **Development / tracking branch:** leave the default or set `FLOSSWARE_RELEASE_REF=main`.
- **Pinned install:** set `FLOSSWARE_RELEASE_REF` to a tag or full commit SHA once releases exist.
- **Windows and Unix** both honor the same variable; Windows may use a codeload archive when Git is not installed.

Record the resolved ref after install for audit. For a Git checkout, use `git -C "$INSTALL_ROOT/coding-agent-setup" rev-parse HEAD`. For an artifact-first install, which may not contain `.git`, record the `FLOSSWARE_RELEASE_REF` value used for the installation and retain the installer/archive metadata with the deployment record.
