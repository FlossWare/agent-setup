import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("runtime", Path(__file__).parents[1] / "scripts" / "runtime.py")
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def test_runtime_names_are_supported():
    assert {x["runtime"] for x in runtime.all_status()} == {"podman", "docker"}


def test_selection_defaults_to_auto(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "STATE", tmp_path)
    monkeypatch.setattr(runtime, "PREFERENCE", tmp_path / "selected")
    assert runtime.selected() == "auto"
    assert runtime.healthy_preference() in {"podman", "docker", "native"}


def test_select_persists_non_secret_preference(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "STATE", tmp_path)
    monkeypatch.setattr(runtime, "PREFERENCE", tmp_path / "selected")
    assert runtime.main(["select", "podman"]) == 0
    assert runtime.selected() == "podman"
    assert runtime.PREFERENCE.read_text() == "podman\n"
