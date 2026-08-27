"""Regression coverage for the provider-neutral default profile."""

from __future__ import annotations

from pathlib import Path


def test_shipped_default_profile_is_neutral() -> None:
    profile = Path(__file__).parents[1] / "profiles" / "default.toml"
    text = profile.read_text(encoding="utf-8")

    assert 'profile = "default"' in text
    assert 'allowed_providers = ["*configured*"]' in text
    assert "allow_local_models = true" in text
    assert "allow_unconfigured_providers = false" in text
    assert 'profile = "personal"' not in text
    assert 'profile = "redhat"' not in text


def test_named_profiles_are_examples_not_requirements() -> None:
    root = Path(__file__).parents[1] / "profiles"
    assert not (root / "personal.toml").exists()
    assert not (root / "redhat.toml").exists()
    assert (root / "default.toml").is_file()
