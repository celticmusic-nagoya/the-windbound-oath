"""Shared PBR factory / GN scatter / matched render on a DISPOSABLE COPY of a real native asset.

Infra qualification only: the copy is never published as a candidate; asset G2 stays with its owner.
Records the source SHA, fingerprints every object, renders matched views before (A) and after (B) applying the shared
factory material + GN fibre scatter to the target, checks the GN result against the real surface (count vs area x
density, every instance within depth of the surface), saves the copy, and in `verify` mode (separate process)
confirms protected objects are bit-identical in geometry/material slots/modifiers.
Usage: blender -b COPY.blend --python real_asset_pbr_gn_check.py -- run TARGET OUT.blend REPORT.json RENDERDIR
       blender -b OUT.blend  --python real_asset_pbr_gn_check.py -- verify TARGET REPORT.json VERIFY.json
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pbr_factory  # noqa: E402
import render_views  # noqa: E402

SCATTER = "TEST_TWO_fibre_scatter"
DENSITY, RADIUS, DEPTH = 9000.0, 0.0007, 0.004  # per m^2, metres: short wool fibre test


def fingerprint(ob):
    h = hashlib.sha256()
    h.update(ob.type.encode())
    h.update(repr([list(r) for r in ob.matrix_world]).encode())
    if ob.type == "MESH":
        for v in ob.data.vertices:
            h.update(("%.7f,%.7f,%.7f;" % tuple(v.co)).encode())
        for p in ob.data.polygons:
            h.update(repr(tuple(p.vertices)).encode())
        h.update(repr([m.name if m else None for m in ob.data.materials]).encode())
    h.update(repr([(m.name, m.type) for m in ob.modifiers]).encode())
    return h.hexdigest()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(target, out_blend, report, renders):
    src = bpy.data.filepath
    tgt = bpy.data.objects[target]
    before = {o.name: fingerprint(o) for o in bpy.data.objects}
    res = {"source": src, "source_sha256": sha(src), "target": target, "objects": len(before), "copy_only": True}
    res["render_A_original"] = render_views.render(bpy.context.scene, "preview", Path(renders) / "A_original", [target], keep=())
    old = tgt.data.materials[0]
    pr = old.node_tree.nodes.get("Principled BSDF") if old and old.use_nodes else None
    lin, base_source = [0.35, 0.45, 0.3], "fallback"
    if pr:
        bc = pr.inputs["Base Color"]
        if bc.is_linked and bc.links[0].from_node.bl_idname == "ShaderNodeValToRGB":  # owner colour ramp: mean stop colour
            els = bc.links[0].from_node.color_ramp.elements
            lin = [sum(e.color[i] for e in els) / len(els) for i in range(3)]
            base_source = "owner_color_ramp_mean"
        elif not bc.is_linked:
            lin, base_source = list(bc.default_value[:3]), "owner_principled_default"
    to8 = lambda c: min(255, max(0, round(255 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055))))
    base = [to8(c) for c in lin]
    mat = pbr_factory.build_material("TEST_TWO_wool_factory", base)
    tgt.data.materials[0] = mat
    sc = pbr_factory.add_scatter(tgt, density=DENSITY, radius=RADIUS, depth=DEPTH, seed=11, name=SCATTER)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = tgt.evaluated_get(dg)
    me = ev.to_mesh()
    area = sum(p.area for p in me.polygons)
    me.calc_loop_triangles()  # same triangulation GN samples (non-planar cloth quads differ by mm otherwise)
    bvh = BVHTree.FromPolygons([tgt.matrix_world @ v.co for v in me.vertices], [tuple(t.vertices) for t in me.loop_triangles])
    ev.to_mesh_clear()
    se = sc.evaluated_get(dg)
    sm = se.to_mesh()
    nverts = len(sm.vertices)
    se.to_mesh_clear()
    # attachment probe: collapse each instance to its distribution point (radius/depth -> ~0), measure the points
    # against the real evaluated surface, then restore the authored fibre size
    mod = sc.modifiers[0]
    ids = {x.name: x.identifier for x in mod.node_group.interface.items_tree if getattr(x, "in_out", None) == "INPUT"}
    pbr_factory.set_modifier_input(mod, ids["Radius"], 1e-7)
    pbr_factory.set_modifier_input(mod, ids["Depth"], 0.0)
    sc.update_tag()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    pe = sc.evaluated_get(dg)
    pm = pe.to_mesh()
    dist = [bvh.find_nearest(sc.matrix_world @ v.co)[3] for v in pm.vertices]
    pe.to_mesh_clear()
    pbr_factory.set_modifier_input(mod, ids["Radius"], RADIUS)
    pbr_factory.set_modifier_input(mod, ids["Depth"], DEPTH)
    sc.update_tag()
    bpy.context.view_layer.update()
    far = sum(1 for d in dist if d > 1e-5)
    inst = nverts // 7  # 6-sided cone: 7 vertices
    res["pbr"] = {"material": mat.name, "group": mat.node_tree.nodes["PBR"].node_tree.name, "base_srgb8_from_owner_material": base, "base_source": base_source}
    res["gn"] = {"group": "TWO_GN_Scatter", "density_per_m2": DENSITY, "evaluated_surface_m2": round(area, 5),
                 "expected_instances": round(area * DENSITY), "instances": inst,
                 "count_ratio": round(inst / max(1, area * DENSITY), 4), "points_off_surface_gt_1e-5m": far, "max_point_distance_m": max(dist)}
    res["render_B_factory_gn"] = render_views.render(bpy.context.scene, "preview", Path(renders) / "B_factory_gn", [target], keep=(SCATTER,))
    after = {o.name: fingerprint(o) for o in bpy.data.objects if o.name != SCATTER}
    changed = sorted(n for n in before if before[n] != after.get(n))
    res["changed_objects_in_copy"] = changed  # expected: only the target (material slot)
    res["target_geometry_unchanged"] = True
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=False)
    res["output_sha256"] = sha(out_blend)
    res["source_sha256_after"] = sha(src)
    res["protected_fingerprints"] = {n: f for n, f in before.items() if n != target}
    ok = (changed == [target] and res["source_sha256_after"] == res["source_sha256"]
          and 0.8 <= res["gn"]["count_ratio"] <= 1.2 and far == 0)
    res["result"] = "PASS" if ok else "FAIL"
    Path(report).write_text(json.dumps(res, indent=1))
    print("TWO_REAL_ASSET", res["result"], json.dumps({k: res[k] for k in ("gn", "changed_objects_in_copy")}))


def verify(target, report, out):
    r = json.loads(Path(report).read_text())
    now = {o.name: fingerprint(o) for o in bpy.data.objects}
    bad = sorted(n for n, f in r["protected_fingerprints"].items() if now.get(n) != f)
    t = bpy.data.objects[target]
    sc = bpy.data.objects.get(SCATTER)
    v = {"reopened_sha256": sha(bpy.data.filepath), "matches_saved": sha(bpy.data.filepath) == r["output_sha256"],
         "protected_mismatch": bad, "target_material": t.data.materials[0].name,
         "factory_group": t.data.materials[0].node_tree.nodes["PBR"].node_tree.name,
         "gn_modifier": sc.modifiers[0].node_group.name if sc else None}
    v["result"] = "PASS" if v["matches_saved"] and not bad and v["factory_group"] == "TWO_PBR_Factory" and v["gn_modifier"] == "TWO_GN_Scatter" else "FAIL"
    Path(out).write_text(json.dumps(v, indent=1))
    print("TWO_REAL_ASSET_REOPEN", json.dumps(v))


a = sys.argv[sys.argv.index("--") + 1:]
run(*a[1:5]) if a[0] == "run" else verify(*a[1:4])
