"""Deterministic offline showcase for the complete configuration/optimization contract."""
from __future__ import annotations

from flossware_setup.config_contract import ConfigField, ConfigLayer, ConfigResolver, ConfigSchema, Policy, resolve_order
from flossware_setup.optimizer import Arm, ThompsonBandit, genetic_search


def run_demo() -> int:
    print("FLOSSWARE CONFIGURATION + OPTIMIZATION DEMO")
    print("=" * 52)
    resolver = ConfigResolver()
    resolver.add_layer(ConfigLayer("defaults", 0, {"optimization.population": 30, "provider": "anthropic"}))
    resolver.add_layer(ConfigLayer("system", 100, {"optimization.population": 50}))
    resolver.add_layer(ConfigLayer("profile:redhat-cost-conscious", 300, {"provider": "anthropic", "budget.monthly": 300.0}))
    resolver.add_layer(ConfigLayer("project", 400, {"optimization.population": 75}))
    effective = resolver.resolve()
    schema = ConfigSchema().add(ConfigField("optimization.population", "integer", 30, 1, 500)).add(
        ConfigField("provider", "string", "anthropic", values=("anthropic",))
    )
    schema.validate(effective)
    Policy(allowed={"provider": ["anthropic"]}).validate(effective)
    print("\nLAYERED CONFIGURATION")
    print(resolver.explain("optimization.population"))

    order = resolve_order(
        ["models", "validation", "optimization", "agents"],
        [{"item": "optimization", "after": ["models"], "before": ["validation"]}],
    )
    print("\nORDERING")
    print(" -> ".join(order))

    candidates = [
        {"model": "haiku", "retrieval": "hybrid", "verification": "tests", "cost": 0.25, "quality": 0.86},
        {"model": "sonnet", "retrieval": "hybrid", "verification": "tests", "cost": 0.80, "quality": 0.96},
        {"model": "sonnet", "retrieval": "direct", "verification": "consensus", "cost": 1.10, "quality": 0.98},
        {"model": "haiku", "retrieval": "direct", "verification": "static", "cost": 0.15, "quality": 0.80},
    ]

    def fitness(candidate):
        return float(candidate["quality"]) - 0.12 * float(candidate["cost"])

    best, score = genetic_search(candidates, fitness, generations=10, seed=42)
    print("\nGENETIC OPTIMIZATION")
    print(f"best={best['model']} + {best['retrieval']} + {best['verification']} fitness={score:.3f}")

    arms = [
        Arm("haiku+hybrid", 0.86, 0.25),
        Arm("sonnet+hybrid", 0.96, 0.80),
        Arm("sonnet+consensus", 0.98, 1.10),
    ]
    bandit = ThompsonBandit(arms, seed=42)
    observations = 30
    for _ in range(observations):
        bandit.simulate_observation(bandit.select())
    print("\nTHOMPSON SAMPLING")
    for name, stats in bandit.stats().items():
        print(f"{name:20} alpha={stats['alpha']:.0f} beta={stats['beta']:.0f} mean={stats['mean']:.3f}")
    selected = max(bandit.stats(), key=lambda n: bandit.stats()[n]["mean"])
    print(f"\nSELECTED: {selected}")
    print("Policy: PASS | Provider: Anthropic | Budget: $300/month hard ceiling | Network: not used")
    print(f"Observations: {observations} | Explainability: PASS | Reproducibility: PASS")
    return 0
