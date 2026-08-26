"""Small deterministic, stdlib-only optimization engines for the setup demo."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Arm:
    name: str
    success: float
    cost: float


class ThompsonBandit:
    """Beta-Bernoulli Thompson Sampling with deterministic simulation support."""

    def __init__(self, arms: list[Arm], seed: int = 42) -> None:
        if not arms:
            raise ValueError("at least one arm is required")
        if any(not 0.0 <= arm.success <= 1.0 for arm in arms):
            raise ValueError("arm success probabilities must be between 0 and 1")
        self.arms = arms
        self.alpha = {a.name: 1.0 for a in arms}
        self.beta = {a.name: 1.0 for a in arms}
        self.rng = random.Random(seed)

    def select(self) -> Arm:
        return max(self.arms, key=lambda a: self.rng.betavariate(self.alpha[a.name], self.beta[a.name]))

    def observe(self, arm: Arm, success: bool) -> None:
        if arm.name not in self.alpha:
            raise ValueError(f"unknown arm: {arm.name}")
        if success:
            self.alpha[arm.name] += 1
        else:
            self.beta[arm.name] += 1

    def simulate_observation(self, arm: Arm) -> bool:
        """Generate a reproducible Bernoulli observation for offline demos."""
        success = self.rng.random() < arm.success
        self.observe(arm, success)
        return success

    def stats(self) -> dict[str, dict[str, float]]:
        return {
            a.name: {
                "alpha": self.alpha[a.name],
                "beta": self.beta[a.name],
                "mean": self.alpha[a.name] / (self.alpha[a.name] + self.beta[a.name]),
            }
            for a in self.arms
        }


def genetic_search(
    candidates: list[dict[str, object]],
    fitness: Callable[[dict[str, object]], float],
    *,
    generations: int = 8,
    seed: int = 42,
) -> tuple[dict[str, object], float]:
    """Deterministic bounded GA over a finite candidate list."""
    if not candidates:
        raise ValueError("at least one candidate is required")
    rng = random.Random(seed)
    population = [dict(candidate) for candidate in candidates]
    best = max(population, key=fitness)
    keys = sorted({key for candidate in candidates for key in candidate})
    values = {
        key: sorted({candidate[key] for candidate in candidates if key in candidate}, key=repr)
        for key in keys
    }

    for _ in range(max(1, generations)):
        scored = sorted(((fitness(x), x) for x in population), key=lambda pair: pair[0], reverse=True)
        if scored[0][0] > fitness(best):
            best = dict(scored[0][1])
        elite_count = max(1, len(scored) // 2)
        elites = [dict(x) for _, x in scored[:elite_count]]
        population = elites[:]
        while len(population) < len(candidates):
            left = rng.choice(elites)
            right = rng.choice(elites)
            child = {key: (left.get(key) if rng.random() < 0.5 else right.get(key)) for key in keys}
            for key in keys:
                if rng.random() < 0.20 and values[key]:
                    child[key] = rng.choice(values[key])
            population.append(child)
    return dict(best), float(fitness(best))
