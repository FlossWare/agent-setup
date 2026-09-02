"""Installer must accept both historical and canonical GitHub archive prefixes."""

from __future__ import annotations

from pathlib import Path

INSTALLER = Path(__file__).resolve().parents[1] / "scripts" / "install.sh"


def test_installer_accepts_renamed_archive_prefix() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert "coding-agent-setup-*" in text
    assert "agent-setup-*" in text
    assert "failed to unpack" in text and "artifact" in text
