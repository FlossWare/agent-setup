"""Credential-source discovery. Secret values are never returned or persisted."""
import os
from .catalog import PROVIDERS

def status() -> dict[str, bool]:
    return {name: bool(os.environ.get(env)) for name, env, _ in PROVIDERS}

def environment_names() -> dict[str, str]:
    return {name: env for name, env, _ in PROVIDERS}
