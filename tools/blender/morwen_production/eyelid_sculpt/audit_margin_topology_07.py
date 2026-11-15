"""Read-only EYELID-07 graph audit. Does not infer upper/lower or canonical canthi."""
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

import bpy

def audit():
    src = Path(bpy.data.filepath)
    if not src.is_file():
        raise RuntimeError("Saved source .blend required")
    face = bpy.data.objects["Face"]
    mesh = face.data
    attr = mesh.attributes.get("elm_patch")
    if attr is None or attr.domain != "POINT":
        raise RuntimeError("elm_patch must be POINT domain")
    tags = [int(x.value) for x in attr.data]
    if len(tags) != len(mesh.vertices):
        raise RuntimeError("Vertex tag count mismatch")
    edge_faces = defaultdict(list)
    for poly in mesh.polygons:
        for edge in poly.edge_keys:
            edge_faces[tuple(sorted(edge))].append(poly.index)
    result = {}
    for side, pid in (("R", 1), ("L", 2)):
        selected = set()
        for edge, adjacent in edge_faces.items():
            a, b = edge
            if tags[a] != pid or tags[b] != pid:
                continue
            has_wall = any(any(tags[v] == pid + 10 for v in mesh.polygons[i].vertices) for i in adjacent)
            has_lid = any(all(tags[v] == pid for v in mesh.polygons[i].vertices) for i in adjacent)
            if has_wall and has_lid:
                selected.add(edge)
        graph = defaultdict(set)
        for a, b in selected:
            graph[a].add(b)
            graph[b].add(a)
        components = []
        unseen = set(graph)
        while unseen:
            start = min(unseen)
            stack = [start]
            vertices = set()
            while stack:
                v = stack.pop()
                if v in vertices:
                    continue
                vertices.add(v)
                unseen.discard(v)
                stack.extend(sorted(graph[v] - vertices, reverse=True))
            deg1 = sorted(v for v in vertices if len(graph[v]) == 1)
            forks = sorted(v for v in vertices if len(graph[v]) > 2)
            valid = not forks and len(deg1) in (0, 2)
            ordered = []
            if valid:
                cursor = min(deg1) if deg1 else min(vertices)
                prev = None
                while True:
                    ordered.append(cursor)
                    options = sorted(graph[cursor] - ({prev} if prev is not None else set()))
                    nxt = next((v for v in options if v not in ordered), None)
                    if nxt is None:
                        break
                    prev, cursor = cursor, nxt
                valid = len(ordered) == len(vertices)
            world = face.matrix_world
            coords = {str(v): [round(float(q), 9) for q in (world @ mesh.vertices[v].co)] for v in sorted(vertices)}
            components.append({"vertex_ids": sorted(vertices), "edge_ids": [list(e) for e in sorted(selected) if set(e) <= vertices],
                               "endpoint_ids": deg1, "fork_ids": forks, "ordered_vertex_ids": ordered if valid else [],
                               "graph_valid": valid, "closed_loop": len(deg1) == 0, "world_xyz_m": coords})
        result[side] = {"edge_count": len(selected), "component_count": len(components), "components": components}
    return {"status": "DIAGNOSTIC_NOT_CANON", "input_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
            "blender_version": bpy.app.version_string, "elm_patch_domain": attr.domain, "sides": result,
            "upper_lower_correspondence": "NOT_ESTABLISHED", "canthi_semantics": "NOT_ESTABLISHED",
            "G1": "PARTIAL", "G2": "NOT_RUN", "G3": "DIAGNOSTIC_ONLY", "G4": "NOT_RUN"}

def build_correspondence(report):
    """Candidate vertex-ID correspondence. No unverified anatomical labels."""
    import math
    output = {}
    for side, info in report["sides"].items():
        comps = info["components"]
        chains = [c for c in comps if c["graph_valid"] and not c["closed_loop"]
                  and len(c["endpoint_ids"]) == 2 and len(c["ordered_vertex_ids"]) >= 2]
        output[side] = {"status": "BLOCKED_AMBIGUOUS_TOPOLOGY", "candidate_chains": [],
                        "paired_samples": [], "semantic_upper_lower": "UNASSIGNED",
                        "medial_lateral_canthi": "UNASSIGNED"}
        for chain in chains:
            ids = chain["ordered_vertex_ids"]
            coords = chain["world_xyz_m"]
            distances = [0.0]
            for a, b in zip(ids, ids[1:]):
                pa, pb = coords[str(a)], coords[str(b)]
                distances.append(distances[-1] + math.dist(pa, pb))
            if distances[-1] <= 1e-10:
                continue
            output[side]["candidate_chains"].append({
                "vertex_ids": ids, "endpoint_ids": [ids[0], ids[-1]],
                "length_m": distances[-1],
                "normalized_arc_u": [round(d / distances[-1], 9) for d in distances]})
        # A single closed ring, or an unclassified number of open chains, is
        # insufficient to establish upper/lower or canthus correspondence.
        if len(output[side]["candidate_chains"]) != 2:
            continue
        a, b = output[side]["candidate_chains"]
        # Match endpoint direction by minimizing world-space endpoint distance.
        xyz = lambda chain, idx: comps[next(i for i, comp in enumerate(comps)
                           if comp["ordered_vertex_ids"] == chain["vertex_ids"])]["world_xyz_m"][str(idx)]
        forward = math.dist(xyz(a, a["vertex_ids"][0]), xyz(b, b["vertex_ids"][0])) + math.dist(
                  xyz(a, a["vertex_ids"][-1]), xyz(b, b["vertex_ids"][-1]))
        reverse = math.dist(xyz(a, a["vertex_ids"][0]), xyz(b, b["vertex_ids"][-1])) + math.dist(
                  xyz(a, a["vertex_ids"][-1]), xyz(b, b["vertex_ids"][0]))
        if abs(forward - reverse) < 1e-8:
            output[side]["status"] = "BLOCKED_ENDPOINT_ORIENTATION_TIE"
            continue
        if reverse < forward:
            b = {"vertex_ids": list(reversed(b["vertex_ids"])),
                 "normalized_arc_u": [round(1-u, 9) for u in reversed(b["normalized_arc_u"])],
                 "endpoint_ids": list(reversed(b["endpoint_ids"])), "length_m": b["length_m"]}
        def at(chain, u):
            us = chain["normalized_arc_u"]
            ids = chain["vertex_ids"]
            for i in range(len(us)-1):
                if us[i] <= u <= us[i+1]:
                    t = (u-us[i]) / (us[i+1]-us[i]) if us[i+1] > us[i] else 0
                    return {"edge_vertex_ids": [ids[i], ids[i+1]], "edge_t": round(t, 9)}
            return {"edge_vertex_ids": [ids[-2], ids[-1]], "edge_t": 1.0}
        output[side]["paired_samples"] = [{"u": round(i/32, 9), "chain_A": at(a,i/32),
                                           "chain_B": at(b,i/32)} for i in range(33)]
        output[side]["status"] = "PROVISIONAL_ARC_LENGTH_PAIRS_NOT_ANATOMICAL_APPROVAL"
    return output


def main():
    dest = Path(os.environ["EYELID_07_TOPOLOGY_JSON"]).resolve()
    if dest.exists():
        raise RuntimeError("Refusing to overwrite diagnostic")
    dest.parent.mkdir(parents=True, exist_ok=True)
    report = audit()
    report["correspondence_candidates"] = build_correspondence(report)
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({side: {"components": info["component_count"], "edges": info["edge_count"],
                            "valid": [c["graph_valid"] for c in info["components"]]}
                      for side, info in report["sides"].items()}))

if __name__ == "__main__":
    main()
