"""Guarded closed-loop splitter. Requires externally verified canthus IDs."""
import math

def split_loop(component, anchors, samples=33):
    ids = component["ordered_vertex_ids"]
    edges = {tuple(sorted(e)) for e in component["edge_ids"]}
    if not component["graph_valid"] or not component["closed_loop"] or len(ids) < 6:
        raise ValueError("Expected valid closed loop")
    if len(ids) != len(set(ids)) or len(edges) != len(ids):
        raise ValueError("Malformed ring")
    if any(tuple(sorted((ids[i], ids[(i+1) % len(ids)]))) not in edges for i in range(len(ids))):
        raise ValueError("Invalid edge traversal")
    if len(anchors) != 2 or anchors[0] == anchors[1] or any(x not in ids for x in anchors):
        raise ValueError("Two distinct verified canthus IDs required")
    i, j = sorted(ids.index(x) for x in anchors)
    first = ids[i:j+1]
    second = list(reversed(ids[j:] + ids[:i+1]))
    if min(len(first), len(second)) < 3:
        raise ValueError("Degenerate candidate arc")
    coords = component["world_xyz_m"]
    def params(chain):
        ds = [0.0]
        for x,y in zip(chain,chain[1:]):
            length = math.dist(coords[str(x)], coords[str(y)])
            if not math.isfinite(length) or length <= 1e-10:
                raise ValueError("Invalid edge length")
            ds.append(ds[-1]+length)
        return [d/ds[-1] for d in ds]
    def at(chain, us, u):
        for k in range(len(us)-1):
            if us[k] <= u <= us[k+1]:
                return {"edge_vertex_ids":[chain[k],chain[k+1]],
                        "edge_t":round((u-us[k])/(us[k+1]-us[k]),9)}
        raise AssertionError("Interpolation failure")
    ua,ub = params(first),params(second)
    return {"status":"PROVISIONAL_ANCHOR_GATED_NOT_ART_APPROVED",
            "anchor_ids":list(anchors),"chain_A":first,"chain_B":second,
            "paired_samples":[{"u":round(k/(samples-1),9),
                               "A":at(first,ua,k/(samples-1)),
                               "B":at(second,ub,k/(samples-1))} for k in range(samples)],
            "semantic_upper_lower":"UNASSIGNED","medial_lateral":"UNASSIGNED"}
