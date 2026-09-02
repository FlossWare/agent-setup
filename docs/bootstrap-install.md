# Bootstrap installation

`agent-setup` is a consumer-facing installer. A normal user does **not** clone the Git repository.

## Quick start

Linux, Fedora/RHEL, Debian-family systems, FreeBSD, and Termux use the public bootstrap path:

```bash
curl -fsSL https://raw.githubusercontent.com/FlossWare/agent-setup/main/install.sh | bash
flossware-ai tui
```

The bootstrap is designed for an empty working directory. It obtains the selected setup distribution without creating a Git checkout.

## What happens

```text
public bootstrap
      |
      +--> agent-ai package artifact (when available)
      |
      +--> agent-setup source archive for the selected ref
      |
      +--> managed virtual environment
      |
      +--> default profile + CLI/TUI
      |
      +--> discovery / doctor / dogfood
```

The normal installation path does not require `git`, does not clone the repository, and does not leave a `.git` directory in the managed installation.

## Release selection

The bootstrap defaults to `main` until a formal stable release channel is established. Controlled deployments and release-candidate testing can select a ref with:

```bash
FLOSSWARE_RELEASE_REF=<tag-or-branch> \
  curl -fsSL https://raw.githubusercontent.com/FlossWare/agent-setup/main/install.sh | bash
```

Use a release/tag rather than a moving branch when reproducibility is required.

## Developer/source mode

Only contributors who intentionally need editable source installation should use a checkout:

```bash
git clone https://github.com/FlossWare/agent-setup.git
cd agent-setup
FLOSSWARE_USE_SOURCE=true ./scripts/install.sh
```

Source mode is a development escape hatch. It is not part of the normal consumer workflow.

## Reinstall and cleanup

After installation, use the managed installer/CLI lifecycle commands documented in the operator guide. Cleanup removes only FlossWare-managed state. It must not remove native agent credentials, provider credentials, project instruction files, or unrelated user data.

## CI contract

The clean-install workflow validates the consumer boundary separately from source-checkout testing. The important consumer invariant is:

> An empty directory plus the public bootstrap is sufficient to install and start the setup control plane.

CI may use a local checkout to exercise the bootstrap implementation itself, but that is a test harness detail, not a consumer requirement.

## Troubleshooting

If the bootstrap fails:

1. rerun with shell tracing if needed;
2. check the platform prerequisites in [`platforms.md`](platforms.md);
3. run `flossware-ai doctor` after a partial installation if the CLI is available;
4. use explicit source mode only when investigating a source/development problem.

Do not manually delete credentials or native agent configuration as a first recovery step.
