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

def main():
    dest = Path(os.environ["EYELID_07_TOPOLOGY_JSON"]).resolve()
    if dest.exists():
        raise RuntimeError("Refusing to overwrite diagnostic")
    dest.parent.mkdir(parents=True, exist_ok=True)
    report = audit()
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({side: {"components": info["component_count"], "edges": info["edge_count"],
                            "valid": [c["graph_valid"] for c in info["components"]]}
                      for side, info in report["sides"].items()}))

if __name__ == "__main__":
    main()
