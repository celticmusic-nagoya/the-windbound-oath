"""Blender 5.3.0 measurement of HairHarpy lock meshes (OBJ export of the native project).

Coordinates are reported back in the blueprint frame (HairHarpy head-local, Y-up, metres): the OBJ is imported with
forward -Z / up Y, so Blender (x, y, z) = HairHarpy (x, -z, y).
Per lock: centreline length (height-band centroids), tip height, root width, min head clearance (ellipsoid).
Global: L/R asymmetry, min clearance, four-view silhouette extents, technical checks (non-manifold edges, degenerate
faces, inter-lock intersections). Optional: UV OBJ (HairHarpy Topology room) -> UV checks, PBR factory, native .blend.
Usage: blender -b --factory-startup --python hh_measure_blender.py -- MEASURE LOCKS.obj BLUEPRINT.json OUT.json
       blender -b --factory-startup --python hh_measure_blender.py -- FINISH  UV.obj BLUEPRINT.json OUT.json OUT.blend RENDERDIR
"""
import json
import math
import re
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import pbr_factory  # noqa: E402
import render_views  # noqa: E402

BAND = 0.005  # centreline band height (m)


def hh(v):
    return (v.x, v.z, -v.y)  # Blender -> HairHarpy frame


def import_obj(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=path, forward_axis="NEGATIVE_Z", up_axis="Y")
    locks = {}
    for o in bpy.data.objects:
        m = re.search(r"(L\d\d)", o.name)
        if o.type == "MESH" and m and "cocoon" in o.name.lower():
            locks[m.group(1)] = o
    return locks


def world(o):
    return [o.matrix_world @ v.co for v in o.data.vertices]


def clearance(p, ax):
    x, y, z = p
    f = math.sqrt((x / ax[0]) ** 2 + (y / ax[1]) ** 2 + (z / ax[2]) ** 2)
    g = math.sqrt((x / ax[0] ** 2) ** 2 + (y / ax[1] ** 2) ** 2 + (z / ax[2] ** 2) ** 2) or 1e-9
    return (f * f - 1) / (2 * g)  # first-order signed distance, metres


def lock_metrics(o, ax):
    """Surface length root -> tip: shortest edge path from the root band to the tip vertex (Dijkstra), the mean
    of the paths from the two root-band extremes; uncertainty ~ half the mean edge length along the lock."""
    import heapq
    pts = [hh(v) for v in world(o)]
    me = o.data
    adj = {i: [] for i in range(len(pts))}
    elen = []
    for e in me.edges:
        a, b = e.vertices
        w = math.dist(pts[a], pts[b])
        adj[a].append((b, w))
        adj[b].append((a, w))
        elen.append(w)
    top = max(p[1] for p in pts)
    tip = min(range(len(pts)), key=lambda i: pts[i][1])
    root = [i for i, p in enumerate(pts) if p[1] >= top - 0.004]
    ends = [min(root, key=lambda i: pts[i][0] + pts[i][2]), max(root, key=lambda i: pts[i][0] + pts[i][2])]

    def path(src):
        dist, q = {src: 0.0}, [(0.0, src)]
        while q:
            dd, u = heapq.heappop(q)
            if u == tip:
                return dd
            if dd > dist.get(u, 1e9):
                continue
            for v, w in adj[u]:
                if dd + w < dist.get(v, 1e9):
                    dist[v] = dd + w
                    heapq.heappush(q, (dd + w, v))
        return float("nan")
    lens = [path(s) for s in ends]
    rw = max(math.dist(pts[a], pts[b]) for a in root for b in root) if len(root) > 1 else 0.0
    return {"length": sum(lens) / 2, "length_paths": lens, "tip_y": pts[tip][1], "root_y": top, "root_width": rw,
            "min_clearance": min(clearance(p, ax) for p in pts), "edge_mean": sum(elen) / len(elen),
            "length_uncertainty": max(abs(lens[0] - lens[1]) / 2, 0.5 * sum(elen) / len(elen) * 0.25), "vertices": len(pts)}


def technical(locks):
    res = {"non_manifold_edges": 0, "degenerate_faces": 0, "loose_vertices": 0, "inter_lock_overlaps": 0}
    trees = {}
    for k, o in locks.items():
        bm = bmesh.new()
        bm.from_mesh(o.data)
        res["non_manifold_edges"] += sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
        res["degenerate_faces"] += sum(1 for f in bm.faces if f.calc_area() < 1e-10)
        res["loose_vertices"] += sum(1 for v in bm.verts if not v.link_edges)
        bm.transform(o.matrix_world)
        trees[k] = BVHTree.FromBMesh(bm)
        bm.free()
    ks = sorted(trees)
    pairs = []
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            n = len(trees[a].overlap(trees[b]))
            if n:
                pairs.append([a, b, n])
            res["inter_lock_overlaps"] += n
    res["overlap_pairs"] = pairs
    return res


def silhouettes(locks):
    pts = [hh(v) for o in locks.values() for v in world(o)]
    xs, ys, zs = ([p[i] for p in pts] for i in range(3))
    return {"front_width_x": max(xs) - min(xs), "front_height_y": max(ys) - min(ys),
            "side_depth_z": max(zs) - min(zs), "lowest_y": min(ys), "left_extent_x": -min(xs), "right_extent_x": max(xs)}


def measure(obj, bp_path, out):
    bp = json.loads(Path(bp_path).read_text())
    ax = bp["head"]["semi_axes_xyz"]
    locks = import_obj(obj)
    per = {k: lock_metrics(o, ax) for k, o in sorted(locks.items())}
    side = {lk["id"]: lk["side"] for lk in bp["locks"]}
    left = [per[k]["length"] for k in per if side.get(k) == "left"]
    right = [per[k]["length"] for k in per if side.get(k) == "right"]
    g = {"asymmetry_left_over_right": (sum(left) / len(left)) / (sum(right) / len(right)) if left and right else float("nan"),
         "min_head_clearance": min(m["min_clearance"] for m in per.values())}
    res = {"locks": per, "global": g, "technical": technical(locks), "silhouette": silhouettes(locks),
           "missing_locks": sorted(set(side) - set(per)), "blender": bpy.app.version_string}
    Path(out).write_text(json.dumps(res, indent=1, sort_keys=True))
    print("TWO_HH_MEASURE", json.dumps({k: round(v["length"], 5) for k, v in per.items()}), json.dumps(g))


def transfer_uv(locks, merged):
    """HairHarpy's Topology room merges (and welds) the import: copy its UVs back per lock by corner position."""
    from mathutils.kdtree import KDTree
    md = merged.data
    kd = KDTree(len(md.vertices))
    for v in md.vertices:
        kd.insert(merged.matrix_world @ v.co, v.index)
    kd.balance()
    corner = {}
    for p in md.polygons:
        for li in p.loop_indices:
            corner.setdefault((p.index, md.loops[li].vertex_index), li)
    face_of = {}
    for p in md.polygons:
        face_of.setdefault(frozenset(p.vertices), p.index)
    src = md.uv_layers.active.data
    stats = {}
    for k, o in locks.items():
        me = o.data
        uvl = me.uv_layers.new(name="HairHarpyUV")
        mapped = 0
        for p in me.polygons:
            ids = []
            for vi in p.vertices:
                co, j, dist = kd.find(o.matrix_world @ me.vertices[vi].co)
                ids.append(j if dist < 1e-5 else None)
            if None in ids or frozenset(ids) not in face_of:
                continue
            f = face_of[frozenset(ids)]
            for li, j in zip(p.loop_indices, ids):
                uvl.data[li].uv = src[corner[(f, j)]].uv
            mapped += 1
        stats[k] = {"faces": len(me.polygons), "mapped": mapped}
    return stats


def finish(locks_obj, uv_obj, bp_path, out, out_blend, renders):
    """UV from HairHarpy (Topology room unfold/pack) carried onto the lock meshes, UV QA, shared PBR factory,
    matched preview views, editable native .blend."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=uv_obj, forward_axis="NEGATIVE_Z", up_axis="Y")
    merged = [o for o in bpy.data.objects if o.type == "MESH"][0]
    merged.name = "HH_uv_merged"
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=locks_obj, forward_axis="NEGATIVE_Z", up_axis="Y")
    locks = {}
    for o in bpy.data.objects:
        m = re.search(r"(L\d\d)", o.name)
        if o not in before and o.type == "MESH" and m and "cocoon" in o.name.lower():
            locks[m.group(1)] = o
    tr = transfer_uv(locks, merged)
    uv = {}
    for k, o in locks.items():
        d = o.data.uv_layers["HairHarpyUV"].data
        flips = 0
        for p in o.data.polygons:
            pts = [d[i].uv for i in p.loop_indices]
            a = sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))
            flips += a < 0
        uv[k] = dict(tr[k], inside_unit=all(-1e-6 <= l.uv.x <= 1 + 1e-6 and -1e-6 <= l.uv.y <= 1 + 1e-6 for l in d),
                     flipped=int(min(flips, len(o.data.polygons) - flips)))
    bpy.data.objects.remove(merged, do_unlink=True)
    mat = pbr_factory.build_material("TWO_HH_Hair_QUAL", [70, 52, 74])
    for o in locks.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    names = sorted(o.name for o in locks.values())
    stats = render_views.render(bpy.context.scene, "preview", Path(renders), names, keep=())
    bpy.context.scene["two_hh_finish"] = "QUAL-HH-LONGHAIR-V1"
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=False)
    ok = bool(uv) and all(v["mapped"] == v["faces"] and v["inside_unit"] and v["flipped"] == 0 for v in uv.values())
    res = {"uv": uv, "uv_ok": ok, "material": mat.name, "factory_group": mat.node_tree.nodes["PBR"].node_tree.name,
           "renders": stats, "uv_source": "HairHarpy Topology room unfoldall/packall (merged, welded import)"}
    Path(out).write_text(json.dumps(res, indent=1, sort_keys=True))
    print("TWO_HH_FINISH", ok, json.dumps(uv))


a = sys.argv[sys.argv.index("--") + 1:]
measure(*a[1:4]) if a[0] == "MEASURE" else finish(*a[1:7])
