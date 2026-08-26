import pytest

from flossware_setup.config.ordering import OrderingError, resolve_order


def test_resolves_before_after_constraints():
    items = ["models", "validation", "optimization", "agents"]
    constraints = [{"item": "optimization", "after": ["models"], "before": ["validation"]}]
    assert resolve_order(items, constraints) == ["models", "optimization", "validation", "agents"]


def test_rejects_cycles():
    with pytest.raises(OrderingError, match="cycle"):
        resolve_order(["a", "b"], [{"item": "a", "after": ["b"]}, {"item": "b", "after": ["a"]}])
