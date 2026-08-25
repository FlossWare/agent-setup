import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("flossware_tui", ROOT / "scripts" / "tui.py")
tui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tui)


def test_discovery_commands_cover_provider_and_model_views():
    assert tui._run_discovery.__doc__
    expected = {
        "providers": ["providers"],
        "accounts": ["accounts"],
        "verified": ["accounts", "--verify"],
        "models": ["models"],
        "available": ["models", "--available"],
        "free": ["models", "--free"],
        "doctor": ["doctor"],
    }
    choices = ["providers", "accounts", "verified", "models", "available", "free", "doctor"]
    command_map = dict(zip(choices, expected.values()))
    assert command_map["available"] == ["models", "--available"]
    assert command_map["free"] == ["models", "--free"]
    assert command_map["verified"] == ["accounts", "--verify"]


def test_run_discovery_returns_stdout_without_credentials(monkeypatch):
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["timeout"] == 60
        return SimpleNamespace(stdout="Provider: anthropic\nStatus: configured", stderr="")

    monkeypatch.setattr(tui.subprocess, "run", fake_run)
    output = tui._run_discovery(["providers"])

    assert "anthropic" in output
    assert "API_KEY" not in output
    assert seen["command"][-1] == "providers"
    assert str(tui.ROOT / "venv/bin/python") in seen["command"][0]


def test_run_discovery_prefers_error_output(monkeypatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(stdout="", stderr="discovery unavailable")

    monkeypatch.setattr(tui.subprocess, "run", fake_run)
    assert tui._run_discovery(["doctor"]) == "discovery unavailable"
