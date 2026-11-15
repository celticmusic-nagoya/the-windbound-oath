"""Guarded closed-loop splitter. Requires externally verified canthus IDs."""
import math

def split_loop(component, anchors, samples=33):
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 2:
        raise ValueError("samples must be an integer >= 2")
    ids = component["ordered_vertex_ids"]
    raw_edges = component["edge_ids"]
    if any(len(e) != 2 or e[0] == e[1] for e in raw_edges):
        raise ValueError("Malformed edge")
    edges = {tuple(sorted(e)) for e in raw_edges}
    if not component["graph_valid"] or not component["closed_loop"] or len(ids) < 6:
        raise ValueError("Expected valid closed loop")
    if len(ids) != len(set(ids)) or len(edges) != len(ids) or len(edges) != len(raw_edges):
        raise ValueError("Malformed ring or duplicate edge")
    expected = {tuple(sorted((ids[k], ids[(k+1) % len(ids)]))) for k in range(len(ids))}
    if edges != expected or set(component.get("vertex_ids", ids)) != set(ids):
        raise ValueError("Invalid edge traversal, branch or missing vertex")
    if len(anchors) != 2 or anchors[0] == anchors[1] or any(x not in ids for x in anchors):
        raise ValueError("Two distinct verified canthus IDs required")
    # Preserve the caller's medial -> lateral direction, regardless of ring origin.
    i = ids.index(anchors[0])
    ring = ids[i:] + ids[:i]
    j = ring.index(anchors[1])
    first = ring[:j+1]
    second = [ring[0]] + list(reversed(ring[j:]))
    if min(len(first), len(second)) < 3:
        raise ValueError("Degenerate candidate arc")
    coords = component["world_xyz_m"]
    try:
        points = [coords[str(v)] for v in ids]
        if any(len(p) != 3 or any(not math.isfinite(x) for x in p) for p in points):
            raise ValueError("Expected finite XYZ coordinates")
    except (KeyError, TypeError) as exc:
        raise ValueError("Missing or invalid coordinates") from exc
    if len({tuple(p) for p in points}) != len(points):
        raise ValueError("Coincident vertices")
    lengths = [math.dist(coords[str(a)], coords[str(b)]) for a, b in expected]
    if min(lengths) <= 1e-10:
        raise ValueError("Invalid edge length")
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
            "anchor_ids":list(anchors),"edge_length_ratio":max(lengths)/min(lengths),"chain_A":first,"chain_B":second,
            "paired_samples":[{"u":round(k/(samples-1),9),
                               "A":at(first,ua,k/(samples-1)),
                               "B":at(second,ub,k/(samples-1))} for k in range(samples)],
            "semantic_upper_lower":"UNASSIGNED","medial_lateral":"UNASSIGNED"}
