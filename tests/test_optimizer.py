from flossware_setup.optimizer import Arm, ThompsonBandit, genetic_search


def test_thompson_sampling_is_reproducible():
    arms = [Arm("cheap", 0.8, 0.1), Arm("strong", 0.95, 1.0)]
    left = ThompsonBandit(arms, seed=42)
    right = ThompsonBandit(arms, seed=42)
    for _ in range(30):
        left.simulate_observation(left.select())
        right.simulate_observation(right.select())
    assert left.stats() == right.stats()


def test_thompson_rejects_invalid_arms():
    try:
        ThompsonBandit([Arm("bad", 1.1, 0.1)])
    except ValueError as exc:
        assert "between 0 and 1" in str(exc)
    else:
        raise AssertionError("invalid probability was accepted")


def test_genetic_search_is_reproducible_and_bounded():
    candidates = [
        {"model": "cheap", "quality": 0.7, "cost": 0.1},
        {"model": "strong", "quality": 0.95, "cost": 1.0},
    ]
    fitness = lambda x: x["quality"] - 0.1 * x["cost"]
    first = genetic_search(candidates, fitness, generations=10, seed=42)
    second = genetic_search(candidates, fitness, generations=10, seed=42)
    assert first == second
    assert first[0]["model"] in {"cheap", "strong"}
