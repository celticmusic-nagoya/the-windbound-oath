"""HairHarpy -> Blender 5.3.0 round-trip QA (shape, UV, material, save/reopen).

Inputs: the .blend saved by hairharpy_bridge_receiver.py (real GUI Send), plus HairHarpy's own OBJ/FBX exports of the
same mesh after HairHarpy Topology-room UV unfold/pack. Checks per-vertex shape identity between the bridge mesh and
both file exports (Y-up -> Z-up), UV validity (range, flipped, overlap, coverage), transfers the HairHarpy UVs onto the
bridge object, applies the shared TWO_PBR_Factory material, renders matched preview views, saves a native .blend.
Usage: blender -b RECEIVED.blend --factory-startup --python hairharpy_roundtrip_qa.py -- qa UV.obj UV.fbx OUT.blend REPORT.json RENDERDIR
       blender -b OUT.blend --factory-startup --python hairharpy_roundtrip_qa.py -- measure REPORT.json
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pbr_factory  # noqa: E402
import render_views  # noqa: E402

TOL = 1e-4  # metres; HairHarpy writes fixed-point text


def mesh_stats(ob):
    me = ob.data
    st = {"vertices": len(me.vertices), "faces": len(me.polygons), "quads": sum(len(p.vertices) == 4 for p in me.polygons),
          "uv_layers": [l.name for l in me.uv_layers], "materials": [m.name if m else None for m in me.materials],
          "dimensions": [round(x, 6) for x in ob.dimensions]}
    if me.uv_layers:
        uv = me.uv_layers.active.data
        us = [d.uv for d in uv]
        st["uv_in_unit_square"] = all(-1e-6 <= u.x <= 1 + 1e-6 and -1e-6 <= u.y <= 1 + 1e-6 for u in us)
        flipped, area, tris = 0, 0.0, []
        for p in me.polygons:
            pts = [uv[i].uv for i in p.loop_indices]
            a = 0.5 * sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))
            area += abs(a)
            flipped += a < 0
            for i in range(1, len(pts) - 1):
                tris.append((pts[0].copy(), pts[i].copy(), pts[i + 1].copy()))
        st["uv_flipped_faces"] = int(min(flipped, len(me.polygons) - flipped))  # orientation-consistent shells
        st["uv_coverage"] = round(area, 5)
        st["uv_overlap_samples"] = overlap(tris)
    return st


def overlap(tris, n=96):
    """Rasterise UV triangles on an n x n grid; count cells covered by more than one face's triangles."""
    grid = {}
    for k, (a, b, c) in enumerate(tris):
        face = k  # adjacent triangles of the same quad share an edge, counted once by centre test
        xs, ys = [a.x, b.x, c.x], [a.y, b.y, c.y]
        for i in range(max(0, int(min(xs) * n)), min(n, int(max(xs) * n) + 1)):
            for j in range(max(0, int(min(ys) * n)), min(n, int(max(ys) * n) + 1)):
                px, py = (i + 0.5) / n, (j + 0.5) / n
                d1 = (px - b.x) * (a.y - b.y) - (a.x - b.x) * (py - b.y)
                d2 = (px - c.x) * (b.y - c.y) - (b.x - c.x) * (py - c.y)
                d3 = (px - a.x) * (c.y - a.y) - (c.x - a.x) * (py - a.y)
                if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
                    grid.setdefault((i, j), set()).add(face)
    return sum(1 for v in grid.values() if len(v) > 1)


def correspondence(a, b):
    """Order-independent vertex match (HairHarpy re-orders vertices on file export): a-index -> (b-index, distance)."""
    from mathutils.kdtree import KDTree
    if len(a.data.vertices) != len(b.data.vertices):
        return None
    kd = KDTree(len(b.data.vertices))
    for v in b.data.vertices:
        kd.insert(b.matrix_world @ v.co, v.index)
    kd.balance()
    m = {}
    for v in a.data.vertices:
        co, i, d = kd.find(a.matrix_world @ v.co)
        m[v.index] = (i, d)
    return m if len({i for i, _ in m.values()}) == len(m) else None


def max_dev(a, b):
    m = correspondence(a, b)
    return None if m is None else max(d for _, d in m.values())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def qa(uv_obj, uv_fbx, out_blend, report, renders):
    src = bpy.data.filepath
    hair = [o for o in bpy.data.collections["HairMesh"].objects]
    assert len(hair) == 1, "expected one GUI-sent mesh"
    hair = hair[0]
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=uv_obj, forward_axis="NEGATIVE_Z", up_axis="Y")
    o_obj = [o for o in bpy.data.objects if o not in before][0]
    o_obj.name = "HH_export_obj"
    before = set(bpy.data.objects)
    # HairHarpy v2.0.0 FBX: metre-valued coordinates under a centimetre unit header -> Blender imports at 0.01;
    # compensate x100 and report it (finding, not a fix of the source file)
    bpy.ops.import_scene.fbx(filepath=uv_fbx, global_scale=100.0)
    o_fbx = [o for o in bpy.data.objects if o not in before and o.type == "MESH"][0]
    o_fbx.name = "HH_export_fbx"
    bpy.context.view_layer.update()
    res = {"fbx_import_global_scale": 100.0, "source_blend": src, "source_blend_sha256": sha(src), "uv_obj_sha256": sha(uv_obj), "uv_fbx_sha256": sha(uv_fbx),
           "bridge_mesh": mesh_stats(hair), "obj_export": mesh_stats(o_obj), "fbx_export": mesh_stats(o_fbx),
           "max_vertex_deviation_bridge_vs_obj": max_dev(hair, o_obj), "max_vertex_deviation_bridge_vs_fbx": max_dev(hair, o_fbx)}
    m = correspondence(hair, o_obj)
    faces_b = {frozenset(p.vertices): p for p in o_obj.data.polygons}
    mapped = 0
    if m:  # carry HairHarpy's UVs onto the GUI-sent object through the vertex correspondence
        uvl = hair.data.uv_layers.new(name="HairHarpyUV")
        src_uv = o_obj.data.uv_layers.active.data
        for p in hair.data.polygons:
            q = faces_b.get(frozenset(m[v][0] for v in p.vertices))
            if q is None:
                continue
            corner = {o_obj.data.loops[li].vertex_index: li for li in q.loop_indices}
            for li in p.loop_indices:
                uvl.data[li].uv = src_uv[corner[m[hair.data.loops[li].vertex_index][0]]].uv
            mapped += 1
    res["uv_transfer_faces_mapped"] = mapped
    mat = pbr_factory.build_material("TWO_HH_Hair", [107, 66, 107])
    hair.data.materials.clear()
    hair.data.materials.append(mat)
    for o in (o_obj, o_fbx):
        o.hide_render = True
    res["bridge_mesh_after"] = mesh_stats(hair)
    res["renders"] = render_views.render(bpy.context.scene, "preview", Path(renders), [hair.name])
    bpy.context.scene["two_hh_qa"] = "roundtrip"
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=False)
    res["output_blend"] = out_blend
    res["output_blend_sha256"] = sha(out_blend)
    d = [res["max_vertex_deviation_bridge_vs_obj"], res["max_vertex_deviation_bridge_vs_fbx"]]
    a = res["bridge_mesh_after"]
    res["checks"] = {
        "shape_bridge_eq_obj": d[0] is not None and d[0] <= TOL,
        "shape_bridge_eq_fbx": d[1] is not None and d[1] <= TOL,
        "uv_present": bool(a.get("uv_layers")), "uv_all_faces_mapped": res["uv_transfer_faces_mapped"] == a["faces"], "uv_in_unit_square": a.get("uv_in_unit_square") is True,
        "uv_no_flips": a.get("uv_flipped_faces") == 0, "uv_no_overlap": a.get("uv_overlap_samples") == 0,
        "fbx_uv_present": bool(res["fbx_export"]["uv_layers"]),
        "material_factory_applied": a["materials"] == ["TWO_HH_Hair"] and mat.node_tree.nodes["PBR"].node_tree.name == "TWO_PBR_Factory"}
    res["result"] = "PASS" if all(res["checks"].values()) else "FAIL"
    Path(report).write_text(json.dumps(res, indent=1))
    print("TWO_HH_ROUNDTRIP", res["result"], json.dumps(res["checks"]))


def measure(report):
    hair = bpy.data.collections["HairMesh"].objects[0]
    st = mesh_stats(hair)
    st["material_group"] = hair.data.materials[0].node_tree.nodes["PBR"].node_tree.name
    st["marker"] = bpy.context.scene.get("two_hh_qa")
    st["source_sha256"] = sha(bpy.data.filepath)
    Path(report).write_text(json.dumps(st, indent=1))
    print("TWO_HH_REOPEN", json.dumps(st))


a = sys.argv[sys.argv.index("--") + 1:]
if a[0] == "qa":
    qa(*a[1:6])
else:
    measure(a[1])
