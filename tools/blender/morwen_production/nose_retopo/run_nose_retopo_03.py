"""MORWEN-LOCAL-RETOPO-03: build the nose candidate, render fixed-camera evidence and run technical QA.

Writes to $MORWEN_OUT (default render_output/morwen_local_retopo_03):
  NOSE_RETOPO_03_REPORT.json       all metrics and gate statements
  renders/<set>/<view>.png         fixed-camera close-ups (clay / wire / original)
  SHEET_*.png                      labelled sheets (baseline vs candidate, design range,
                                   expressions, 3D-target and calibrated Layer 0 comparisons)
  MORWEN_NOSE_RETOPO_03_CANDIDATE.blend   derived review file (artifact only, never committed)
Never claims G2 PASS; the source VRM SHA is asserted unchanged.
"""
import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


B = _load(HERE / "build_nose_retopo_03.py", "morwen_nose_build")
M3 = B.M3
CMP = _load(HERE.parent / "head_landmark" / "compare_head_landmarks.py", "morwen_cmp")
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_local_retopo_03"))
CMP.OUT = OUT
M3.OUT = OUT
TARGET = Path(os.environ.get("MORWEN_TARGET_PNG", "render_output/target/file_00000000301c8209af49625fd11d7670.png"))
TARGET_SHA = "7640822cfeb6c3de5b988a79e438babfaf7e3dafbdbc8433ae6cde78f3988957"
RES = int(os.environ.get("MORWEN_RES", "640"))
VIEWS = {"front": (0, 1, 0), "right": (1, 0, 0), "left": (-1, 0, 0),
         "q3L": (-0.70711, 0.70711, 0), "q3R": (0.70711, 0.70711, 0)}
CLOSE_SCALE = 0.10
FACE_SCALE = 0.24
BG = (232, 232, 228)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- render infrastructure
class Stage:
    def __init__(self, centre):
        sc = bpy.context.scene
        self.sc = sc
        for o in sc.objects:
            if o.users_collection and o.users_collection[0].name == "glTF_not_exported":
                o.hide_render = True
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.seed = 20261114
        if hasattr(sc.cycles, "use_denoising"):
            sc.cycles.use_denoising = False
        sc.render.film_transparent = True
        sc.view_settings.view_transform = "Standard"
        w = bpy.data.worlds.new("NOSE_WORLD")
        w.use_nodes = True
        self.bg = w.node_tree.nodes["Background"]
        sc.world = w
        self.sun = bpy.data.objects.new("NOSE_KEY", bpy.data.lights.new("NOSE_KEY", "SUN"))
        self.sun.data.energy = 3.0
        sc.collection.objects.link(self.sun)
        self.cam = bpy.data.objects.new("NOSE_CAM", bpy.data.cameras.new("NOSE_CAM"))
        self.cam.data.type = "ORTHO"
        self.cam.data.clip_end = 10
        sc.collection.objects.link(self.cam)
        self.centre = centre
        self.lit_cache = {}
        self.clay = self._clay(0.0)
        self.wire = self._clay(0.75)
        self.records = []

    def _clay(self, wire):
        m = bpy.data.materials.new("NOSE_CLAY_WIRE" if wire else "NOSE_CLAY")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        b = nt.nodes.new("ShaderNodeBsdfDiffuse")
        b.inputs["Color"].default_value = (0.62, 0.55, 0.50, 1)
        o = nt.nodes.new("ShaderNodeOutputMaterial")
        if not wire:
            nt.links.new(b.outputs[0], o.inputs["Surface"])
            return m
        wf = nt.nodes.new("ShaderNodeWireframe")
        wf.use_pixel_size = True
        wf.inputs["Size"].default_value = wire
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = (0.05, 0.05, 0.1, 1)
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(wf.outputs[0], mx.inputs[0])
        nt.links.new(b.outputs[0], mx.inputs[1])
        nt.links.new(e.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], o.inputs["Surface"])
        return m

    def lit(self, mat):
        """Imported texture as base colour of a lit diffuse surface (the VRM import is unlit)."""
        if mat is None:
            return self.clay
        if mat.name not in self.lit_cache:
            m = bpy.data.materials.new("LIT_" + mat.name)
            m.use_nodes = True
            nt = m.node_tree
            nt.nodes.clear()
            b = nt.nodes.new("ShaderNodeBsdfPrincipled")
            b.inputs["Roughness"].default_value = 0.7
            img = next((n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
            if img is not None:
                t = nt.nodes.new("ShaderNodeTexImage")
                t.image = img
                nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
                nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
            o = nt.nodes.new("ShaderNodeOutputMaterial")
            nt.links.new(b.outputs[0], o.inputs["Surface"])
            self.lit_cache[mat.name] = m
        return self.lit_cache[mat.name]

    def materials(self, mode, originals):
        for o in self.sc.objects:
            if o.type != "MESH":
                continue
            for i, s in enumerate(o.material_slots):
                if mode == "original":
                    s.material = originals[o.name][i]
                elif mode == "lit":
                    s.material = self.lit(originals[o.name][i])
                else:
                    s.material = self.clay if mode == "clay" else self.wire

    def shot(self, set_name, view, mode, originals, scale=CLOSE_SCALE, res=RES):
        sc = self.sc
        self.materials(mode, originals)
        sc.render.resolution_x = sc.render.resolution_y = res
        sc.cycles.samples = 6 if mode == "original" else 24
        if mode == "original":
            self.bg.inputs["Strength"].default_value = 0.0
            self.sun.hide_render = True
        else:
            self.bg.inputs["Color"].default_value = (0.8, 0.8, 0.8, 1)
            self.bg.inputs["Strength"].default_value = 0.6
            self.sun.hide_render = False
        d = Vector(VIEWS[view]).normalized()
        self.cam.data.ortho_scale = scale
        self.cam.location = self.centre + d * 1.5
        self.cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        k = (d + Vector((-d.y, d.x, 0)) * 0.5 + Vector((0, 0, 0.7))).normalized()
        self.sun.rotation_euler = (-k).to_track_quat("-Z", "Y").to_euler()
        sc.camera = self.cam
        tag = "" if scale == CLOSE_SCALE else "_face"
        f = OUT / "renders" / set_name / f"{view}_{mode}{tag}.png"
        f.parent.mkdir(parents=True, exist_ok=True)
        sc.render.filepath = str(f.resolve())
        bpy.ops.render.render(write_still=True)
        Image.open(f).save(f)  # strip timing metadata
        self.records.append(str(f.relative_to(OUT)))
        return f


# ---------------------------------------------------------------- metrics
def world_verts(obj, coords=None):
    mw = obj.matrix_world
    co = coords if coords is not None else np.array([v.co[:] for v in obj.data.vertices])
    return (np.hstack([co, np.ones((len(co), 1))]) @ np.array(mw).T)[:, :3]


def tri_normals(P, tris):
    a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    n = np.cross(b - a, c - a)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def patch_geometry_stats(face, patch, coords, base_coords=None):
    """Dihedral / fold / stretch metrics for faces touching the patch at the given coordinates."""
    me = face.data
    P = world_verts(face, coords)
    polys = [p for p in me.polygons if any(v in patch for v in p.vertices)]
    pidx = {p.index for p in polys}
    edge_faces = {}
    for p in polys:
        for ek in p.edge_keys:
            edge_faces.setdefault(ek, []).append(p.index)
    # polygon normals (Newell) at the given coordinates
    def pn(poly):
        vs = P[list(poly.vertices)]
        n = np.zeros(3)
        for i in range(len(vs)):
            a, b = vs[i], vs[(i + 1) % len(vs)]
            n += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
        return n / max(np.linalg.norm(n), 1e-12)
    normals = {p.index: pn(p) for p in polys}
    allp = {}  # outside neighbours across the patch border
    for p in me.polygons:
        for ek in p.edge_keys:
            if ek in edge_faces and p.index not in pidx:
                edge_faces[ek].append(p.index)
                allp[p.index] = p
    for i, p in allp.items():
        normals[i] = pn(p)
    inner, border = [], []
    for ek, fs in edge_faces.items():
        if len(fs) != 2:
            continue
        ang = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(normals[fs[0]], normals[fs[1]]))))))
        (inner if all(f in pidx for f in fs) else border).append(ang)
    out = {"faces": len(polys), "inner_dihedral_deg_max": round(max(inner), 3),
           "inner_dihedral_deg_p95": round(float(np.percentile(inner, 95)), 3),
           "border_dihedral_deg_max": round(max(border), 3) if border else None,
           "non_manifold_edges": sum(1 for fs in edge_faces.values() if len(fs) > 2)}
    if base_coords is not None:
        Pb = world_verts(face, base_coords)
        folds, ratios = 0, []
        for p in polys:
            vs = list(p.vertices)
            nb = Pb[vs]
            n0 = np.zeros(3)
            for i in range(len(nb)):
                a, b = nb[i], nb[(i + 1) % len(nb)]
                n0 += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
            if np.dot(n0, normals[p.index]) < 0:
                folds += 1
            for i in range(len(vs)):
                l0 = np.linalg.norm(Pb[vs[i]] - Pb[vs[(i + 1) % len(vs)]])
                if l0 > 1e-7:
                    ratios.append(np.linalg.norm(P[vs[i]] - P[vs[(i + 1) % len(vs)]]) / l0)
        out["folded_vs_basis"] = folds
        out["edge_ratio_p1"] = round(float(np.percentile(ratios, 1)), 4)
        out["edge_ratio_p99"] = round(float(np.percentile(ratios, 99)), 4)
    return out


def winding_conflicts(face, patch):
    me = face.data
    dirs = {}
    for p in me.polygons:
        if not any(v in patch for v in p.vertices):
            continue
        vs = list(p.vertices)
        for i in range(len(vs)):
            a, b = vs[i], vs[(i + 1) % len(vs)]
            dirs.setdefault(tuple(sorted((a, b))), []).append((a, b))
    return sum(1 for d in dirs.values() if len(d) == 2 and d[0] == d[1])


def centre_profile(face, coords, tip_z):
    tri = M3.face_skin_triangles(face)
    if coords is not None:
        P = world_verts(face, coords)
        me = face.data
        si = M3.slot_index(face, "Face_00_SKIN")
        idx = np.array([t.vertices[:] for t in me.loop_triangles if t.material_index == si])
        tri = P[idx]
    pts = M3.slice_plane(tri, 0, M3.MID_X)
    pts = pts[(pts[:, 2] > tip_z - 0.03) & (pts[:, 2] < tip_z + 0.04)]
    front = {}
    for q in pts:  # front-most y per 0.25 mm z bin
        k = round(q[2] * 4000)
        if k not in front or q[1] > front[k][1]:
            front[k] = q
    prof = np.array(sorted(front.values(), key=lambda q: q[2]))
    i = int(np.argmax(prof[:, 1]))
    near = prof[np.abs(prof[:, 2] - prof[i, 2]) < 0.003]
    # algebraic circle fit in (z, y)
    A = np.c_[2 * near[:, 2], 2 * near[:, 1], np.ones(len(near))]
    bb = near[:, 2] ** 2 + near[:, 1] ** 2
    cz, cy, c = np.linalg.lstsq(A, bb, rcond=None)[0]
    radius = math.sqrt(max(c + cz * cz + cy * cy, 0))
    rounded = radius < 0.02  # a corner (fan tip) gives an ill-conditioned, very large fit
    return {"tip_y": round(float(prof[i, 1]), 5), "tip_z": round(float(prof[i, 2]), 5),
            "tip_radius_mm_circle_fit_pm3mm": round(radius * 1000, 2) if rounded else None,
            "tip_shape": "rounded" if rounded else "corner (circle fit ill-conditioned)",
            "profile_points": [[round(float(q[2]), 5), round(float(q[1]), 5)] for q in prof]}


# ---------------------------------------------------------------- sheets
def label(img, text):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width, 15], fill=(255, 255, 255))
    d.text((4, 2), text, fill=(0, 0, 0))
    return img


def tile(path, size):
    im = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
    bg = Image.new("RGBA", im.size, BG + (255,))
    bg.alpha_composite(im)
    return bg.convert("RGB")


def grid(rows, size, dst, title):
    """rows: list of (row_label, [(cell_label, path or PIL image)])."""
    ncol = max(len(r[1]) for r in rows)
    sheet = Image.new("RGB", (ncol * size, len(rows) * size + 18), BG)
    ImageDraw.Draw(sheet).text((4, 3), title, fill=(0, 0, 0))
    for j, (rl, cells) in enumerate(rows):
        for i, (cl, src) in enumerate(cells):
            im = tile(src, size) if not isinstance(src, Image.Image) else src.resize((size, size), Image.LANCZOS).convert("RGB")
            label(im, f"{rl} | {cl}")
            sheet.paste(im, (i * size, 18 + j * size))
    sheet.save(dst)
    return dst


# ---------------------------------------------------------------- main
def main():
    params = json.loads(B.PARAMS_PATH.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    M3.load()
    face, body = bpy.data.objects["Face"], bpy.data.objects["Body"]
    originals = {o.name: [s.material for s in o.material_slots] for o in bpy.context.scene.objects if o.type == "MESH"}
    base_lm = M3.measure()
    L0 = base_lm["landmarks"]
    tip0 = Vector(L0["pronasale"]["position"])
    centre = Vector((M3.MID_X, tip0.y - 0.02, tip0.z + 0.004))
    st = Stage(centre)

    # baseline evidence before any edit
    face.data.calc_loop_triangles()
    body_hash0 = hashlib.sha256(np.array([v.co[:] for v in body.data.vertices]).tobytes()).hexdigest()
    me0 = face.data
    old_faces = {}
    for p in me0.polygons:
        old_faces[tuple(sorted(tuple(round(c, 7) for c in me0.vertices[v].co) for v in p.vertices))] = p.material_index
    base_profile = centre_profile(face, None, tip0.z)
    for v in VIEWS:
        st.shot("baseline", v, "clay", originals)
        st.shot("baseline", v, "wire", originals)
    st.shot("baseline", "q3L", "original", originals)
    st.shot("baseline", "front", "original", originals)

    # same region as the build, measured on the ORIGINAL mesh (relative acceptance baseline)
    si0 = M3.slot_index(face, "Face_00_SKIN")
    td0 = B.Teardrop(tip0, Vector(L0["nasion"]["position"]), params["region"])
    co_w0 = [face.matrix_world @ v.co for v in me0.vertices]
    region0, _ = B.select_region(face, td0, params, si0, co_w0)
    region_v0 = {v for i in region0 for v in me0.polygons[i].vertices}
    keys0 = me0.shape_keys.key_blocks
    basis0 = np.array([v.co[:] for v in keys0[0].data])
    base_geom = patch_geometry_stats(face, region_v0, basis0)
    base_geom.pop("folded_vs_basis", None)
    base_keys = {}
    rv0 = np.array(sorted(region_v0))
    for kb in keys0[1:]:
        co = np.array([v.co[:] for v in kb.data])
        off = float(np.linalg.norm(co - basis0, axis=1)[rv0].max())
        if off > params["expression_checks"]["affected_threshold_m"]:
            g = patch_geometry_stats(face, region_v0, co, basis0)
            base_keys[kb.name] = {"folded": g["folded_vs_basis"], "edge_ratio_p99": g["edge_ratio_p99"],
                                  "inner_dihedral_deg_max": g["inner_dihedral_deg_max"], "max_offset_m": round(off, 6)}
    for v in ("front", "q3L"):
        st.shot("baseline", v, "lit", originals, scale=FACE_SCALE)
    st.shot("baseline", "q3L", "clay", originals, scale=FACE_SCALE)

    st.materials("original", originals)  # build/measure locate parts by material name
    rec = B.build(params)
    me = face.data
    me.calc_loop_triangles()
    patch = set(rec["patch_vertex_indices"])
    loopv = rec["boundary_vertex_indices"]
    keys = me.shape_keys.key_blocks
    basis = np.array([v.co[:] for v in keys[0].data])
    design = np.array([v.co[:] for v in keys[params["design_range"]["shape_key_name"]].data])

    # ---- technical checks -------------------------------------------------------------------
    new_faces = {}
    for p in me.polygons:
        new_faces[tuple(sorted(tuple(round(c, 7) for c in me.vertices[v].co) for v in p.vertices))] = p.material_index
    kept = [k for k in old_faces if k in new_faces and old_faces[k] == new_faces[k]]
    untouched_expected = len(old_faces) - rec["region_faces"]
    body_hash1 = hashlib.sha256(np.array([v.co[:] for v in body.data.vertices]).tobytes()).hexdigest()
    # Face/Body seam
    bw = world_verts(body)
    kd = KDTree(len(bw))
    for i, q in enumerate(bw):
        kd.insert(q, i)
    kd.balance()
    fw = world_verts(face)
    seam = [kd.find(q)[2] for q in fw if kd.find(q)[2] < 1e-4]
    # UV
    uvl = me.uv_layers.active.data
    si = M3.slot_index(face, "Face_00_SKIN")
    def uv_area(poly):
        u = [uvl[li].uv for li in poly.loop_indices]
        return sum(u[i].x * u[(i + 1) % len(u)].y - u[(i + 1) % len(u)].x * u[i].y for i in range(len(u))) / 2
    skin_sign = np.sign(np.median([uv_area(p) for p in me.polygons if p.material_index == si and not any(v in patch for v in p.vertices)]))
    patch_polys = [p for p in me.polygons if any(v in patch for v in p.vertices)]
    uv_flips = sum(1 for p in patch_polys if np.sign(uv_area(p)) != skin_sign)
    uv_out = sum(1 for p in patch_polys for li in p.loop_indices if not (0 <= uvl[li].uv.x <= 1 and 0 <= uvl[li].uv.y <= 1))
    # weights
    new_only = sorted(patch - set(loopv))
    wsum = [sum(g.weight for g in me.vertices[i].groups) for i in new_only]
    dom = {}
    for i in new_only:
        g = max(me.vertices[i].groups, key=lambda g: g.weight)
        dom[face.vertex_groups[g.group].name] = dom.get(face.vertex_groups[g.group].name, 0) + 1
    # expressions
    exp_rows = {}
    thr = params["expression_checks"]["affected_threshold_m"]
    idx_of = params["expression_checks"]["vrm_preset_to_target_index"]
    preset_of = {f"target_{v}": k for k, v in idx_of.items()}
    region_pts = np.array(sorted(patch))
    for kb in keys[1:]:
        if kb.name == params["design_range"]["shape_key_name"]:
            continue
        co = np.array([v.co[:] for v in kb.data])
        off = np.linalg.norm(co - basis, axis=1)[region_pts].max()
        row = {"preset": preset_of.get(kb.name), "max_patch_offset_m": round(float(off), 6)}
        if off <= thr:
            row["status"] = "UNAFFECTED"
        else:
            g = patch_geometry_stats(face, patch, co, basis)
            row.update({"folded": g["folded_vs_basis"], "edge_ratio_p99": g["edge_ratio_p99"],
                        "inner_dihedral_deg_max": g["inner_dihedral_deg_max"]})
            b0 = base_keys.get(kb.name)
            row["baseline"] = b0
            acc_ = params["acceptance_technical"]
            ok = (b0 is not None and g["folded_vs_basis"] <= b0["folded"]
                  and g["edge_ratio_p99"] <= b0["edge_ratio_p99"] * acc_["relative_edge_ratio_margin"]
                  and g["inner_dihedral_deg_max"] <= b0["inner_dihedral_deg_max"] + acc_["relative_dihedral_margin_deg"])
            reviewed = row["preset"] in params["expression_checks"]["render_presets"]
            row["status"] = ("TECH_PASS_RENDERED" if reviewed else "BLOCKED_TRANSFER_UNREVIEWED") if ok else "FAIL"
        exp_rows[kb.name] = row

    # ---- design range ------------------------------------------------------------------------
    design_rows = {}
    U = base_lm["normalisation"]["unit_U_m"]
    pupil_y = L0["pupil_R"]["position"][1]
    for d in params["design_range"]["render_values"]:
        co = basis + d * (design - basis)
        g = patch_geometry_stats(face, patch, co, basis if d else None)
        prof = centre_profile(face, co, tip0.z)
        design_rows[str(d)] = {"geometry": g, "tip": {k: v for k, v in prof.items() if k != "profile_points"},
                               "nose_projection_from_pupil_U": round((prof["tip_y"] - pupil_y) / U, 4),
                               "profile_points": prof["profile_points"]}
    canon_side = {}
    l2 = json.loads((OUT / "CANONICAL_LANDMARKS_2D.json").read_text()) if (OUT / "CANONICAL_LANDMARKS_2D.json").is_file() else None

    # ---- renders: candidate ------------------------------------------------------------------
    dk = keys[params["design_range"]["shape_key_name"]]
    for d in params["design_range"]["render_values"]:
        dk.value = d
        for v in VIEWS:
            st.shot(f"candidate_d{d}", v, "clay", originals)
        st.shot(f"candidate_d{d}", "q3L", "original", originals)
        for v in ("front", "q3L"):
            st.shot(f"candidate_d{d}", v, "lit", originals, scale=FACE_SCALE)
        st.shot(f"candidate_d{d}", "q3L", "clay", originals, scale=FACE_SCALE)
    dk.value = 0.0
    for v in VIEWS:
        st.shot("candidate_d0.0", v, "wire", originals)
    st.shot("candidate_d0.0", "front", "original", originals)
    for preset in params["expression_checks"]["render_presets"]:
        kb = keys[f"target_{idx_of[preset]}"]
        kb.value = 1.0
        st.shot(f"expr_{preset}", "front", "clay", originals)
        st.shot(f"expr_{preset}", "q3L", "clay", originals)
        st.shot(f"expr_{preset}", "front", "original", originals)
        kb.value = 0.0

    # ---- calibrated Layer 0 comparison (same calibration as LANDMARK-02) ---------------------
    l3b = json.loads((OUT / "HEAD_LANDMARKS_3D.json").read_text())
    cal = {}
    if l2 is not None:
        mp = CMP.Mapping(l3b, l2)
        for d in params["design_range"]["render_values"]:
            co = basis + d * (design - basis)
            saved = np.array([v.co[:] for v in me.vertices])
            me.vertices.foreach_set("co", co.ravel())
            me.update()
            st.materials("original", originals)
            cand = M3.measure()
            me.vertices.foreach_set("co", saved.ravel())
            me.update()
            mp.L = {k: Vector(v["position"]) for k, v in cand["landmarks"].items()}
            mp.st3 = {k: v["status"] for k, v in cand["landmarks"].items()}
            rows = CMP.compare(mp)
            dk.value = d
            st.materials("original", originals)
            renders = CMP.render(mp, reload=False, tag=f"_NOSE_D{d}")
            CMP.draw(mp, renders, rows, tag=f"_NOSE_D{d}")
            cal[str(d)] = {r["view"] + ":" + r["landmark"]: r["delta_U"] for r in rows
                           if "delta_U" in r and r["landmark"] in ("pronasale", "chin_profile", "stomion", "menton")}
            canon_side[str(d)] = {"note": "2D side drawing value is a reference only, NOT a 3D target"}
        dk.value = 0.0

    # ---- sheets --------------------------------------------------------------------------------
    R = OUT / "renders"
    order = list(VIEWS)
    grid([("baseline VRoid", [(v, R / "baseline" / f"{v}_clay.png") for v in order])] +
         [(f"candidate depth {d}", [(v, R / f"candidate_d{d}" / f"{v}_clay.png") for v in order])
          for d in params["design_range"]["render_values"]],
         320, OUT / "SHEET_NOSE_CLAY_DESIGN_RANGE.png",
         "MORWEN-LOCAL-RETOPO-03 clay, fixed ortho cameras (scale 0.10 m), depth = MORWEN_DESIGN_NoseDepth")
    grid([("baseline VRoid", [(v, R / "baseline" / f"{v}_wire.png") for v in order]),
          ("candidate depth 0", [(v, R / "candidate_d0.0" / f"{v}_wire.png") for v in order])],
         320, OUT / "SHEET_NOSE_WIRE.png", "Wireframe: baseline fan tip vs ring patch")
    grid([(p_, [("front clay", R / f"expr_{p_}" / "front_clay.png"), ("q3L clay", R / f"expr_{p_}" / "q3L_clay.png"),
                ("front original", R / f"expr_{p_}" / "front_original.png")])
          for p_ in params["expression_checks"]["render_presets"]],
         320, OUT / "SHEET_NOSE_EXPRESSIONS.png", "Expression keys at 1.0 on the candidate (depth 0)")
    tgt_rows = []
    if TARGET.is_file():
        assert sha(TARGET) == TARGET_SHA, "3D target PNG SHA mismatch"
        t = Image.open(TARGET).convert("RGB")
        close = t.crop((1140, 20, 1536, 420))
        exprs = [t.crop((18 + i * 124, 740, 136 + i * 124, 1000)) for i in range(4)]
        tgt_rows = [("3D TARGET (uncalibrated crop)", [("3/4 close-up", close)] + [(f"expression {i+1}", e) for i, e in enumerate(exprs)]),
                    ("candidate LIT texture preview (not final shading)", [("q3L depth 0", R / "candidate_d0.0" / "q3L_lit_face.png"),
                                               ("q3L depth 0.5", R / "candidate_d0.5" / "q3L_lit_face.png"),
                                               ("q3L depth 1.0", R / "candidate_d1.0" / "q3L_lit_face.png"),
                                               ("front depth 0", R / "candidate_d0.0" / "front_lit_face.png"),
                                               ("front depth 0.5", R / "candidate_d0.5" / "front_lit_face.png")]),
                    ("baseline VRoid", [("q3L LIT", R / "baseline" / "q3L_lit_face.png"),
                                        ("front LIT", R / "baseline" / "front_lit_face.png"),
                                        ("q3L clay", R / "baseline" / "q3L_clay_face.png"),
                                        ("q3L clay cand d0", R / "candidate_d0.0" / "q3L_clay_face.png"),
                                        ("q3L unlit VRM cand d0", R / "candidate_d0.0" / "q3L_original.png")])]
        grid(tgt_rows, 320, OUT / "SHEET_NOSE_VS_3D_TARGET_UNCALIBRATED.png",
             "3D quality target vs candidate: different camera, lens, hair and accessories; qualitative only")

    checks = {
        "untouched_faces_identical": len(kept) == untouched_expected,
        "untouched_faces": len(kept), "untouched_expected": untouched_expected,
        "body_mesh_unchanged": body_hash0 == body_hash1,
        "face_body_seam_vertices": len(seam), "face_body_seam_max_gap_m": round(max(seam), 7) if seam else None,
        "winding_conflicts": winding_conflicts(face, patch),
        "uv_flipped_faces": uv_flips, "uv_out_of_range_loops": uv_out,
        "weights_sum_min": round(min(wsum), 6), "weights_sum_max": round(max(wsum), 6),
        "dominant_bone_new_vertices": dom,
        "shape_keys_original_preserved": [k.name for k in keys[1:57]] == [f"target_{i}" for i in range(56)],
        "design_key_added": params["design_range"]["shape_key_name"] in keys,
    }
    acc = params["acceptance_technical"]
    g0 = design_rows["0.0"]["geometry"]
    tech_pass = (checks["untouched_faces_identical"] and checks["body_mesh_unchanged"] and checks["winding_conflicts"] == 0
                 and checks["uv_flipped_faces"] == 0 and checks["uv_out_of_range_loops"] == 0
                 and abs(checks["weights_sum_min"] - 1) < 1e-3 and abs(checks["weights_sum_max"] - 1) < 1e-3
                 and checks["shape_keys_original_preserved"] and g0["non_manifold_edges"] == 0
                 and g0["inner_dihedral_deg_max"] <= base_geom["inner_dihedral_deg_max"]
                 and g0["border_dihedral_deg_max"] <= base_geom["border_dihedral_deg_max"]
                 and checks["face_body_seam_max_gap_m"] is not None and checks["face_body_seam_max_gap_m"] <= acc["face_body_seam_max_gap_m"]
                 and all(r["status"] != "FAIL" for r in exp_rows.values()))
    blocked_keys = [k for k, r in exp_rows.items() if r["status"] == "BLOCKED_TRANSFER_UNREVIEWED"]
    report = {
        "task_id": "MORWEN-LOCAL-RETOPO-03", "method_id": params["method_id"], "method_family": params["method_family"],
        "params_sha256": sha(B.PARAMS_PATH), "seed": params["seed"], "blender_version": bpy.app.version_string,
        "source_vrm_sha256": M3.VRM_SHA256, "source_modified": False,
        "build": {k: v for k, v in rec.items() if k not in ("baseline", "patch_vertex_indices", "boundary_vertex_indices", "ring_s")},
        "baseline_region_geometry": base_geom,
        "baseline_nose": {"tip": {k: v for k, v in base_profile.items() if k != "profile_points"},
                          "nose_projection_from_pupil_U": round((base_profile["tip_y"] - pupil_y) / U, 4),
                          "baseline_region_dihedral_note": "see baseline wire sheet: single-vertex fan tip"},
        "design_range": design_rows,
        "canonical_side_reference_U": "0.49-0.53 (2D drawing; NOT used as a 3D target)",
        "calibrated_layer0_deltas_U": cal,
        "expressions": exp_rows, "expression_keys_blocked": blocked_keys,
        "technical_checks": checks, "technical_result": "PASS" if tech_pass else "FAIL",
        "renders": st.records,
        "sheets": {p.name: sha(p) for p in sorted(OUT.glob("SHEET_*.png"))},
        "G1": "PASS for source preservation only (VRM, Layer 0, 3D target SHA verified; v5.61 binary unavailable -> full canon comparison BLOCKED)",
        "G2": "NOT_RUN - art review of nose form and depth required; candidate is not an approved head",
        "G3": ("PASS" if tech_pass else "FAIL") + (" (expression transfers partially BLOCKED, see expression_keys_blocked)" if blocked_keys else ""),
        "G4": "NOT_RUN",
    }
    bpy.ops.wm.save_as_mainfile(filepath=str((OUT / "MORWEN_NOSE_RETOPO_03_CANDIDATE.blend").resolve()), compress=True, copy=True)
    (OUT / "NOSE_RETOPO_03_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    assert sha(M3.SRC) == M3.VRM_SHA256
    print("nose retopo technical:", report["technical_result"], "blocked keys:", len(blocked_keys))


if __name__ == "__main__":
    main()
