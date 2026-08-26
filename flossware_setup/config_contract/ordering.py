"""Declarative before/after ordering with cycle detection."""
from collections import defaultdict
class OrderingError(ValueError): pass
def resolve_order(items: list[str], constraints: list[dict[str, object]] | None = None) -> list[str]:
    constraints = constraints or []; nodes=set(items); edges:dict[str,set[str]]=defaultdict(set); indegree={x:0 for x in nodes}; index={x:i for i,x in enumerate(items)}
    for c in constraints:
        item=str(c["item"])
        if item not in nodes: raise OrderingError(f"unknown ordering item: {item}")
        for before in c.get("before",[]) or []:
            before=str(before)
            if before not in nodes: raise OrderingError(f"unknown ordering item: {before}")
            if before not in edges[item]: edges[item].add(before); indegree[before]+=1
        for after in c.get("after",[]) or []:
            after=str(after)
            if after not in nodes: raise OrderingError(f"unknown ordering item: {after}")
            if item not in edges[after]: edges[after].add(item); indegree[item]+=1
    ready=sorted((x for x,d in indegree.items() if d==0), key=index.get); result=[]
    while ready:
        node=ready.pop(0); result.append(node)
        for child in sorted(edges[node], key=index.get): indegree[child]-=1
        ready.extend(x for x in sorted(edges[node], key=index.get) if indegree[x]==0 and x not in ready and x not in result); ready.sort(key=index.get)
    if len(result)!=len(nodes): raise OrderingError("ordering constraints contain a cycle")
    return result
