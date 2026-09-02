# Platform support

FlossWare agent-setup targets a common user-facing workflow across Fedora/RHEL derivatives, Debian-family Linux, FreeBSD, Windows, and Termux.

## Supported platforms

| Platform | Installer | Setup TUI | CLI | Artifact-first | Containers |
|---|---|---|---|---|---|
| Fedora / RHEL derivatives | `install.sh` | Yes | Yes | Yes | Podman preferred, Docker supported |
| Debian-family Linux | `install.sh` | Yes | Yes | Yes | Podman preferred, Docker supported |
| FreeBSD | `install.sh` | Yes | Yes | Yes | Detect only reachable runtime |
| Termux / Android | `install.sh` | Yes | Yes | Yes | Detect only reachable runtime |
| Windows | `install.ps1` | Yes | Yes | Yes | Docker Desktop / Podman where available |

The table describes FlossWare setup support. It does not claim that every third-party coding agent or container runtime provides identical native functionality on every platform.

## Fedora and RHEL derivatives

The installer detects the RPM-family platform and uses the available system tooling. Red Hat policy is represented by the active `redhat` profile, not by assuming that every RPM-family system is a Red Hat corporate environment.

Podman is the preferred container backend when it is installed and reachable.

## Debian family

The installer detects Debian-family systems and uses the available package tooling. Ubuntu and other compatible Debian derivatives follow the same setup path where their Python/runtime prerequisites are compatible.

## FreeBSD

The setup layer is platform-aware and avoids Linux-specific assumptions. Container support is capability-detected. If Podman or Docker requires an external VM or compatibility arrangement, the UI reports that arrangement as external rather than claiming native support.

## Termux

Termux is treated as an Android userland. The installer uses `pkg`-provided prerequisites and keeps FlossWare state in the user-managed FlossWare directory. Native Android restrictions are respected. Container runtime availability is detected rather than assumed.

## Windows

Windows uses the PowerShell installer and Windows-compatible launchers. The Setup TUI uses the Windows curses compatibility dependency when required. Container support is capability-based and can use Docker Desktop or Podman where available.

## Shared behavior

All platforms share these invariants:

- configuration is declarative and platform-neutral where possible;
- secrets remain in environment/native credential stores;
- managed state is isolated under the FlossWare user directory;
- released artifacts are preferred to source builds;
- source installation remains an explicit fallback;
- native execution remains available when containers are absent;
- `doctor` reports platform-specific failures without hiding them behind generic success states.

## Platform path reference

| Platform | User / config style | Default managed runtime (`FLOSSWARE_AI_ROOT` unset) | Notes |
|----------|---------------------|------------------------------------------------------|-------|
| Linux (Fedora/Debian) | XDG-style under `$HOME` | `~/.flossware/ai` | Override with absolute `FLOSSWARE_AI_ROOT` |
| FreeBSD | Same as Linux | `~/.flossware/ai` | |
| macOS | Same as Linux | `~/.flossware/ai` | Not forced under `~/Library` |
| Windows | `%USERPROFILE%\.flossware\ai` | Same pattern via home | Use `install.ps1` |
| Termux | `$HOME` under Termux prefix | `$HOME/.flossware/ai` | See `docs/platforms/termux.md` |

### Environment variables that control install paths

| Variable | Role |
|----------|------|
| `FLOSSWARE_INSTALL_ROOT` | Managed install root used by `scripts/install.sh` (default `~/.flossware/ai`) |
| `FLOSSWARE_AI_ROOT` | Runtime/state root read by the Python package (active project, themes) |
| `FLOSSWARE_RELEASE_REF` | Git branch, tag, or commit for the **agent-setup** archive |
| `FLOSSWARE_AI_REF` | Git ref for **agent-ai** (defaults to `main`; independent of setup ref) |
| `FLOSSWARE_USE_SOURCE` | When `true`, clone setup with git instead of the source archive |
| `FLOSSWARE_INSTALL_URL` | Override base URL for bootstrap download of `scripts/install.sh` |

### Reproducible bootstrap examples

```bash
# Stable release (default main)
curl -fsSL https://raw.githubusercontent.com/FlossWare/agent-setup/main/install.sh | bash

# Specific branch or tag
FLOSSWARE_RELEASE_REF=v0.1.0 bash install.sh

# Specific commit (reproducible)
FLOSSWARE_RELEASE_REF=3d2e52ba601bd16d4451448d0b843ffb25d35a27 bash install.sh
```

### Central project state layout

```text
~/.flossware/ai/
├── profiles/
├── profile-bindings.toml
├── projects/
│   └── <16-char-sha256-of-path>/
│       ├── state.json
│       ├── ai_config.py
│       └── path.txt
└── state/
    └── active-project
```
