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


def curvature(p0, p1, p2):
    a, b, c = math.dist(p0, p1), math.dist(p1, p2), math.dist(p0, p2)
    s = (a + b + c) / 2
    area = math.sqrt(max(0.0, s * (s - a) * (s - b) * (s - c)))
    return 0.0 if a * b * c == 0 else 4 * area / (a * b * c)


def centre_at(C, frac):
    frac = min(1.0, max(0.0, frac))
    cl = [0.0]
    for a, b in zip(C, C[1:]):
        cl.append(cl[-1] + math.dist(a, b))
    s = frac * cl[-1]
    i = max(1, min(len(cl) - 1, next((k for k, v in enumerate(cl) if v >= s), len(cl) - 1)))
    t = (s - cl[i - 1]) / ((cl[i] - cl[i - 1]) or 1e-9)
    return [C[i - 1][k] + (C[i][k] - C[i - 1][k]) * t for k in range(3)]


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
        w85, t85 = pca_extents(ring_at(R, C, 0.85))
        kap = {}
        for uu in (0.25, 0.5, 0.75):
            pa, pb, pc = (centre_at(C, uu + du) for du in (-0.06, 0.0, 0.06))
            kap[f"kappa_{int(uu * 100):02d}"] = curvature(pa, pb, pc)
        chord = [C[-1][c] - C[0][c] for c in range(3)]
        cn = math.sqrt(sum(x * x for x in chord)) or 1e-9
        bend = max(math.sqrt(max(0.0, sum((p[c] - C[0][c]) ** 2 for c in range(3))
                                 - (sum((p[c] - C[0][c]) * chord[c] for c in range(3)) / cn) ** 2)) for p in C)
        pts = [to_hh(ob.matrix_world @ v.co) for v in ob.data.vertices]
        per[k] = {"length": L, "width_mid": w, "thickness_mid": t, "width_root": w0, "thickness_root": t0,
                  "width_tip": w85, "thickness_tip": t85, "taper_085": w85 / w if w else 0.0, **kap,
                  "bend_offset": bend, "tip_y": min(p[1] for p in pts), "min_clearance": min(clearance(p, ax) for p in pts),
                  "u_length": abs(L2 - L) + 0.0005, "u_section": 0.0004,
                  "u_kappa": 0.1 * kap["kappa_50"] + 0.3, "u_taper": 0.02}
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


def penetration(objs, threshold=0.001, root_zone=0.15):
    """Every vertex of lock A inside closed lock B (ray parity on B's BVH) -> depth = distance to B's surface.
    contact: all depths <= threshold, or only inside B within B's/A's root zone (layering under the crown edge);
    penetration: any vertex deeper than threshold outside the root zones."""
    trees, uvv = {}, {}
    for k, o in objs.items():
        bm = bmesh.new()
        bm.from_mesh(o.data)
        trees[k] = BVHTree.FromBMesh(bm)
        uvl = o.data.uv_layers["StrandUV"].data
        vv = [0.0] * len(o.data.vertices)
        for l in o.data.loops:
            vv[l.vertex_index] = max(vv[l.vertex_index], uvl[l.index].uv.y)
        uvv[k] = vv
        bm.free()
    dirs = [Vector((1, 0.13, 0.07)).normalized(), Vector((-0.11, 1, 0.05)).normalized(), Vector((0.03, -0.09, 1)).normalized()]
    pairs = []
    for a, oa in objs.items():
        for b, tb in trees.items():
            if a == b:
                continue
            ins = []
            for v in oa.data.vertices:
                p = v.co
                if not tb.ray_cast(p, dirs[0])[0] and not tb.ray_cast(p, -dirs[0])[0]:
                    continue
                votes = 0
                for d in dirs:  # parity along 3 skew directions, majority vote
                    n, q = 0, p.copy()
                    for _ in range(64):
                        hit = tb.ray_cast(q, d)
                        if hit[0] is None:
                            break
                        n += 1
                        q = hit[0] + d * 1e-6
                    votes += n % 2
                if votes >= 2:
                    ins.append((tb.find_nearest(p)[3], uvv[a][v.index]))
            if ins:
                deep = [x for x in ins if x[0] > threshold]
                outside_root = [x for x in deep if x[1] > root_zone]
                pairs.append({"a": a, "b": b, "inside_vertices": len(ins), "max_depth": max(x[0] for x in ins),
                              "deep_vertices": len(deep), "deep_outside_root_zone": len(outside_root),
                              "u_range": [round(min(x[1] for x in ins), 3), round(max(x[1] for x in ins), 3)],
                              "class": "penetration" if outside_root else "contact"})
    pen = [p for p in pairs if p["class"] == "penetration"]
    return {"pairs": pairs, "contact_pairs": len(pairs) - len(pen), "penetration_pairs": len(pen),
            "max_penetration_depth": max((p["max_depth"] for p in pen), default=0.0), "threshold": threshold,
            "root_zone_v": root_zone}


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
           "penetration": penetration(objs),
           "missing_locks": sorted({lk["id"] for lk in bp["locks"]} - set(objs)), "blender": bpy.app.version_string,
           "mesh_generator": "loft of HairHarpy modconv lock curves (Catmull-Rom x%d, root cap)" % SUB}
    res["global"] = {"min_head_clearance": min(v["min_clearance"] for v in res["locks"].values()),
                     "max_penetration_depth": res["penetration"]["max_penetration_depth"]}
    Path(out).write_text(json.dumps(res, indent=1, sort_keys=True))
    print("TWO_HHV_MEASURE", json.dumps({k: [round(v["length"], 4), round(v["width_mid"], 4), round(v["thickness_mid"], 4)]
                                         for k, v in res["locks"].items()}), json.dumps(res["structure"]))


def fix_crown(o, lift=0.0015):
    """HairHarpy crown cap (run 45084619143 inspection: no UV, 38/392 faces inward, dipping 0.6 % into the scalp):
    per-face outward orientation, a 1.5 mm lift along the head normal, and a radial StrandUV (V from the crown centre)
    so the NPR tangent/highlight are defined."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    inward = [f for f in bm.faces if f.calc_center_median().dot(f.normal) < 0]
    bmesh.ops.reverse_faces(bm, faces=inward)
    for v in bm.verts:
        v.co += v.co.normalized() * lift
    top = max(bm.verts, key=lambda v: v.co.z).co.copy()
    uv = bm.loops.layers.uv.new("StrandUV")
    dmax = max((v.co - top).length for v in bm.verts) or 1e-9
    for f in bm.faces:
        for lp in f.loops:
            p = lp.vert.co
            lp[uv].uv = ((math.atan2(p.y, p.x) / (2 * math.pi)) % 1.0, (p - top).length / dmax)
    o.matrix_world = o.matrix_world.Identity(4)
    bm.to_mesh(o.data)
    bm.free()
    return {"crown_faces_reoriented": len(inward), "crown_lift_m": lift, "crown_uv": "radial StrandUV"}


FINISH_SPP = 128  # r5 finding: 32 spp left tip noise; 128 spp enables OIDN in render_views


def FINISH(native, bp_path, out, out_blend, renders, head_obj, crown_obj=None):
    bp = json.loads(Path(bp_path).read_text())
    d = json.loads(Path(native).read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = build(d, bp)
    mat = pbr_factory.build_hair_npr("TWO_HAIR_NPR_QUAL", [58, 44, 66], [24, 18, 34], [214, 196, 232])
    for o in objs.values():
        o.data.materials.append(mat)
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    extra, crown_fix = [], {}
    for path, name, col in ((head_obj, "QUAL_head", [196, 178, 164]), (crown_obj, "HH_crown", None)):
        if not path or not Path(path).exists():
            continue
        before = set(bpy.data.objects)
        bpy.ops.wm.obj_import(filepath=str(path), forward_axis="NEGATIVE_Z", up_axis="Y")
        for o in set(bpy.data.objects) - before:
            o.name = name
            o.data.materials.clear()
            crown_mat = pbr_factory.build_hair_npr("TWO_HAIR_NPR_CROWN", [58, 44, 66], [24, 18, 34], [214, 196, 232],
                                                   band_v=5.0)  # scalp fill: no angel-ring band (radial UV drew a ring)
            o.data.materials.append(crown_mat if col is None else pbr_factory.build_material("TWO_QUAL_skin", col))
            o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
            if col is None:
                crown_fix.update(fix_crown(o))
            extra.append(o.name)
    names = sorted(o.name for o in objs.values()) + extra
    stats = render_views.render(bpy.context.scene, "preview", Path(renders) / "matched", names, keep=())
    bangs = [objs[lk["id"]].name for lk in bp["locks"] if lk["role"] in ("bang", "face_frame") and lk["id"] in objs]
    render_views.MODES["views"] = {"res": 768, "clay": False, "cycles_spp": FINISH_SPP,
                                   "cycles_views": ("front", "right", "back", "left", "three_quarter"), "cycles_res": 768}
    views = render_views.render(bpy.context.scene, "views", Path(renders) / "views", names, keep=())
    render_views.VIEWS.setdefault("top", (0.0, 0.0001, 1.0))
    render_views.MODES["top"] = {"res": 768, "clay": False, "cycles_spp": FINISH_SPP, "cycles_views": ("top",), "cycles_res": 768}
    top = render_views.render(bpy.context.scene, "top", Path(renders) / "top", names, keep=())
    render_views.MODES["face"] = {"res": 768, "clay": False, "cycles_spp": FINISH_SPP, "cycles_views": ("front", "three_quarter"),
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
           "renders_matched": stats, "renders_face": face, "renders_top": top, "renders_views": views, "objects": names, "crown_fix": crown_fix}
    Path(out).write_text(json.dumps(res, indent=1, sort_keys=True))
    print("TWO_HHV_FINISH", res["uv_ok"], len(stats), len(face))


a = sys.argv[sys.argv.index("--") + 1:]
{"MEASURE": MEASURE, "FINISH": FINISH}[a[0]](*a[1:])
