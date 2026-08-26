"""Declarative before/after ordering with cycle detection."""

from collections import defaultdict


class OrderingError(ValueError):
    pass


def resolve_order(items: list[str], constraints: list[dict[str, object]] | None = None) -> list[str]:
    constraints = constraints or []
    nodes = set(items)
    edges: dict[str, set[str]] = defaultdict(set)
    indegree = {item: 0 for item in nodes}

    for constraint in constraints:
        item = str(constraint["item"])
        if item not in nodes:
            raise OrderingError(f"unknown ordering item: {item}")
        for before in constraint.get("before", []) or []:
            before = str(before)
            if before not in nodes:
                raise OrderingError(f"unknown ordering item: {before}")
            if before not in edges[item]:
                edges[item].add(before)
                indegree[before] += 1
        for after in constraint.get("after", []) or []:
            after = str(after)
            if after not in nodes:
                raise OrderingError(f"unknown ordering item: {after}")
            if item not in edges[after]:
                edges[after].add(item)
                indegree[item] += 1

    # Stable topological sort: preserve caller order whenever constraints permit it.
    order_index = {item: index for index, item in enumerate(items)}
    ready = sorted((n for n, degree in indegree.items() if degree == 0), key=order_index.get)
    result: list[str] = []
    while ready:
        node = ready.pop(0)
        result.append(node)
        for child in sorted(edges[node], key=order_index.get):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
        ready.sort(key=order_index.get)

    if len(result) != len(nodes):
        raise OrderingError("ordering constraints contain a cycle")
    return result
