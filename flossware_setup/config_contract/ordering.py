"""Declarative before/after ordering with cycle detection."""
from collections import defaultdict

class OrderingError(ValueError):
    pass

def resolve_order(items: list[str], constraints: list[dict[str, object]] | None = None) -> list[str]:
    constraints = constraints or []
    nodes = set(items)
    if len(nodes) != len(items):
        raise OrderingError("duplicate ordering item")
    edges: dict[str, set[str]] = defaultdict(set)
    indegree = {x: 0 for x in nodes}
    index = {x: i for i, x in enumerate(items)}
    for c in constraints:
        if "item" not in c:
            raise OrderingError("ordering constraint missing item")
        item = str(c["item"])
        if item not in nodes:
            raise OrderingError(f"unknown ordering item: {item}")
        for before in c.get("before", []) or []:
            before = str(before)
            if before not in nodes:
                raise OrderingError(f"unknown ordering item: {before}")
            if before not in edges[item]:
                edges[item].add(before)
                indegree[before] += 1
        for after in c.get("after", []) or []:
            after = str(after)
            if after not in nodes:
                raise OrderingError(f"unknown ordering item: {after}")
            if item not in edges[after]:
                edges[after].add(item)
                indegree[item] += 1
    ready = sorted((x for x, d in indegree.items() if d == 0), key=index.get)
    result: list[str] = []
    while ready:
        node = ready.pop(0)
        result.append(node)
        for child in sorted(edges[node], key=index.get):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
        ready.sort(key=index.get)
    if len(result) != len(nodes):
        raise OrderingError("ordering constraints contain a cycle")
    return result


def reorder(items: list[str], item: str, direction: int, constraints: list[dict[str, object]] | None = None) -> list[str]:
    """Move an item one position while preserving declared dependency constraints."""
    if item not in items:
        raise OrderingError(f"unknown ordering item: {item}")
    proposed = list(items)
    i = proposed.index(item)
    j = i + (1 if direction > 0 else -1)
    if not 0 <= j < len(proposed):
        return proposed
    proposed[i], proposed[j] = proposed[j], proposed[i]
    resolved = resolve_order(proposed, constraints)
    if resolved != proposed:
        raise OrderingError("move would violate an ordering constraint")
    return proposed
