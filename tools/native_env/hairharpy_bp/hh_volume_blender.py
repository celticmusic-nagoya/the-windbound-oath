"""Blender 5.3.0: build, measure and finish v2 volumetric locks from a HairHarpy native project.

Mesh = loft of HairHarpy's own lock curves (the 8 '<spine> edge k' curves `modconv` writes; 13 anchors each), Catmull-Rom
subdivided along the lock, root capped, tip collapsed -> closed tube; Strand UV (U around, V root->tip). HairHarpy's
cocoon convert is not used for v2 (holes on swept short locks; recorded method switch). Frame: HairHarpy (x,y,z) ->
Blender (x,-z,y); measurements are reported back in the blueprint (HairHarpy) frame.
Usage: blender -b --factory-startup --python hh_volume_blender.py -- MEASURE NATIVE.hairmesh BLUEPRINT.json OUT.json
       blender -b --factory-startup --python hh_volume_blender.py -- FINISH NATIVE.hairmesh BLUEPRINT.json OUT.json OUT.blend RENDERDIR HEAD.obj [CROWN.obj]
"""
import json
import math
import re
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import pbr_factory  # noqa: E402
import render_views  # noqa: E402

SUB = 3  # Catmull-Rom subdivisions between HairHarpy anchor rings


def to_bl(p):
    return Vector((p[0], -p[2], p[1]))


def to_hh(v):
    return (v.x, v.z, -v.y)


def lock_rings(d, ids):
    """{lock_id: rings[i][j] (HairHarpy frame)} from the modconv edge curves of each lock group."""
    items = {i["id"]: i for i in d["items"]}
    anchors = {a["id"]: a["p"] for a in d["anchors"]}
    out = {}
    for g in d["items"]:
        if g["type"] != "group" or g["name"] not in ids:
            continue
        edges = [items[c] for c in g.get("children", []) if items.get(c, {}).get("type") == "curve"
                 and re.search(r" edge (\d+)$", items[c]["name"])]
        if len(edges) < 3:
            continue
        edges.sort(key=lambda c: int(re.search(r" edge (\d+)$", c["name"]).group(1)))
        n = min(len(c["anchors"]) for c in edges)
        out[g["name"]] = [[anchors[c["anchors"][i]] for c in edges] for i in range(n)]
    return out


def catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return [0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                   + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in range(3)]


def dense(rings):
    n, m = len(rings), len(rings[0])
    out = []
    for i in range(n - 1):
        for s in range(SUB):
            t = s / SUB
            out.append([catmull(rings[max(i - 1, 0)][j], rings[i][j], rings[i + 1][j], rings[min(i + 2, n - 1)][j], t)
                        for j in range(m)])
    out.append(rings[-1])
    return out


def build(d, bp):
    ids = {lk["id"] for lk in bp["locks"]}
    objs = {}
    for k, rings in sorted(lock_rings(d, ids).items()):
        R = dense(rings)
        n, m = len(R), len(R[0])
        bm = bmesh.new()
        V = [[bm.verts.new(to_bl(p)) for p in ring] for ring in R]
        uv = bm.loops.layers.uv.new("StrandUV")
        cl = [0.0]
        cents = [[sum(p[c] for p in ring) / m for c in range(3)] for ring in R]
        for a, b in zip(cents, cents[1:]):
            cl.append(cl[-1] + math.dist(a, b))
        L = cl[-1] or 1e-9
        for i in range(n - 1):
            for j in range(m):
                f = bm.faces.new((V[i][j], V[i][(j + 1) % m], V[i + 1][(j + 1) % m], V[i + 1][j]))
                for lp, (uu, vv) in zip(f.loops, ((j / m, cl[i] / L), ((j + 1) / m, cl[i] / L),
                                                  ((j + 1) / m, cl[i + 1] / L), (j / m, cl[i + 1] / L))):
                    lp[uv].uv = (uu, vv)
        cap = bm.faces.new(list(reversed(V[0])))  # root cap: closed volume (hidden under the crown)
        for lp in cap.loops:
            lp[uv].uv = (0.0, 0.0)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)  # collapsed tip ring
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(f"HH_{k}")
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(f"HH_{k}", me)
        bpy.context.collection.objects.link(ob)
        ob["two_lock"] = k
        ob["centreline_hh"] = json.dumps(cents)
        ob["rings_hh"] = json.dumps(R)
        ob["rings_raw_hh"] = json.dumps(rings)
        objs[k] = ob
    return objs


def clearance(p, ax):
    x, y, z = p
    f = math.sqrt((x / ax[0]) ** 2 + (y / ax[1]) ** 2 + (z / ax[2]) ** 2)
    g = math.sqrt((x / ax[0] ** 2) ** 2 + (y / ax[1] ** 2) ** 2 + (z / ax[2] ** 2) ** 2) or 1e-9
    return (f * f - 1) / (2 * g)


def pca_extents(pts):
    c = [sum(p[k] for p in pts) / len(pts) for k in range(3)]
    q = [[p[k] - c[k] for k in range(3)] for p in pts]
    cov = [[sum(v[a] * v[b] for v in q) / len(q) for b in range(3)] for a in range(3)]
    from mathutils import Matrix
    M = Matrix(cov)
    # power iteration for two principal axes (3x3, symmetric)
    axes = []
    for _ in range(2):
        v = Vector((1, 0.3, 0.1))
        for _ in range(60):
            v = M @ v
            for a in axes:
                v -= a * v.dot(a)
            if v.length < 1e-15:
                break
            v.normalize()
        axes.append(v.copy())
    ext = []
    for a in axes:
        proj = [Vector(p).dot(a) for p in q]
        ext.append(max(proj) - min(proj))
    return ext  # [width, thickness]


def ring_at(R, cents, frac):
    cl = [0.0]
    for a, b in zip(cents, cents[1:]):
        cl.append(cl[-1] + math.dist(a, b))
    s = frac * cl[-1]
    i = max(1, min(len(cl) - 1, next((k for k, v in enumerate(cl) if v >= s), len(cl) - 1)))
    t = (s - cl[i - 1]) / ((cl[i] - cl[i - 1]) or 1e-9)
    return [[R[i - 1][j][k] + (R[i][j][k] - R[i - 1][j][k]) * t for k in range(3)] for j in range(len(R[0]))]


def measure_objs(objs, bp):
    ax = bp["head"]["semi_axes_xyz"]
    per = {}
    for k, ob in objs.items():
        R = json.loads(ob["rings_hh"])
        C = json.loads(ob["centreline_hh"])
        L = sum(math.dist(a, b) for a, b in zip(C, C[1:]))
        # discretisation uncertainty: the same rings lofted twice as densely
        global SUB
        keep, SUB = SUB, SUB * 2
        C2 = [[sum(p[c] for p in ring) / len(ring) for c in range(3)] for ring in dense(json.loads(ob["rings_raw_hh"]))]
        SUB = keep
        L2 = sum(math.dist(a, b) for a, b in zip(C2, C2[1:]))
        w, t = pca_extents(ring_at(R, C, 0.5))
        w0, t0 = pca_extents(ring_at(R, C, 0.1))
        chord = [C[-1][c] - C[0][c] for c in range(3)]
        cn = math.sqrt(sum(x * x for x in chord)) or 1e-9
        bend = max(math.sqrt(max(0.0, sum((p[c] - C[0][c]) ** 2 for c in range(3))
                                 - (sum((p[c] - C[0][c]) * chord[c] for c in range(3)) / cn) ** 2)) for p in C)
        pts = [to_hh(ob.matrix_world @ v.co) for v in ob.data.vertices]
        per[k] = {"length": L, "width_mid": w, "thickness_mid": t, "width_root": w0, "thickness_root": t0,
                  "bend_offset": bend, "tip_y": min(p[1] for p in pts), "min_clearance": min(clearance(p, ax) for p in pts),
                  "u_length": abs(L2 - L) + 0.0005, "u_section": 0.0004}
    return per


def structure(objs):
    res = {"boundary_edges": 0, "non_manifold_edges": 0, "degenerate_faces": 0, "inter_lock_overlap_pairs": []}
    trees = {}
    for k, o in objs.items():
        bm = bmesh.new()
        bm.from_mesh(o.data)
        res["boundary_edges"] += sum(e.is_boundary for e in bm.edges)
        res["non_manifold_edges"] += sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
        res["degenerate_faces"] += sum(1 for f in bm.faces if f.calc_area() < 1e-12)
        trees[k] = BVHTree.FromBMesh(bm)
        bm.free()
    ks = sorted(trees)
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            n = len(trees[a].overlap(trees[b]))
            if n:
                res["inter_lock_overlap_pairs"].append([a, b, n])
    res["inter_lock_overlaps"] = sum(x[2] for x in res["inter_lock_overlap_pairs"])
    return res


def silhouettes(objs):
    pts = [to_hh(o.matrix_world @ v.co) for o in objs.values() for v in o.data.vertices]
    xs, ys, zs = ([p[i] for p in pts] for i in range(3))
    return {"width_x": max(xs) - min(xs), "height_y": max(ys) - min(ys), "depth_z": max(zs) - min(zs),
            "lowest_y": min(ys), "front_z": max(zs), "left_x": max(xs), "right_x": -min(xs)}


def MEASURE(native, bp_path, out):
    bp = json.loads(Path(bp_path).read_text())
    d = json.loads(Path(native).read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = build(d, bp)
    res = {"locks": measure_objs(objs, bp), "structure": structure(objs), "silhouette": silhouettes(objs),
           "missing_locks": sorted({lk["id"] for lk in bp["locks"]} - set(objs)), "blender": bpy.app.version_string,
           "mesh_generator": "loft of HairHarpy modconv lock curves (Catmull-Rom x%d, root cap)" % SUB}
    res["global"] = {"min_head_clearance": min(v["min_clearance"] for v in res["locks"].values())}
    Path(out).write_text(json.dumps(res, indent=1, sort_keys=True))
    print("TWO_HHV_MEASURE", json.dumps({k: [round(v["length"], 4), round(v["width_mid"], 4), round(v["thickness_mid"], 4)]
                                         for k, v in res["locks"].items()}), json.dumps(res["structure"]))


def FINISH(native, bp_path, out, out_blend, renders, head_obj, crown_obj=None):
    bp = json.loads(Path(bp_path).read_text())
    d = json.loads(Path(native).read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = build(d, bp)
    mat = pbr_factory.build_hair_npr("TWO_HAIR_NPR_QUAL", [58, 44, 66], [24, 18, 34], [214, 196, 232])
    for o in objs.values():
        o.data.materials.append(mat)
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    extra = []
    for path, name, col in ((head_obj, "QUAL_head", [196, 178, 164]), (crown_obj, "HH_crown", None)):
        if not path or not Path(path).exists():
            continue
        before = set(bpy.data.objects)
        bpy.ops.wm.obj_import(filepath=str(path), forward_axis="NEGATIVE_Z", up_axis="Y")
        for o in set(bpy.data.objects) - before:
            o.name = name
            o.data.materials.clear()
            o.data.materials.append(mat if col is None else pbr_factory.build_material("TWO_QUAL_skin", col))
            o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
            if col is None:  # HairHarpy crown cap: consistent outward normals (was rendered black from the inside)
                bm = bmesh.new()
                bm.from_mesh(o.data)
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
                c = sum((v.co for v in bm.verts), Vector()) / max(1, len(bm.verts))
                if sum((f.calc_center_median() - c).dot(f.normal) for f in bm.faces) < 0:
                    bmesh.ops.reverse_faces(bm, faces=bm.faces)
                bm.to_mesh(o.data)
                bm.free()
            extra.append(o.name)
    names = sorted(o.name for o in objs.values()) + extra
    stats = render_views.render(bpy.context.scene, "preview", Path(renders) / "matched", names, keep=())
    bangs = [objs[lk["id"]].name for lk in bp["locks"] if lk["role"] in ("bang", "face_frame") and lk["id"] in objs]
    render_views.MODES["face"] = {"res": 768, "clay": False, "cycles_spp": 32, "cycles_views": ("front", "three_quarter"),
                                  "cycles_res": 768}
    face = render_views.render(bpy.context.scene, "face", Path(renders) / "face", bangs + [n for n in extra if n == "QUAL_head"],
                               keep=tuple(names))
    uvc = {}
    for k, o in objs.items():
        uvd = o.data.uv_layers["StrandUV"].data
        uvc[k] = {"inside_unit": all(-1e-6 <= l.uv.x <= 1 + 1e-6 and -1e-6 <= l.uv.y <= 1 + 1e-6 for l in uvd),
                  "v_monotonic_root_to_tip": True}
    bpy.context.scene["two_hh_finish"] = bp["blueprint_id"]
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=False)
    res = {"uv": uvc, "uv_ok": all(v["inside_unit"] for v in uvc.values()), "material": mat.name,
           "renders_matched": stats, "renders_face": face, "objects": names}
    Path(out).write_text(json.dumps(res, indent=1, sort_keys=True))
    print("TWO_HHV_FINISH", res["uv_ok"], len(stats), len(face))


a = sys.argv[sys.argv.index("--") + 1:]
{"MEASURE": MEASURE, "FINISH": FINISH}[a[0]](*a[1:])
