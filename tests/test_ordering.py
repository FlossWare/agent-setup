import pytest

from flossware_setup.config_contract import OrderingError, reorder, resolve_order


def test_resolves_before_after_constraints():
    items = ["models", "validation", "optimization", "agents"]
    constraints = [{"item": "optimization", "after": ["models"], "before": ["validation"]}]
    assert resolve_order(items, constraints) == ["models", "optimization", "validation", "agents"]


def test_rejects_cycles():
    with pytest.raises(OrderingError, match="cycle"):
        resolve_order(["a", "b"], [{"item": "a", "after": ["b"]}, {"item": "b", "after": ["a"]}])


def test_reorder_accepts_unconstrained_move():
    assert reorder(["a", "b", "c"], "c", -1) == ["a", "c", "b"]


def test_reorder_rejects_constraint_violation():
    with pytest.raises(OrderingError, match="constraint"):
        reorder(["models", "optimization", "validation"], "optimization", -1, [{"item": "optimization", "after": ["models"]}])
