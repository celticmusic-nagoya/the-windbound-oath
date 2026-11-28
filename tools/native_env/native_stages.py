"""TWO native Blender stage executor (CALIBRATION FIXTURE ONLY, never a production asset).

Usage: blender -b [IN.blend] --factory-startup --python native_stages.py -- STAGE --out OUT.blend --report R.json [--blueprint B.json]
STAGE: s1_build | s2_calibrate | s3_correct_shape | s4_material | s5_render_preview | s6_render_hq | measure
Every mutating stage measures actual evaluated geometry, saves a native checkpoint and writes a report.
Reopen verification is done by the host adapter in a separate Blender process (stage `measure`).
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_views  # noqa: E402
import pbr_factory  # noqa: E402

HEAD, HAIR, PATCH = "CAL-head", "CAL-hair_shell", "CAL-color_patch"
EYE_SK, TAPER_MOD = "EyeSpread", "HemTaper"
TOL_SHAPE = 0.002  # absolute ratio tolerance on blueprint ratios
TOL_RGB = 3  # 8-bit sRGB per channel


def args():
    a = sys.argv[sys.argv.index("--") + 1:]
    stage, opts = a[0], {}
    for i in range(1, len(a), 2):
        opts[a[i].lstrip("-")] = a[i + 1]
    return stage, opts


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------- measurement (actual evaluated geometry) ----------
def evaluated_coords(name):
    ob = bpy.data.objects[name]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ob.matrix_world
    co = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return co


def head_height():
    co = evaluated_coords(HEAD)
    zs = [c.z for c in co]
    return max(zs) - min(zs)


def eye_spacing_ratio():
    ob = bpy.data.objects[HEAD]
    co = evaluated_coords(HEAD)
    cents = []
    for g in ("eye_L", "eye_R"):
        gi = ob.vertex_groups[g].index
        idx = [v.index for v in ob.data.vertices if any(e.group == gi and e.weight > 0.5 for e in v.groups)]
        cents.append(sum(co[i].x for i in idx) / len(idx))
    return abs(cents[0] - cents[1]) / head_height()


def hem_span_ratio():
    co = evaluated_coords(HAIR)
    zmin = min(c.z for c in co)
    band = [c.x for c in co if c.z <= zmin + 0.06]
    return (max(band) - min(band)) / head_height()


def metrics():
    m = {"eye_spacing_over_head_height": eye_spacing_ratio(),
         "front_hair_hem_span_over_head_height": hem_span_ratio(),
         "head_height": head_height()}
    for name in (HEAD, HAIR):
        ob = bpy.data.objects.get(name)
        if ob:
            m["topology_" + name] = [len(ob.data.vertices), len(ob.data.edges), len(ob.data.polygons)]
    mat = bpy.data.materials.get("TWO_CAL_Hair")
    if mat:
        m["hair_base_color_linear"] = list(pbr_factory.get_base_color(mat))
    m["controls"] = controls()
    return {k: (round(v, 9) if isinstance(v, float) else v) for k, v in m.items()}


def controls():
    head = bpy.data.objects[HEAD]
    c = {"EyeSpread": head.data.shape_keys.key_blocks[EYE_SK].value}
    c["HemTaper"] = bpy.data.objects[HAIR].modifiers[TAPER_MOD].factor
    return {k: round(v, 9) for k, v in c.items()}


def set_control(name, value):
    if name == "EyeSpread":
        bpy.data.objects[HEAD].data.shape_keys.key_blocks[EYE_SK].value = value
    else:
        bpy.data.objects[HAIR].modifiers[TAPER_MOD].factor = value
    bpy.context.view_layer.update()


METRIC_OF = {"EyeSpread": eye_spacing_ratio, "HemTaper": hem_span_ratio}
RANGE_OF = {"EyeSpread": (0.0, 1.0), "HemTaper": (-0.6, 0.6)}
TARGET_KEY = {"EyeSpread": "eye_spacing_over_head_height", "HemTaper": "front_hair_hem_span_over_head_height"}


# ---------- stages ----------
def s1_build(o):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0)
    head = bpy.context.active_object
    head.name = HEAD
    head.scale = (0.82, 0.9, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    surf = head.copy()
    surf.data = head.data.copy()
    surf.name = "CAL-head_surface"
    bpy.context.collection.objects.link(surf)
    surf.hide_render = surf.hide_viewport = True
    gl, gr = head.vertex_groups.new(name="eye_L"), head.vertex_groups.new(name="eye_R")
    for v in head.data.vertices:
        x, y, z = v.co
        if y < -0.5 and 0.0 <= z <= 0.28:
            if 0.08 <= x <= 0.40:
                gl.add([v.index], 1.0, "REPLACE")
            elif -0.40 <= x <= -0.08:
                gr.add([v.index], 1.0, "REPLACE")
    head.shape_key_add(name="Basis")
    sk = head.shape_key_add(name=EYE_SK)
    sk.value = 0.0
    for g, sign in ((gl, 1), (gr, -1)):
        for v in head.data.vertices:
            if any(e.group == g.index for e in v.groups):
                sk.data[v.index].co.x += sign * 0.22
    sw = head.modifiers.new("EyeSlide", "SHRINKWRAP")  # nonlinear: eyes slide over the curved surface
    sw.target, sw.wrap_method = surf, "NEAREST_SURFACEPOINT"
    vg = head.vertex_groups.new(name="eyes")
    vg.add([v.index for v in head.data.vertices if any(e.group in (gl.index, gr.index) for e in v.groups)], 1.0, "REPLACE")
    sw.vertex_group = "eyes"
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.08)
    hair = bpy.context.active_object
    hair.name = HAIR
    hair.scale = (0.86, 0.95, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    bm = [v.index for v in hair.data.vertices if v.co.z < -0.45]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for i in bm:
        hair.data.vertices[i].select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    t = hair.modifiers.new(TAPER_MOD, "SIMPLE_DEFORM")
    t.deform_method, t.deform_axis, t.factor = "TAPER", "Z", 0.0
    keep = hair.modifiers.new("KeepOutsideHead", "SHRINKWRAP")  # nonlinear clamp
    keep.target, keep.wrap_method, keep.wrap_mode, keep.offset = surf, "NEAREST_SURFACEPOINT", "OUTSIDE_SURFACE", 0.04
    hair.modifiers.new("Solidify", "SOLIDIFY").thickness = 0.03
    for ob in (head, hair):
        ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
    bpy.ops.mesh.primitive_plane_add(size=0.6, location=(0, -3.0, 0), rotation=(1.5707963, 0, 0))
    bpy.context.active_object.name = PATCH
    return {"note": "calibration fixture; not a TWO asset"}


def s2_calibrate(o):
    out = {}
    for name, (lo, hi) in RANGE_OF.items():
        base = controls()[name]
        xs = [lo + (hi - lo) * i / 6 for i in range(7)]
        ys = []
        for x in xs:
            set_control(name, x)
            ys.append(METRIC_OF[name]())
        set_control(name, base)
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
        icpt = my - slope * mx
        ss_res = sum((y - (icpt + slope * x)) ** 2 for x, y in zip(xs, ys))
        ss_tot = sum((y - my) ** 2 for y in ys) or 1e-30
        out[name] = {"metric": TARGET_KEY[name], "samples": [[round(x, 6), round(y, 9)] for x, y in zip(xs, ys)],
                     "linear_slope": round(slope, 9), "r2": round(1 - ss_res / ss_tot, 9),
                     "max_linear_deviation": round(max(abs(y - (icpt + slope * x)) for x, y in zip(xs, ys)), 9),
                     "monotonic": all(b > a for a, b in zip(ys, ys[1:])) or all(b < a for a, b in zip(ys, ys[1:]))}
    bpy.context.scene["two_calibration"] = json.dumps(out)
    return {"response": out}


def invert(samples, target):
    for (x0, y0), (x1, y1) in zip(samples, samples[1:]):
        if min(y0, y1) <= target <= max(y0, y1) and y1 != y0:
            return x0 + (target - y0) * (x1 - x0) / (y1 - y0)
    return None


def s3_correct_shape(o):
    bp_path = Path(o["blueprint"])
    bp = json.loads(bp_path.read_text(encoding="utf-8"))
    cal = json.loads(bpy.context.scene["two_calibration"])
    res = {"blueprint": str(bp_path), "blueprint_sha256": sha(bp_path), "blueprint_status": bp.get("status"), "targets": {}}
    for name, data in cal.items():
        target = bp["metrics"][data["metric"]]
        x = invert(data["samples"], target)
        if x is None:
            raise RuntimeError("TARGET_OUTSIDE_MEASURED_RANGE:" + name)
        it, xs, rs = [], [], []
        for _ in range(8):
            set_control(name, x)
            r = METRIC_OF[name]() - target
            it.append({"control": round(x, 9), "measured": round(r + target, 9), "residual": round(r, 9)})
            xs.append(x)
            rs.append(r)
            if abs(r) <= TOL_SHAPE / 10:
                break
            if len(xs) >= 2 and rs[-1] != rs[-2]:
                x = xs[-1] - rs[-1] * (xs[-1] - xs[-2]) / (rs[-1] - rs[-2])
            else:
                x = x - r / data["linear_slope"]
            x = max(RANGE_OF[name][0], min(RANGE_OF[name][1], x))
        final = it[-1]
        if abs(final["residual"]) > TOL_SHAPE:
            raise RuntimeError("RESIDUAL_OUT_OF_TOLERANCE:" + name)
        res["targets"][data["metric"]] = {"target": target, "tolerance": TOL_SHAPE, "control": name,
                                          "initial_inverse_estimate": it[0]["control"], "iterations": it,
                                          "final_residual": final["residual"], "result": "PASS"}
    return res


def s4_material(o):
    bp = json.loads(Path(o["blueprint"]).read_text(encoding="utf-8"))
    hexv = bp["materials"]["hair_provisional_target"].lstrip("#")
    target = [int(hexv[i:i + 2], 16) for i in (0, 2, 4)]
    mat = pbr_factory.build_material("TWO_CAL_Hair", target)
    hair = bpy.data.objects[HAIR]
    hair.data.materials.clear()
    hair.data.materials.append(mat)
    patch = bpy.data.objects[PATCH]
    patch.data.materials.clear()
    patch.data.materials.append(mat)
    pbr_factory.add_scatter(hair)
    it = []
    for _ in range(6):
        got = render_views.measure_patch(bpy.context.scene, patch)
        err = [g - t for g, t in zip(got, target)]
        it.append({"base_color_linear": [round(c, 6) for c in pbr_factory.get_base_color(mat)], "measured_srgb8": got, "error": err})
        if max(abs(e) for e in err) <= TOL_RGB:
            break
        pbr_factory.correct_base_color(mat, got, target)
    if max(abs(e) for e in it[-1]["error"]) > TOL_RGB:
        raise RuntimeError("MATERIAL_RESPONSE_OUT_OF_TOLERANCE")
    return {"target_srgb8": target, "target_status": bp["materials"].get("status"), "tolerance": TOL_RGB,
            "iterations": it, "result": "PASS", "gn_scatter": pbr_factory.scatter_stats(hair)}


def s5_render_preview(o):
    return {"renders": render_views.render(bpy.context.scene, "preview", Path(o["outdir"]), [HEAD, HAIR])}


def s6_render_hq(o):
    return {"renders": render_views.render(bpy.context.scene, "hq", Path(o["outdir"]), [HEAD, HAIR])}


def main():
    stage, o = args()
    report = {"stage": stage, "blender": bpy.app.version_string, "build_hash": bpy.app.build_hash.decode() if isinstance(bpy.app.build_hash, bytes) else bpy.app.build_hash,
              "input": bpy.data.filepath or None}
    if report["input"]:
        report["input_sha256"] = sha(report["input"])
    if stage != "measure":
        report["result"] = globals()[stage](o)
        hold = float(os.environ.get("TWO_TEST_HOLD_SECONDS", "0"))  # interruption test hook only
        if hold:
            time.sleep(hold)
        bpy.context.scene["two_last_stage"] = stage
        bpy.ops.wm.save_as_mainfile(filepath=o["out"], compress=False)
        report["output"] = o["out"]
        report["output_sha256"] = sha(o["out"])
    report["metrics"] = metrics()
    report["last_stage_in_file"] = bpy.context.scene.get("two_last_stage")
    Path(o["report"]).write_text(json.dumps(report, indent=1, sort_keys=True), encoding="utf-8")
    print("TWO_STAGE_DONE", stage)


try:
    main()
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    print("TWO_STAGE_FAIL", e)
    sys.exit(3)
