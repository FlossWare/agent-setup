"""Small deterministic, stdlib-only optimization engine for the setup demo."""
from __future__ import annotations
import random
from dataclasses import dataclass

@dataclass(frozen=True)
class Arm:
    name: str
    success: float
    cost: float

class ThompsonBandit:
    def __init__(self, arms: list[Arm], seed: int = 42) -> None:
        self.arms = arms
        self.alpha = {a.name: 1.0 for a in arms}
        self.beta = {a.name: 1.0 for a in arms}
        self.rng = random.Random(seed)

    def select(self) -> Arm:
        return max(self.arms, key=lambda a: self.rng.betavariate(self.alpha[a.name], self.beta[a.name]))

    def observe(self, arm: Arm, success: bool) -> None:
        self.alpha[arm.name] += 1 if success else 0
        self.beta[arm.name] += 0 if success else 1

    def stats(self) -> dict[str, dict[str, float]]:
        return {a.name: {"alpha": self.alpha[a.name], "beta": self.beta[a.name], "mean": self.alpha[a.name] / (self.alpha[a.name] + self.beta[a.name])} for a in self.arms}

def genetic_search(candidates: list[dict[str, object]], fitness, *, generations: int = 8, seed: int = 42) -> tuple[dict[str, object], float]:
    """Deterministic bounded GA over a finite candidate list."""
    rng = random.Random(seed)
    population = list(candidates)
    best = max(population, key=fitness)
    for _ in range(max(1, generations)):
        scored = sorted(((fitness(x), x) for x in population), key=lambda p: p[0], reverse=True)
        if scored[0][0] > fitness(best): best = scored[0][1]
        elites = [x for _, x in scored[:max(1, len(scored)//2)]]
        population = elites[:]
        while len(population) < len(candidates):
            parent = rng.choice(elites)
            child = dict(parent)
            if rng.random() < 0.35:
                child["verification"] = rng.choice(["tests", "consensus", "static"])
            population.append(child)
    return best, float(fitness(best))
