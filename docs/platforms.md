# Platform support

FlossWare coding-agent-setup targets a common user-facing workflow across Fedora/RHEL derivatives, Debian-family Linux, FreeBSD, Windows, and Termux.

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
