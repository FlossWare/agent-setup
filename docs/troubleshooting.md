# Troubleshooting

## Start with diagnostics

```bash
flossware-ai doctor
flossware-ai providers
flossware-ai accounts --verify
flossware-ai models --refresh
```

Use `doctor` for platform/runtime inventory. Use provider/account/model commands for discovery problems. Use `dogfood` for setup acceptance failures.

## `configured` but not `verified`

The credential source exists, but validation has not succeeded. Confirm that the native credential store or referenced environment variable is available to the current process. Never paste a secret into a profile or issue report.

## `verified` but not `available`

The credentials work, but the active profile policy excludes the provider/model. Inspect the active profile and its `model_policy.allowed_providers` and local-model policy.

## Provider or model discovery is empty

1. Verify the provider credential source.
2. Run `flossware-ai accounts --verify`.
3. Run `flossware-ai models --refresh`.
4. Run `flossware-ai doctor`.
5. Check whether the active profile blocks the provider.

Do not treat an empty discovery result as proof that a provider is unsupported. It may be unconfigured, unreachable, or policy-blocked.

## TUI will not start

Check terminal capability and Python dependencies with `flossware-ai doctor`. Resize the terminal if panels are clipped. The Setup TUI is a curses terminal application, not a graphical desktop UI.

Keyboard navigation uses arrows, Enter, Escape, Space, `a`, `n`, `q`, and the documented contextual shortcuts. Primary mouse clicks are supported where the terminal reports mouse events; terminal emulators differ in how mouse reporting is exposed.

## Agent is not detected

The setup registry can describe an agent even when its executable is absent. Install the agent separately, ensure its executable is on `PATH`, then rerun:

```bash
flossware-ai agents
flossware-ai agents setup <agent-id>
```

Native agent credentials are not owned by FlossWare and are not removed by `--clean`.

## Container runtime problems

```bash
flossware-ai runtime list
flossware-ai runtime status
flossware-ai runtime auto
```

Podman is preferred automatically on healthy Linux installations. Docker can be selected explicitly. Native execution remains valid when no container runtime is available.

## Reinstall and cleanup

```bash
./scripts/install.sh --reinstall
./scripts/install.sh --clean
```

Cleanup is limited to the managed FlossWare installation. If native agent configuration or project instruction files disappear, stop and report the failure rather than manually restoring secrets from logs.

## Dogfood failures

Source tree:

```bash
python scripts/dogfood.py
python scripts/dogfood.py --strict
```

Installed runtime:

```bash
flossware-ai dogfood --strict
```

Strict mode intentionally requires both Claude Code and Crush on `PATH`. CI validates clean Fedora and Debian installation boundaries but does not impersonate a user's authenticated provider accounts.

## Platform notes

- Fedora/RHEL: Podman is normally the preferred runtime.
- Debian/Ubuntu: use the Debian-family installer path.
- FreeBSD: container support is capability-detected and may require an external VM.
- Termux: Android restrictions apply; native container support is not assumed.
- Windows: use `scripts/install.ps1`; container support depends on Docker Desktop/Podman availability and the terminal's curses compatibility.
