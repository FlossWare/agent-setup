# Installation reproducibility

Consumer installs resolve setup content from `FLOSSWARE_RELEASE_REF` (default: `main`).

- **Development / tracking branch:** leave the default or set `FLOSSWARE_RELEASE_REF=main`.
- **Pinned install:** set `FLOSSWARE_RELEASE_REF` to a tag or full commit SHA once releases exist.
- **Windows and Unix** both honor the same variable; Windows may use a codeload archive when Git is not installed.

Every installation records non-secret provenance in managed state at:

`$FLOSSWARE_INSTALL_ROOT/state/install-metadata.json`

The metadata records the requested setup ref, source/archive mode, detected platform, active profile, and the fact that installer credential values were not written. This file is the canonical audit trail for artifact-first installs, which intentionally do not contain a Git checkout.

For source checkouts, `git -C "$INSTALL_ROOT/agent-setup" rev-parse HEAD` may additionally be used to inspect the checked-out commit, but it is not required for installation provenance.
