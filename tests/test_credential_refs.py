from flossware_setup import credential_refs


def test_set_credential_reference_persists_only_reference(monkeypatch):
    data = {"profile": "default", "model_policy": {"allowed_providers": ["*configured*"]}}
    captured = {}

    monkeypatch.setattr(credential_refs, "load_profile", lambda name: data)
    monkeypatch.setattr(
        credential_refs,
        "write_profile",
        lambda name, value: captured.update({"name": name, "value": value}) or "profile.toml",
    )

    result = credential_refs.set_credential_reference(
        "default", "anthropic/personal", "ANTHROPIC_API_KEY", source="environment"
    )

    assert result == "profile.toml"
    assert captured["value"]["credentials"] == {
        "anthropic/personal": {
            "ref": "ANTHROPIC_API_KEY",
            "source": "environment",
        }
    }
    assert "secret" not in repr(captured["value"]).lower()


def test_credential_reference_rejects_unsupported_source(monkeypatch):
    monkeypatch.setattr(credential_refs, "load_profile", lambda name: {"profile": name})

    try:
        credential_refs.set_credential_reference(
            "default", "github/personal", "GH_TOKEN", source="plaintext"
        )
    except ValueError as exc:
        assert "unsupported credential source" in str(exc)
    else:
        raise AssertionError("unsupported credential source was accepted")


def test_credential_reference_rejects_multiline_reference():
    try:
        credential_refs._validate_ref("TOKEN\nLEAK", "credential ref")
    except ValueError as exc:
        assert "single-line" in str(exc)
    else:
        raise AssertionError("multiline credential reference was accepted")
