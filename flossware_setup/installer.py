"""Package installation for selected FlossWare capabilities."""

from __future__ import annotations

import subprocess
import sys

from flossware_setup.artifacts import pip_packages


def install_packages(capability_indexes: list[int]) -> None:
    """Install selected capability packages. Fails closed on any error."""
    for package in pip_packages(capability_indexes):
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", package],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,  # we inspect returncode and raise a domain-specific error
        )
        if result.returncode != 0:
            detail = result.stderr[-1200:] if result.stderr else ""
            raise RuntimeError(
                f"Required library failed to install: {package}\n{detail}"
            )
