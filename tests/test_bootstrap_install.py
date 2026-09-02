"""Canonical bootstrap entry point behavior."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "install.sh"
INSTALLER = ROOT / "scripts" / "install.sh"


def test_root_install_sh_is_executable() -> None:
    assert BOOTSTRAP.is_file()
    mode = BOOTSTRAP.stat().st_mode
    assert mode & stat.S_IXUSR, "install.sh must be executable"


def test_root_install_sh_is_not_recovery_wrapper() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "RECOVERY_REF" not in text
    assert "e9a4b2692d66cc7c4f9285516ef5eaa1a174cc67" not in text
    assert "scripts/install.sh" in text
    assert "FlossWare/agent-setup" in text


def test_scripts_install_uses_canonical_repo_urls() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert "github.com/FlossWare/agent-setup" in text
    assert "codeload.github.com/FlossWare/agent-setup" in text
    # Historical install path name remains for managed layout compatibility.
    assert 'SETUP_DIR="$INSTALL_ROOT/coding-agent-setup"' in text or "coding-agent-setup" in text


def test_local_bootstrap_delegates_to_scripts_install_help() -> None:
    """From a checkout, ./install.sh must exec scripts/install.sh (help path)."""
    proc = subprocess.run(
        ["bash", str(BOOTSTRAP), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    out = (proc.stdout or "") + (proc.stderr or "")
    assert "Usage:" in out or "install.sh" in out
    assert "Profile" in out or "--profile" in out or "profile" in out.lower()


def test_crush_setup_is_not_duplicated_in_bootstrap() -> None:
    """Bootstrap must not embed a second Crush installer; CLI owns that path."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "crush" not in text.lower()
    crush = (ROOT / "flossware_setup" / "crush_setup.py").read_text(encoding="utf-8")
    assert "def setup_crush" in crush
