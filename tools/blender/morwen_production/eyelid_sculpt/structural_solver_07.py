"""Dirichlet harmonic lid displacement; no pivot rotation or old-key transfer."""
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve


def harmonic_field(vertices, edges, fixed):
    """Uniform positive graph Laplacian, exact prescribed boundary values.

    Raises on disconnected/unanchored components; never invents a zero solution.
    fixed maps vertex IDs to equally sized vectors (displacement + blend weights).
    """
    ids=sorted(vertices); index={v:i for i,v in enumerate(ids)}
    graph={v:set() for v in ids}
    for a,b in edges:
        if a in graph and b in graph:
            graph[a].add(b); graph[b].add(a)
    seen=set()
    for start in ids:
        if start in seen: continue
        stack=[start]; component=set()
        while stack:
            v=stack.pop()
            if v in component: continue
            component.add(v); stack.extend(graph[v]-component)
        seen.update(component)
        if not component & set(fixed): raise ValueError('Unanchored component')
    dimension=len(next(iter(fixed.values())))
    matrix=lil_matrix((len(ids),len(ids)),dtype=float)
    rhs=np.zeros((len(ids),dimension))
    for v,i in index.items():
        if v in fixed:
            matrix[i,i]=1; rhs[i]=fixed[v]
        else:
            matrix[i,i]=len(graph[v])
            for n in graph[v]: matrix[i,index[n]]=-1
    answer=spsolve(matrix.tocsr(),rhs)
    if not np.isfinite(answer).all(): raise ValueError('Nonfinite harmonic solve')
    return {v:answer[i] for v,i in index.items()}


def compose(position, rest, fields, controls):
    """Numeric reference for the Geometry Nodes modifier, four independent controls."""
    result=np.array(position,dtype=float).copy()
    for (delta,weight),control in zip(fields,controls,strict=True):
        if not 0 <= control <= 1: raise ValueError('Control outside [0,1]')
        result+=control*(delta+weight[:,None]*(rest-position))
    return result
