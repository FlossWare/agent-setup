from flossware_setup.demo import run_demo


def test_demo_is_offline_and_deterministic(capsys):
    assert run_demo() == 0
    first = capsys.readouterr().out
    assert run_demo() == 0
    second = capsys.readouterr().out
    assert first == second
    assert "THOMPSON SAMPLING" in first
    assert "SELECTED:" in first
    assert "Policy: PASS" in first
