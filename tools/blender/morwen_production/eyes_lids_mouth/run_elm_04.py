"""MORWEN-EYES-LIDS-MOUTH-04: baseline vs candidate QA, renders and report.

Baseline = exact #312 nose candidate at MORWEN_DESIGN_NoseDepth 0.5 (locked). Candidate = build().
Writes $MORWEN_OUT/ELM_04_REPORT.json, SHEET_*.png and the candidate .blend (artifact only).
Technical QA only; art QA is separate and G2 is never PASS here.
"""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from PIL import Image

HERE = Path(__file__).resolve().parent
MP = HERE.parent


def _load(path, name):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


E = _load(HERE / "build_eyes_lids_mouth_04.py", "morwen_elm_build")
RV = _load(MP / "nose_retopo_review" / "review_nose_03.py", "morwen_nose_review")
R, M3, X = RV.R, E.M3, E.X
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_eyes_lids_mouth_04"))
R.OUT = OUT
RV.OUT = OUT
P = json.loads(E.PARAMS_PATH.read_text())
CAN = {"eye_width_U": 0.4282, "eye_height_U": {"R": 0.2336, "L": 0.1752}, "ipd_U": 0.9916,
       "source": "LANDMARK-02 CANONICAL_LANDMARKS_2D front (Layer 0, SHA verified)"}
DESIGN = {P["locked_nose"]["design_key"]: P["locked_nose"]["design_value"]}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Stage(RV.ToonStage):
    def toon(self, mat):
        if mat is not None and mat.name.startswith("MORWEN_EYE"):
            return mat  # procedural eye stays emissive in the toon look
        return super().toon(mat)


def eye_points():
    ob = bpy.data.objects.get("MORWEN_Eyes")
    if ob is None:
        return None
    mw = ob.matrix_world
    return np.array([tuple(mw @ v.co) for v in ob.data.vertices])


def measure_states(face):
    out = {}
    for name, key in P["states"].items():
        W = X.state_coords(face, key, DESIGN)
        out[name] = X.measure_state(face, W, X.face_slots(face), eye_points())
    return out


def patch_stats(face, regions):
    me = face.data
    keys = me.shape_keys.key_blocks
    basis = np.array([v.co[:] for v in keys[0].data]) + DESIGN_OFF(face)
    res = {}
    for rname, verts in regions.items():
        res[rname] = {"neutral": R.patch_geometry_stats(face, verts, basis)}
        res[rname]["neutral"].pop("folded_vs_basis", None)
        for sname, key in P["states"].items():
            if key is None:
                continue
            co = basis + (np.array([v.co[:] for v in keys[key].data]) - np.array([v.co[:] for v in keys[0].data]))
            g = R.patch_geometry_stats(face, verts, co, basis)
            res[rname][sname] = {k: g[k] for k in ("folded_vs_basis", "edge_ratio_p99", "inner_dihedral_deg_max")}
    return res


def DESIGN_OFF(face):
    keys = face.data.shape_keys.key_blocks
    k = keys[P["locked_nose"]["design_key"]]
    return P["locked_nose"]["design_value"] * (np.array([v.co[:] for v in k.data]) - np.array([v.co[:] for v in keys[0].data]))


SOCKET_VIEWS = {"front": (0, 1, 0), "q3L": (-0.70711, 0.70711, 0), "q3R": (0.70711, 0.70711, 0),
                "up30": (0, 0.86603, 0.5), "down30": (0, 0.86603, -0.5),
                "q3L_up30": (-0.61237, 0.61237, 0.5), "q3R_up30": (0.61237, 0.61237, 0.5)}
SOCKET_GRID = 48


def socket_show_through(face, opening, rim_y):
    """Parallel rays (ortho cameras) over each eye opening; a ray whose first opaque hit
    is the BACK of a Face polygon looks through the socket into the head interior.
    Card / brow / EyeExtra slots are alpha overlays and are passed through."""
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    fe = face.evaluated_get(dg)
    me = fe.data
    rot = fe.matrix_world.to_3x3()
    see_through = {i for i, sl in enumerate(face.material_slots)
                   if sl.material and any(k in sl.material.name for k in ("Eyeline", "Eyelash", "Brow", "EyeExtra"))}
    res = {}
    for side, (x0, x1, z0, z1) in opening.items():
        res[side] = {}
        for vn, dv in SOCKET_VIEWS.items():
            d = Vector(dv).normalized()
            n_eye = n_back = 0
            for i in range(SOCKET_GRID):
                for j in range(SOCKET_GRID):
                    p = Vector((x0 - 0.003 + (x1 - x0 + 0.006) * i / (SOCKET_GRID - 1), rim_y[side],
                                z0 - 0.003 + (z1 - z0 + 0.006) * j / (SOCKET_GRID - 1)))
                    org = p + d * 0.3
                    for _ in range(32):
                        hit, loc, nor, idx, ob, _m = sc.ray_cast(dg, org, -d)
                        if hit and ob.original == face and me.polygons[idx].material_index in see_through:
                            org = loc - d * 1e-5
                            continue
                        break
                    if not hit:
                        continue
                    if ob.name.startswith("MORWEN_Eyes"):
                        n_eye += 1
                    elif ob.original == face and (rot @ me.polygons[idx].normal).dot(d) < 0:
                        n_back += 1
            res[side][vn] = {"eye_rays": n_eye, "show_through_rays": n_back}
    return res


def rim_polygons(face):
    """Ordered xz polygon (+ mean y) of the skin/EyeWhite junction ring per side (Basis)."""
    me = face.data
    ew = M3.slot_index(face, "EyeWhite")
    skin = M3.slot_index(face, "Face_00_SKIN")
    ewp = {E.pkey(me.vertices[v].co) for p in me.polygons if p.material_index == ew for v in p.vertices}
    pts = {E.pkey(me.vertices[v].co): me.vertices[v].co.copy()
           for p in me.polygons if p.material_index == skin for v in p.vertices if E.pkey(me.vertices[v].co) in ewp}
    mw = face.matrix_world
    out = {}
    for side in ("R", "L"):
        q = [mw @ c for c in pts.values() if ((mw @ c).x > M3.MID_X) == (side == "R")]
        cx, cz = sum(v.x for v in q) / len(q), sum(v.z for v in q) / len(q)
        q.sort(key=lambda v: np.arctan2(v.z - cz, v.x - cx))
        out[side] = {"xz": [(v.x, v.z) for v in q], "y": sum(v.y for v in q) / len(q)}
    return out


def _inside(poly, x, z):
    c = False
    for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]):
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
            c = not c
    return c


def _outside_mm(poly, x, z):
    best = 1e9
    for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]):
        dx, dz = x2 - x1, z2 - z1
        t = max(0.0, min(1.0, ((x - x1) * dx + (z - z1) * dz) / (dx * dx + dz * dz)))
        best = min(best, np.hypot(x - x1 - t * dx, z - z1 - t * dz))
    return best * 1000


def eye_surface_protrusion(face, eyes, rims):
    """An eye vertex that is visible from the front (no opaque Face polygon in front of it)
    while lying outside the Basis rim outline sticks out of the skin."""
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    fe = face.evaluated_get(dg)
    see_through = {i for i, sl in enumerate(face.material_slots)
                   if sl.material and any(k in sl.material.name for k in ("Eyeline", "Eyelash", "Brow", "EyeExtra"))}
    ee = eyes.evaluated_get(dg)
    up = Vector((0, 1, 0))
    n, far, ex = 0, 0.0, []
    half = len(ee.data.vertices) // 2  # build_eyes writes R then L with equal counts
    for v in ee.data.vertices:
        q = ee.matrix_world @ v.co
        side = "R" if v.index < half else "L"
        if _inside(rims[side]["xz"], q.x, q.z):
            continue
        org, covered = q + up * 1e-5, False
        for _ in range(32):
            hit, loc, nor, idx, ob, _m = sc.ray_cast(dg, org, up)
            if hit and (ob.name.startswith("MORWEN_Eyes") or
                        (ob.original == face and fe.data.polygons[idx].material_index in see_through)):
                org = loc + up * 1e-5
                continue
            covered = hit and ob.original == face
            break
        if not covered:
            n += 1
            dmm = _outside_mm(rims[side]["xz"], q.x, q.z)
            far = max(far, dmm)
            ex.append((round(dmm, 2), [round(c, 4) for c in q], ob.name if hit else None))
    ex.sort(reverse=True)
    return {"uncovered_outside_rim": n, "uncovered_max_dist_outside_rim_mm": round(far, 3), "worst": ex[:6]}


def set_state(face, key):
    for kb in face.data.shape_keys.key_blocks[1:]:
        kb.value = DESIGN.get(kb.name, 0.0)
    if key:
        face.data.shape_keys.key_blocks[key].value = 1.0


def render_set(st, face, originals, tag, states, views, modes, scale):
    for sname in states:
        set_state(face, P["states"][sname])
        for v in views:
            for m in modes:
                st.shot(f"{tag}_{sname}", v, m, originals, scale=scale)
    set_state(face, None)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    M3.load()
    nrec = E.build_base(P)
    face, body = bpy.data.objects["Face"], bpy.data.objects["Body"]
    L = nrec["baseline"]["landmarks"]
    U = nrec["baseline"]["normalisation"]["unit_U_m"]
    tip = Vector(L["pronasale"]["position"])
    eye_c = Vector((M3.MID_X, tip.y - 0.025, (L["pupil_R"]["position"][2] + L["pupil_L"]["position"][2]) / 2))
    mouth_c = Vector((M3.MID_X, tip.y - 0.02, L["stomion"]["position"][2]))
    face_c = Vector((M3.MID_X, tip.y - 0.02, tip.z + 0.004))

    # ---------------- baseline -------------------------------------------------------------
    me = face.data
    body_hash0 = hashlib.sha256(np.array([v.co[:] for v in body.data.vertices]).tobytes()).hexdigest()
    nose0 = sorted(E.pkey(me.vertices[i].co) for i, a in enumerate(me.attributes[E.PATCH_ATTR].data) if a.value == 4)
    base_ix = measure_states(face)
    ell = E.ellipses(P, L)
    base_regions = {n: E.region_vertices(face, n, spec) for n, spec in ell.items()}
    base_region_pos = {n: {E.pkey(me.vertices[v].co) for v in vs} for n, vs in base_regions.items()}
    base_stats = patch_stats(face, base_regions)
    old_faces = {tuple(sorted(E.pkey(me.vertices[v].co) for v in p.vertices)) for p in me.polygons}
    originals = {o.name: [s.material for s in o.material_slots] for o in bpy.context.scene.objects if o.type == "MESH"}
    st = Stage(face_c)
    render_set(st, face, originals, "base", ["neutral", "blink", "joy", "surprised", "a"], ["front"], ["toon"], R.FACE_SCALE)
    st.centre = eye_c
    render_set(st, face, originals, "base_eyes", ["neutral", "blink", "joy"], ["front"], ["clay"], 0.09)
    st.centre = face_c
    st.materials("original", originals)
    base_open = base_ix["neutral"]["eye_visible_extent_m"]
    rims = rim_polygons(face)
    rim_y = {k: v["y"] for k, v in rims.items()}
    socket_states = ["neutral", "surprised", "angry", "sorrow", "fun", "blink", "joy"]
    base_socket = {}
    for sname in socket_states:
        set_state(face, P["states"][sname])
        base_socket[sname] = socket_show_through(face, base_open, rim_y)
    set_state(face, None)

    # ---------------- candidate -------------------------------------------------------------
    rec, eyes = E.build(P, nrec, base_open)
    me = face.data
    attr = me.attributes[E.PATCH_ATTR].data
    regions = {}
    for name, pid in (("lid_R", 1), ("lid_L", 2), ("mouth", 3)):
        if rec[name].get("built", True):
            regions[name] = {i for i, a in enumerate(attr) if a.value == pid}
        else:  # not rebuilt (method stopped): the same original region, located by position
            skin_v = {v for pp in me.polygons if pp.material_index == M3.slot_index(face, "Face_00_SKIN") for v in pp.vertices}
            regions[name] = {v.index for v in me.vertices if v.index in skin_v and E.pkey(v.co) in base_region_pos[name]}
    cand_ix = measure_states(face)
    cand_socket, protrusion = {}, {}
    for sname in socket_states:
        set_state(face, P["states"][sname])
        cand_socket[sname] = socket_show_through(face, base_open, rim_y)
        protrusion[sname] = eye_surface_protrusion(face, eyes, rims)
    set_state(face, None)
    socket_zero = all(v["show_through_rays"] == 0 for s_ in cand_socket.values() for d_ in s_.values() for v in d_.values())
    cand_stats = patch_stats(face, regions)
    nose1 = sorted(E.pkey(me.vertices[i].co) for i, a in enumerate(attr) if a.value == 4)
    # checks
    new_faces = {tuple(sorted(E.pkey(me.vertices[v].co) for v in p.vertices)) for p in me.polygons}
    patch_all = set().union(*regions.values())
    kept_old = sum(1 for k in old_faces if k in new_faces)
    body_hash1 = hashlib.sha256(np.array([v.co[:] for v in body.data.vertices]).tobytes()).hexdigest()
    bw = R.world_verts(body)
    kd = KDTree(len(bw))
    for i, q in enumerate(bw):
        kd.insert(q, i)
    kd.balance()
    seam = [kd.find(q)[2] for q in R.world_verts(face) if kd.find(q)[2] < 1e-4]
    uvl = me.uv_layers.active.data
    si = M3.slot_index(face, "Face_00_SKIN")

    def uv_area(poly):
        u = [uvl[li].uv for li in poly.loop_indices]
        return sum(u[i].x * u[(i + 1) % len(u)].y - u[(i + 1) % len(u)].x * u[i].y for i in range(len(u))) / 2
    skin_sign = np.sign(np.median([uv_area(p) for p in me.polygons if p.material_index == si and not any(v in patch_all for v in p.vertices)]))
    ppolys = [p for p in me.polygons if any(v in patch_all for v in p.vertices) and p.material_index == si]
    wsum = [sum(g.weight for g in me.vertices[i].groups) for i in patch_all]
    checks = {
        "nose_locked_geometry_unchanged": nose0 == nose1,
        "body_mesh_unchanged": body_hash0 == body_hash1,
        "face_body_seam_vertices": len(seam), "face_body_seam_max_gap_m": round(max(seam), 7) if seam else None,
        "winding_conflicts": R.winding_conflicts(face, patch_all),
        "uv_flipped_faces": sum(1 for p in ppolys if np.sign(uv_area(p)) != skin_sign),
        "uv_out_of_range_loops": sum(1 for p in ppolys for li in p.loop_indices if not (0 <= uvl[li].uv.x <= 1 and 0 <= uvl[li].uv.y <= 1)),
        "weights_sum_min": round(min(wsum), 6), "weights_sum_max": round(max(wsum), 6),
        "shape_keys_preserved": [k.name for k in me.shape_keys.key_blocks[1:57]] == [f"target_{i}" for i in range(56)],
        "old_faces_kept": kept_old, "old_faces_total": len(old_faces),
    }
    acc = P["acceptance_technical"]
    rel = {}
    for rname in regions:
        b, c = base_stats[rname], cand_stats[rname]
        rows = {"neutral": {"baseline": b["neutral"], "candidate": c["neutral"],
                            "ok": c["neutral"]["non_manifold_edges"] == 0}}
        for sname in P["states"]:
            if sname == "neutral":
                continue
            ok = (c[sname]["folded_vs_basis"] <= b[sname]["folded_vs_basis"]
                  and c[sname]["edge_ratio_p99"] <= b[sname]["edge_ratio_p99"] * acc["relative_edge_ratio_margin"]
                  and c[sname]["inner_dihedral_deg_max"] <= b[sname]["inner_dihedral_deg_max"] + acc["relative_dihedral_margin_deg"])
            rows[sname] = {"baseline": b[sname], "candidate": c[sname], "ok": ok}
        rel[rname] = rows
    pen_ok = all(v["max_depth_mm"] <= acc["max_line_penetration_mm"] and v["penetrating_ratio"] <= acc["max_line_penetrating_ratio"]
                 for s in cand_ix.values() for v in s["line_penetration"].values())
    blink_closed = all(cand_ix[s]["eye_visible_samples"][side] == 0
                       for s, side in (("blink", "R"), ("blink", "L"), ("blink_l", "L"), ("blink_r", "R")))
    # eye opening vs canonical (front, calibrated U)
    ev = eyes.matrix_world
    eye_report = {}
    ext = cand_ix["neutral"]["eye_visible_extent_m"]
    pupils = {}
    for side in ("R", "L"):
        x0, x1, z0, z1 = ext[side]
        pv = [ev @ v.co for v in eyes.data.vertices if v.groups and eyes.vertex_groups[v.groups[0].group].name.endswith(f"_{side}_FaceEye")]
        centre = pv[0]
        pupils[side] = centre
        eye_report[side] = {"opening_width_U": round((x1 - x0) / U, 4), "opening_height_U": round((z1 - z0) / U, 4),
                            "canonical_width_U": CAN["eye_width_U"], "canonical_height_U": CAN["eye_height_U"][side],
                            "pupil_centre_m": [round(c, 5) for c in centre]}
    eye_report["ipd_U"] = round(abs(pupils["R"].x - pupils["L"].x) / U, 4)
    eye_report["canonical_ipd_U"] = CAN["ipd_U"]
    eye_report["note"] = ("opening = lids of the existing VRoid socket (shape unchanged: lid retopology stopped). The pupil is "
                          "placed by the Layer 0 per-side fractions inside that opening; because the sockets were not moved, "
                          "opening width, the R/L height asymmetry and the IPD do NOT match the canon (see deltas). "
                          "Matching them needs the socket/lid rework (method switch), not the eye surface.")
    eye_report["deltas_vs_canon"] = {
        "ipd_pct": round(100 * (eye_report["ipd_U"] / CAN["ipd_U"] - 1), 1),
        **{f"width_{sd}_pct": round(100 * (eye_report[sd]["opening_width_U"] / CAN["eye_width_U"] - 1), 1) for sd in ("R", "L")},
        **{f"height_{sd}_pct": round(100 * (eye_report[sd]["opening_height_U"] / CAN["eye_height_U"][sd] - 1), 1) for sd in ("R", "L")}}
    # unreviewed keys: prioritise by region motion
    keys = me.shape_keys.key_blocks
    basis = np.array([v.co[:] for v in keys[0].data])
    W0 = R.world_verts(face, basis)
    masks = RV.region_masks(W0)
    prev_blocked = json.loads((MP / "nose_retopo_review" / "blocked_before_review.json").read_text())
    reviewed8 = {"target_1", "target_5", "target_37", "target_41", "target_39", "target_15", "target_14", "target_2"}
    still = [k for k in prev_blocked if k not in reviewed8]
    prio = []
    for k in still:
        d = np.linalg.norm(R.world_verts(face, np.array([v.co[:] for v in keys[k].data])) - W0, axis=1)
        motion = {r: round(float(d[m].max() * 1000), 2) for r, m in masks.items()}
        prio.append({"key": k, "max_mm": round(float(d.max() * 1000), 2), "region_motion_mm": motion})
    prio.sort(key=lambda r: -r["max_mm"])
    evaluated_now = {"target_4": "sorrow", "target_40": "e"}
    for r_ in prio:
        r_["status"] = "EVALUATED_THIS_TASK (rendered + measured)" if r_["key"] in evaluated_now else "BLOCKED_UNREVIEWED"

    # ---------------- renders -------------------------------------------------------------
    originals = {o.name: [s.material for s in o.material_slots] for o in bpy.context.scene.objects if o.type == "MESH"}
    st.centre = face_c
    allstates = list(P["states"])
    render_set(st, face, originals, "cand", allstates, ["front", "q3L"], ["toon"], R.FACE_SCALE)
    render_set(st, face, originals, "cand", ["neutral"], ["q3R", "right", "left"], ["toon"], R.FACE_SCALE)
    render_set(st, face, originals, "cand", ["neutral"], ["front", "q3L", "q3R", "right", "left"], ["clay", "wire"], R.FACE_SCALE)
    st.centre = eye_c
    render_set(st, face, originals, "cand_eyes", ["neutral", "blink", "joy"], ["front"], ["clay"], 0.09)
    render_set(st, face, originals, "cand_eyes", ["neutral"], ["front"], ["wire"], 0.09)
    for side, ctr in (("R", pupils["R"]), ("L", pupils["L"])):  # one eye per shot, both 45 deg views
        st.centre = Vector((ctr.x, eye_c.y, ctr.z))
        render_set(st, face, originals, f"cand_eye{side}", ["neutral", "surprised"], ["q3L", "q3R"], ["clay", "toon"], 0.06)
    st.centre = mouth_c
    render_set(st, face, originals, "cand_mouth", ["neutral", "a", "i", "u", "e", "o", "joy", "angry", "surprised"], ["front"], ["clay"], 0.07)
    render_set(st, face, originals, "cand_mouth", ["neutral"], ["front"], ["wire"], 0.07)
    st.centre = face_c

    Rr = OUT / "renders"
    f_ = lambda tag, s, v, m, face_=True: Rr / f"{tag}_{s}" / f"{v}_{m}_face.png"  # noqa: E731  (every scale here != CLOSE_SCALE)
    R.grid([("baseline #312@0.5", [(s, f_("base", s, "front", "toon")) for s in ["neutral", "blink", "joy", "surprised", "a"]]),
            ("candidate", [(s, f_("cand", s, "front", "toon")) for s in ["neutral", "blink", "joy", "surprised", "a"]])],
           320, OUT / "SHEET_BASELINE_VS_CANDIDATE_TOON.png",
           "Baseline (#312 nose @0.5, VRoid eyes) vs candidate - validation toon, world-fixed light")
    R.grid([("baseline", [(s, f_("base_eyes", s, "front", "clay", False)) for s in ["neutral", "blink", "joy"]]),
            ("candidate", [(s, f_("cand_eyes", s, "front", "clay", False)) for s in ["neutral", "blink", "joy"]]
             + [("wire", f_("cand_eyes", "neutral", "front", "wire", False))])],
           360, OUT / "SHEET_EYES_LIDS_CLAY.png",
           "Eye/lid close-ups (clay): VRoid plates vs procedural eye surface + rebound cards (lids = original topology, annulus stopped)")
    R.grid([(f"eye {side} {m}", [(f"{s} {v}", f_(f"cand_eye{side}", s, v, m)) for s in ["neutral", "surprised"] for v in ["q3L", "q3R"]])
            for side in ("R", "L") for m in ("clay", "toon")],
           300, OUT / "SHEET_EYE_SOCKET_45.png", "Socket check: each eye at +/-45 deg, neutral and surprised (no head interior visible)")
    R.grid([("toon front", [(s, f_("cand", s, "front", "toon")) for s in allstates[:7]]),
            ("toon left45", [(s, f_("cand", s, "q3L", "toon")) for s in allstates[:7]]),
            ("toon front", [(s, f_("cand", s, "front", "toon")) for s in allstates[7:]]),
            ("toon left45", [(s, f_("cand", s, "q3L", "toon")) for s in allstates[7:]])],
           260, OUT / "SHEET_EXPRESSIONS_TOON.png", "Candidate expressions (nose depth 0.5) - validation toon")
    R.grid([("mouth clay", [(s, f_("cand_mouth", s, "front", "clay", False)) for s in ["neutral", "a", "i", "u", "e"]]),
            ("mouth clay", [(s, f_("cand_mouth", s, "front", "clay", False)) for s in ["o", "joy", "angry", "surprised"]]
             + [("wire", f_("cand_mouth", "neutral", "front", "wire", False))])],
           320, OUT / "SHEET_MOUTH_CLAY.png", "Mouth: original VRoid topology (annulus retopology stopped) under vowels, Joy, Angry, Surprised")
    R.grid([("clay", [(v, f_("cand", "neutral", v, "clay")) for v in ["front", "q3L", "q3R", "right", "left"]]),
            ("wire", [(v, f_("cand", "neutral", v, "wire")) for v in ["front", "q3L", "q3R", "right", "left"]]),
            ("toon", [(v, f_("cand", "neutral", v, "toon")) for v in ["front", "q3L", "q3R", "right", "left"]])],
           300, OUT / "SHEET_NEUTRAL_VIEWS.png", "Candidate neutral: front, 45 L/R, full sides")
    big = Image.open(f_("cand", "neutral", "front", "toon")).convert("RGBA")
    bg = Image.new("RGBA", big.size, (232, 232, 228, 255))
    bg.alpha_composite(big)
    rows = []
    for px in (128, 64, 32):
        small = bg.convert("RGB").resize((px, px), Image.LANCZOS).resize((320, 320), Image.NEAREST)
        rows.append((f"{px}px", small))
    R.grid([("game-size preview (face crop, nearest upscale)", rows)], 320, OUT / "SHEET_GAME_SIZE_PREVIEW.png",
           "Final display size unknown: 128 / 64 / 32 px previews of the toon face crop")

    tech = {
        "line_penetration_zero_all_states": pen_ok,
        "eyes_hidden_when_closed": blink_closed,
        "socket_show_through_zero": socket_zero,
        "eye_surface_protrusion_neutral": protrusion["neutral"]["uncovered_outside_rim"],
        "patch_relative_ok": {r: all(v["ok"] for v in rows.values()) for r, rows in rel.items()},
        **checks,
    }
    tech_pass = (tech["line_penetration_zero_all_states"] and tech["eyes_hidden_when_closed"]
                 and socket_zero and protrusion["neutral"]["uncovered_outside_rim"] == 0
                 and all(tech["patch_relative_ok"].values()) and checks["nose_locked_geometry_unchanged"]
                 and checks["body_mesh_unchanged"] and checks["winding_conflicts"] == 0 and checks["uv_flipped_faces"] == 0
                 and checks["uv_out_of_range_loops"] == 0 and abs(checks["weights_sum_min"] - 1) < 1e-3
                 and abs(checks["weights_sum_max"] - 1) < 1e-3 and checks["shape_keys_preserved"])
    trial = OUT / "ANNULUS_RETOPO_TRIAL.json"
    report = {
        "retopo_status": P["retopo_status"],
        "annulus_trial": json.loads(trial.read_text()) if trial.is_file() else "NOT_RUN",
        "task_id": P["task_id"], "params_sha256": sha(E.PARAMS_PATH), "blender_version": bpy.app.version_string,
        "source_vrm_sha256": M3.VRM_SHA256, "source_modified": False, "build": rec,
        "baseline_intersections": base_ix, "candidate_intersections": cand_ix,
        "patch_relative": rel, "eye_opening_vs_canonical": eye_report,
        "socket_show_through": {"views": SOCKET_VIEWS, "grid": SOCKET_GRID, "baseline": base_socket, "candidate": cand_socket,
                                "definition": "first opaque hit is the back of a Face polygon (head interior) through the eye opening"},
        "eye_surface_protrusion": {"by_state": protrusion,
                                   "definition": "eye vertex outside the Basis rim outline with no opaque Face polygon in front (+Y); "
                                                 "non-neutral states can open wider than the Basis outline, so only neutral is gated"},
        "unreviewed_keys_priority": prio, "technical_checks": tech, "technical_result": "PASS" if tech_pass else "FAIL",
        "renders": st.records, "sheets": {p.name: sha(p) for p in sorted(OUT.glob("SHEET_*.png"))},
        "G1": "PASS for source preservation only (v5.61 binary unavailable -> full canon BLOCKED)",
        "G2": "NOT_RUN - independent art review mandatory", "G3": "PASS" if tech_pass else "FAIL", "G4": "NOT_RUN",
    }
    st.materials("original", originals)  # the artifact .blend keeps the real materials, not the review look
    for o in bpy.context.scene.objects:
        m_ = o.modifiers.get("TOON_OUTLINE_HULL") if o.type == "MESH" else None
        if m_ is not None:
            o.modifiers.remove(m_)
    set_state(face, None)
    bpy.ops.wm.save_as_mainfile(filepath=str((OUT / "MORWEN_ELM_04_CANDIDATE.blend").resolve()), compress=True, copy=True)
    (OUT / "ELM_04_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    assert sha(M3.SRC) == M3.VRM_SHA256
    print("ELM technical:", report["technical_result"], json.dumps(tech))


if __name__ == "__main__":
    main()
