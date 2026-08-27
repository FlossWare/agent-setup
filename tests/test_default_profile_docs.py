"""Keep the default-profile contract visible in the documentation."""

from pathlib import Path


def test_default_profile_docs_describe_optional_named_profiles() -> None:
    docs = Path(__file__).parents[1] / "docs" / "default-profile.md"
    text = docs.read_text(encoding="utf-8")
    assert "provider-neutral" in text
    assert "not make any named deployment profile mandatory" in text
    assert "Turbo C++" in text
    assert "stores no credentials" in text
