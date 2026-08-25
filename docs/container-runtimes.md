# Container runtimes

FlossWare treats containers as an execution backend, not as an operating-system-specific feature. The supported runtimes are **Podman** and **Docker**.

## Policy

- Linux: prefer Podman when available, with Docker fully supported.
- Windows: support Docker Desktop and Podman Desktop/Podman where available.
- FreeBSD and Termux: detect the runtime only when it is actually reachable; do not claim native support where the runtime requires an external VM, daemon, or compatibility layer.
- `auto` selects the first healthy supported runtime according to the platform policy.
- Native execution remains available when no container runtime is configured.

The setup layer must never require a container runtime merely to install or run the core Python tooling.

## CLI contract

```text
flossware-ai runtime list
flossware-ai runtime status
flossware-ai runtime select podman
flossware-ai runtime select docker
flossware-ai runtime auto
```

`status` reports installed, reachable, version, and selected state. `auto` does not install a runtime; installation of Podman or Docker is an explicit platform operation.

## TUI

The operator TUI exposes **Execution → Container Runtime** with:

- Auto / Podman / Docker / Native selection
- health and version status
- runtime endpoint/context where applicable
- refresh and validation
- platform capability notes

The same contextual description/status model used by other FlossWare components applies here. Runtime configuration contains no credentials or secret values.

## Loom

Loom may use the selected container runtime for supporting services or isolated workloads. Loom's core remains usable without containers. A containerized dependency must declare its runtime requirements and health checks rather than assuming Docker or Podman is present.
