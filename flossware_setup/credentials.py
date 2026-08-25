"""Credential presence checks without reading or storing secret values."""

from __future__ import annotations

import os

from flossware_setup.catalog import PROVIDERS


def credential_status() -> dict[str, bool]:
    """Return whether each known provider env var is set (true/false only)."""
    return {name: bool(os.environ.get(env)) for name, env, _ in PROVIDERS}


def environment_names() -> dict[str, str]:
    """Map provider display names to environment variable names."""
    return {name: env for name, env, _ in PROVIDERS}
