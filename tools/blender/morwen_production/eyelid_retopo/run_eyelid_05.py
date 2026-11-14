"""MORWEN-EYELID-RETOPO-05: #316 baseline vs eyelid candidate - QA, renders, report.

Phase A: rebuild the PR #316 candidate exactly (E.build), measure, render, keep positions.
Phase B: fresh import -> locked nose -> canthus-anchored lid strips (build_eyelid_retopo_05).
Writes $MORWEN_OUT/EYELID_05_REPORT.json, EYE_TARGETS_05.json, SHEET_*.png and the candidate
.blend (artifact only). Technical QA only; G2 is never PASS here.
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
MP = HERE.parent
sys.path.insert(0, str(HERE))
from build_eyelid_retopo_05 import _load, E, MT, M3, X, PARAMS_PATH  # noqa: E402
import build_eyelid_retopo_05 as B  # noqa: E402

R4 = _load(MP / "eyes_lids_mouth" / "run_elm_04.py", "morwen_elm_run")
RV, R = R4.RV, R4.R
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_eyelid_retopo_05"))
for mod in (R, RV, R4):
    mod.OUT = OUT
MT.OUT = OUT
P04 = R4.P
P05 = json.loads(PARAMS_PATH.read_text())
STATES = P04["states"]
REQ = P05["acceptance_technical"]["states_required"]
VIEWS5 = ["front", "q3L", "q3R", "right", "left"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def mat_fingerprint(mat):
    """Node types, every input default value and every link of a node material (colour lock)."""
    h = hashlib.sha256()
    for n in sorted(mat.node_tree.nodes, key=lambda n: n.name):
        h.update(f"{n.name}|{n.bl_idname}|{getattr(n, 'operation', '')}|{getattr(n, 'blend_type', '')}".encode())
        for sk in n.inputs:
            dv = getattr(sk, "default_value", None)
            if dv is None:
                continue
            vals = list(dv) if hasattr(dv, "__len__") else [dv]
            h.update(repr([round(float(x), 6) for x in vals]).encode())
    for lk in mat.node_tree.links:
        h.update(f"{lk.from_node.name}.{lk.from_socket.identifier}>{lk.to_node.name}.{lk.to_socket.identifier}".encode())
    return h.hexdigest()


def anchors(nrec):
    L = nrec["baseline"]["landmarks"]
    tip = Vector(L["pronasale"]["position"])
    eye_c = Vector((M3.MID_X, tip.y - 0.025, (L["pupil_R"]["position"][2] + L["pupil_L"]["position"][2]) / 2))
    face_c = Vector((M3.MID_X, tip.y - 0.02, tip.z + 0.004))
    return eye_c, face_c


def pos_hash(obj, verts=None):
    co = np.array([v.co[:] for v in obj.data.vertices])
    if verts is not None:
        co = co[sorted(verts)]
    return hashlib.sha256(np.round(co, 7).tobytes()).hexdigest()


def mouth_positions(face):
    """Basis + every key of the mouth area (FaceMouth slot and skin within the ELM mouth ellipse)."""
    me = face.data
    keys = me.shape_keys.key_blocks
    st = R4.P["mouth"]
    mi = M3.slot_index(face, "FaceMouth")
    vs = {v for p in me.polygons if p.material_index == mi for v in p.vertices}
    cz = np.mean([me.vertices[v].co.z for v in vs])
    near = {v.index for v in me.vertices if abs(v.co.z - cz) < st["z_down_m"] + 0.006 and abs(v.co.x) < 0.04}
    out = set()
    for v in near | vs:
        out.add(tuple(np.round(np.array([kb.data[v].co[:] for kb in keys]).ravel() * 1e6).astype(int)))
    return hashlib.sha256(repr(sorted(out)).encode()).hexdigest(), len(out)


def corner_metrics(face, patch, canthi, coords, base_coords, radius):
    """Faces of the lid patch within `radius` of a canthus: flipped vs basis, max inner dihedral."""
    me = face.data
    P_ = R.world_verts(face, coords)
    Pb = R.world_verts(face, base_coords)
    polys = [p for p in me.polygons if all(v in patch for v in p.vertices)
             and min(np.linalg.norm(Pb[list(p.vertices)] - c, axis=1).min() for c in canthi) < radius]

    def nrm(pts):
        n = np.zeros(3)
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            n += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
        return n / max(np.linalg.norm(n), 1e-12)
    N = {p.index: nrm(P_[list(p.vertices)]) for p in polys}
    flips = sum(1 for p in polys if np.dot(N[p.index], nrm(Pb[list(p.vertices)])) < 0)
    ef = {}
    for p in polys:
        for ek in p.edge_keys:
            ef.setdefault(ek, []).append(p.index)
    dih = [math.degrees(math.acos(max(-1, min(1, float(np.dot(N[a], N[b])))))) for a, b in (f for f in ef.values() if len(f) == 2)]
    return {"faces": len(polys), "flipped_vs_basis": flips, "inner_dihedral_deg_max": round(max(dih), 3) if dih else 0.0}


def region_stats(face, verts):
    """Like R4.patch_stats but only faces with ALL vertices in `verts` (lid faces without the
    lid-thickness wall, whose 90+ deg fold is intentional; baseline = VRoid lid region)."""
    me = face.data
    polys = [p for p in me.polygons if all(v in verts for v in p.vertices)]
    pidx = [list(p.vertices) for p in polys]
    ef = {}
    for k, p in enumerate(polys):
        for ek in p.edge_keys:
            ef.setdefault(ek, []).append(k)

    def normals(P_):
        out = []
        for vs in pidx:
            pts = P_[vs]
            n = np.zeros(3)
            for i in range(len(pts)):
                a, b = pts[i], pts[(i + 1) % len(pts)]
                n += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
            out.append(n / max(np.linalg.norm(n), 1e-12))
        return np.array(out)

    def dih(N):
        return [math.degrees(math.acos(max(-1, min(1, float(np.dot(N[a], N[b])))))) for a, b in (f for f in ef.values() if len(f) == 2)]
    b0 = state_coords_local(face, None)
    Pb = R.world_verts(face, b0)
    Nb = normals(Pb)
    d0 = dih(Nb)
    res = {"neutral": {"faces": len(polys), "inner_dihedral_deg_max": round(max(d0), 3),
                       "inner_dihedral_deg_p95": round(float(np.percentile(d0, 95)), 3),
                       "non_manifold_edges": sum(1 for f in ef.values() if len(f) > 2)}}
    for sn, key in STATES.items():
        if key is None:
            continue
        P_ = R.world_verts(face, state_coords_local(face, key))
        N = normals(P_)
        ratios = [np.linalg.norm(P_[vs[i]] - P_[vs[(i + 1) % len(vs)]]) / max(np.linalg.norm(Pb[vs[i]] - Pb[vs[(i + 1) % len(vs)]]), 1e-9)
                  for vs in pidx for i in range(len(vs))]
        res[sn] = {"folded_vs_basis": int(sum(1 for a, b in zip(N, Nb) if np.dot(a, b) < 0)),
                   "edge_ratio_p99": round(float(np.percentile(ratios, 99)), 4), "inner_dihedral_deg_max": round(max(dih(N)), 3)}
    return res


def state_coords_local(face, key):
    keys = face.data.shape_keys.key_blocks
    base = np.array([v.co[:] for v in keys[0].data]) + R4.DESIGN_OFF(face)
    if key is None:
        return base
    return base + np.array([v.co[:] for v in keys[key].data]) - np.array([v.co[:] for v in keys[0].data])


def render_sets(st, face, originals, tag, eye_c, face_c, eyes_ctr, full):
    allstates = ["neutral", "blink", "blink_l", "blink_r", "joy", "surprised"]
    st.centre = face_c
    R4.render_set(st, face, originals, tag, ["neutral"], VIEWS5, ["toon"] + (["clay", "wire"] if full else []), R.FACE_SCALE)
    R4.render_set(st, face, originals, tag, allstates[1:], ["front", "q3L"], ["toon"], R.FACE_SCALE)
    for side, ctr in eyes_ctr.items():
        st.centre = Vector((ctr[0], eye_c.y, ctr[1]))
        R4.render_set(st, face, originals, f"{tag}_eye{side}", allstates, ["front"], ["clay"], 0.05)
        R4.render_set(st, face, originals, f"{tag}_eye{side}", ["neutral"], ["q3L", "q3R"], ["clay", "toon"], 0.05)
        if full:
            R4.render_set(st, face, originals, f"{tag}_eye{side}", ["neutral", "blink"], ["front"], ["wire"], 0.05)
    st.centre = face_c


def measure_all(face, eyes, opening, rims):
    ix = R4.measure_states(face)
    rim_y = {k: v["y"] for k, v in rims.items()}
    sock, prot = {}, {}
    for sname in ["neutral", "blink", "blink_l", "blink_r", "joy", "surprised", "angry", "sorrow", "fun"]:
        R4.set_state(face, STATES[sname])
        sock[sname] = R4.socket_show_through(face, opening, rim_y)
        prot[sname] = R4.eye_surface_protrusion(face, eyes, rims)
    R4.set_state(face, None)
    return ix, sock, prot


def rims_from_margin(data):
    out = {}
    for s, d in data.items():
        pts = d["margin"]["upper"]["new"] + d["margin"]["lower"]["new"][::-1][1:-1]
        out[s] = {"xz": [(p[0], p[2]) for p in pts], "y": float(np.mean([p[1] for p in pts]))}
    return out


def opening_px(ext, U_m, U_px):
    s = U_px / U_m
    return {side: {"width_px": round((x1 - x0) * s, 2), "height_px": round((z1 - z0) * s, 2)} for side, (x0, x1, z0, z1) in ext.items()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    targets_doc = MT.compute()
    T = targets_doc["targets_3d"]
    # ---------------- Phase A: PR #316 baseline ------------------------------------------------
    M3.load()
    nrec = E.build_base(P04)
    face, body = bpy.data.objects["Face"], bpy.data.objects["Body"]
    U = nrec["baseline"]["normalisation"]["unit_U_m"]
    eye_c, face_c = anchors(nrec)
    vroid_open = R4.measure_states(face)["neutral"]["eye_visible_extent_m"]
    base_regions = {n: E.region_vertices(face, n, spec) for n, spec in E.ellipses(P04, nrec["baseline"]["landmarks"]).items() if n != "mouth"}
    base_rims = R4.rim_polygons(face)
    me = face.data
    base_region_pos = {n: {E.pkey(me.vertices[v].co) for v in vs} for n, vs in base_regions.items()}
    _, eyes0 = E.build(P04, nrec, vroid_open)
    me = face.data
    regions0 = {n: {v.index for v in me.vertices if E.pkey(v.co) in pos} for n, pos in base_region_pos.items()}
    base_ix, base_sock, base_prot = measure_all(face, eyes0, vroid_open, base_rims)
    base_stats = {n: region_stats(face, vs) for n, vs in regions0.items()}
    base_eye_ext = base_ix["neutral"]["eye_visible_extent_m"]
    base_pupils = {s: [round(c, 5) for c in (eyes0.matrix_world @ eyes0.data.vertices[0 if s == "R" else len(eyes0.data.vertices) // 2].co)]
                   for s in ("R", "L")}
    base_mouth = mouth_positions(face)
    base_eye_mat = mat_fingerprint(eyes0.data.materials[0])
    originals = {o.name: [s.material for s in o.material_slots] for o in bpy.context.scene.objects if o.type == "MESH"}
    st = R4.Stage(face_c)
    eyes_ctr0 = {s: (base_pupils[s][0], base_pupils[s][2]) for s in ("R", "L")}
    render_sets(st, face, originals, "base316", eye_c, face_c, eyes_ctr0, full=False)
    st.materials("original", originals)
    # ---------------- Phase B: eyelid candidate --------------------------------------------------
    M3.load()
    nrec = E.build_base(P04)
    face, body = bpy.data.objects["Face"], bpy.data.objects["Body"]
    me = face.data
    body_hash0 = pos_hash(body)
    nose0 = sorted(E.pkey(me.vertices[i].co) for i, a in enumerate(me.attributes[E.PATCH_ATTR].data) if a.value == 4)
    rec, eyes, data = B.build(P05, P04, nrec, T)
    me = face.data
    attr = me.attributes[E.PATCH_ATTR].data
    patches = {f"lid_{s}": {i for i, a in enumerate(attr) if a.value == B.SIDES[s]} for s in ("R", "L")}
    walls = {f"wall_{s}": {i for i, a in enumerate(attr) if a.value == B.SIDES[s] + B.WALL_OFFSET} for s in ("R", "L")}
    rims = rims_from_margin(data)
    cand_open = {s: (min(p[0] for p in r["xz"]), max(p[0] for p in r["xz"]), min(p[1] for p in r["xz"]), max(p[1] for p in r["xz"]))
                 for s, r in rims.items()}
    cand_ix, cand_sock, cand_prot = measure_all(face, eyes, cand_open, rims)
    cand_stats = {n: region_stats(face, vs) for n, vs in patches.items()}
    nose1 = sorted(E.pkey(me.vertices[i].co) for i, a in enumerate(attr) if a.value == 4)
    cand_mouth = mouth_positions(face)
    cand_eye_mat = mat_fingerprint(eyes.data.materials[0])
    # technical checks
    acc = P05["acceptance_technical"]
    canthus_err = {}
    for s in ("R", "L"):
        cv = rec[f"lid_{s}"]["canthus_vertex_world"]
        tg = rec[f"lid_{s}"]["canthus_target_xz"]
        canthus_err[s] = {k: round(1000 * math.hypot(cv[k][0] - tg[k][0], cv[k][2] - tg[k][1]), 4) for k in ("inner", "outer")}
    s_px = targets_doc["U_px"] / U
    open_cand = cand_ix["neutral"]["eye_visible_extent_m"]
    tgt_px = {s: {"width_px": round(T[s]["width_U"] * targets_doc["U_px"], 2), "height_px": round(T[s]["height_U"] * targets_doc["U_px"], 2)} for s in ("R", "L")}
    margin_px = {s: {"width_px": round((cand_open[s][1] - cand_open[s][0]) * s_px, 2), "height_px": round((cand_open[s][3] - cand_open[s][2]) * s_px, 2)} for s in ("R", "L")}
    pupils = {s: [round(c, 5) for c in (eyes.matrix_world @ eyes.data.vertices[0 if s == "R" else len(eyes.data.vertices) // 2].co)] for s in ("R", "L")}
    ipd_U = round(abs(pupils["R"][0] - pupils["L"][0]) / U, 4)
    opening = {"target": tgt_px, "candidate_margin": margin_px, "candidate_visible_eye": opening_px(open_cand, U, targets_doc["U_px"]),
               "baseline316_visible_eye": opening_px(base_eye_ext, U, targets_doc["U_px"]),
               "pupil_world": pupils, "pupil_target_xz": {s: T[s]["pupil_xz"] for s in ("R", "L")},
               "ipd_U": ipd_U, "ipd_target_U": T["ipd_U"],
               "baseline316_ipd_U": round(abs(base_pupils["R"][0] - base_pupils["L"][0]) / U, 4)}
    open_ok = all(abs(margin_px[s][k] - tgt_px[s][k]) <= acc["opening_tolerance_px"] for s in ("R", "L") for k in ("width_px", "height_px"))
    ipd_ok = abs(ipd_U - T["ipd_U"]) * targets_doc["U_px"] <= acc["opening_tolerance_px"]
    # corners and folds per state
    corners = {}
    for s in ("R", "L"):
        cv = rec[f"lid_{s}"]["canthus_vertex_world"]
        canthi = [np.array(cv["inner"]), np.array(cv["outer"])]
        b0 = state_coords_local(face, None)
        corners[s] = {sn: corner_metrics(face, patches[f"lid_{s}"], canthi, state_coords_local(face, STATES[sn]), b0, acc["corner_radius_m"])
                      for sn in REQ}
    corner_ok = all(v["flipped_vs_basis"] == 0 for s in corners.values() for v in s.values())
    rel = {}
    for n in patches:
        rows = {}
        for sn in STATES:
            if sn == "neutral":
                rows[sn] = {"baseline316": base_stats[n]["neutral"], "candidate": cand_stats[n]["neutral"],
                            "ok": cand_stats[n]["neutral"]["non_manifold_edges"] == 0}
                continue
            b, c = base_stats[n][sn], cand_stats[n][sn]
            ok = (c["folded_vs_basis"] <= b["folded_vs_basis"]
                  and c["edge_ratio_p99"] <= b["edge_ratio_p99"] * acc["relative_edge_ratio_margin"]
                  and c["inner_dihedral_deg_max"] <= b["inner_dihedral_deg_max"] + acc["relative_dihedral_margin_deg"])
            rows[sn] = {"baseline316": b, "candidate": c, "ok": ok, "required": sn in REQ}
        rel[n] = rows
    rel_ok = all(r["ok"] for rows in rel.values() for sn, r in rows.items() if sn in REQ)
    rel_all = {n: {sn: r["ok"] for sn, r in rows.items()} for n, rows in rel.items()}
    pen_ok = all(v["penetrating_samples"] == 0 for s_ in cand_ix.values() for v in s_["line_penetration"].values())
    closed = {sn: cand_ix[sn]["eye_visible_samples"] for sn in ("blink", "blink_l", "blink_r", "joy")}
    closed_ok = (closed["blink"]["R"] == 0 and closed["blink"]["L"] == 0 and closed["blink_l"]["L"] == 0
                 and closed["blink_r"]["R"] == 0)
    sock_ok = all(v["show_through_rays"] == 0 for s_ in cand_sock.values() for d_ in s_.values() for v in d_.values())
    prot_ok = cand_prot["neutral"]["uncovered_outside_rim"] == 0
    # mesh integrity
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
    patch_all = set().union(*patches.values(), *walls.values())
    skin_sign = np.sign(np.median([uv_area(p) for p in me.polygons if p.material_index == si and not any(v in patch_all for v in p.vertices)]))
    ppolys = [p for p in me.polygons if all(v in patch_all for v in p.vertices)]
    wsum = [sum(g.weight for g in me.vertices[i].groups) for i in patch_all]
    tri = sum(1 for p in ppolys if len(p.vertices) != 4)
    checks = {
        "canthus_error_mm": canthus_err,
        "canthus_ok": all(v <= acc["canthus_error_max_mm"] for s in canthus_err.values() for v in s.values()),
        "opening_within_1px": open_ok, "ipd_within_1px": ipd_ok,
        "corner_no_flip_required_states": corner_ok,
        "patch_relative_required_states_ok": rel_ok,
        "line_penetration_zero_all_states": pen_ok,
        "eyes_hidden_when_closed": closed_ok,
        "socket_show_through_zero": sock_ok,
        "eye_surface_protrusion_neutral": cand_prot["neutral"]["uncovered_outside_rim"],
        "nose_locked_geometry_unchanged": nose0 == nose1,
        "body_mesh_unchanged": body_hash0 == pos_hash(body),
        "mouth_unchanged_vs_316": cand_mouth == base_mouth,
        "eye_material_unchanged_vs_316": cand_eye_mat == base_eye_mat,
        "face_body_seam_vertices": len(seam), "face_body_seam_max_gap_m": round(max(seam), 7) if seam else None,
        "winding_conflicts": R.winding_conflicts(face, patch_all),
        "uv_flipped_faces": sum(1 for p in ppolys if np.sign(uv_area(p)) != skin_sign),
        "uv_out_of_range_loops": sum(1 for p in ppolys for li in p.loop_indices if not (0 <= uvl[li].uv.x <= 1 and 0 <= uvl[li].uv.y <= 1)),
        "non_quad_patch_faces": tri,
        "weights_sum_min": round(min(wsum), 6), "weights_sum_max": round(max(wsum), 6),
        "shape_keys_preserved": [k.name for k in me.shape_keys.key_blocks[1:57]] == [f"target_{i}" for i in range(56)],
    }
    tech_pass = (checks["canthus_ok"] and open_ok and ipd_ok and corner_ok and rel_ok and pen_ok and closed_ok and sock_ok
                 and prot_ok and checks["nose_locked_geometry_unchanged"] and checks["body_mesh_unchanged"]
                 and checks["mouth_unchanged_vs_316"] and checks["eye_material_unchanged_vs_316"]
                 and checks["winding_conflicts"] == 0 and checks["uv_flipped_faces"] == 0 and checks["uv_out_of_range_loops"] == 0
                 and tri == 0 and abs(checks["weights_sum_min"] - 1) < 1e-3 and abs(checks["weights_sum_max"] - 1) < 1e-3
                 and checks["shape_keys_preserved"])
    # ---------------- renders -------------------------------------------------------------------
    originals = {o.name: [s.material for s in o.material_slots] for o in bpy.context.scene.objects if o.type == "MESH"}
    st = R4.Stage(face_c)
    eyes_ctr = {s: (pupils[s][0], pupils[s][2]) for s in ("R", "L")}
    render_sets(st, face, originals, "cand", eye_c, face_c, eyes_ctr, full=True)
    # Layer 0 overlay: candidate front toon at the reference pixel scale, target curves drawn on top
    st.centre = Vector((M3.MID_X, eye_c.y, T["R"]["pupil_xz"][1]))
    k = 10
    crop_px = (96, 36)
    scale = crop_px[0] / s_px
    R4.render_set(st, face, originals, "cand_l0", ["neutral"], ["front"], ["toon"], scale)
    st.centre = face_c
    st.materials("original", originals)
    sheets(targets_doc, T, s_px, scale, crop_px, k)
    # ---------------- report --------------------------------------------------------------------
    trial = OUT / "EYE_TARGETS_05.json"
    report = {
        "task_id": P05["task_id"], "method_id": P05["method_id"], "method_family": P05["method_family"],
        "params_sha256": sha(PARAMS_PATH), "elm04_params_sha256": sha(E.PARAMS_PATH), "blender_version": bpy.app.version_string,
        "source_vrm_sha256": M3.VRM_SHA256, "source_modified": False, "layer0_front_sha256": targets_doc["source"]["sha256"],
        "targets": {"symmetry_decision": targets_doc["symmetry_decision"], "mirror_comparison_px": targets_doc["mirror_comparison_px"],
                    "canthi_shared": targets_doc["canthi_shared"], "eye_targets_sha256": sha(trial)},
        "build": rec, "opening": opening, "canthus_corner_metrics": corners,
        "baseline316_intersections": base_ix, "candidate_intersections": cand_ix,
        "socket_show_through": {"baseline316": base_sock, "candidate": cand_sock},
        "eye_surface_protrusion": {"baseline316": base_prot, "candidate": cand_prot},
        "patch_relative": rel, "patch_relative_ok_all_states": rel_all,
        "technical_checks": checks, "technical_result": "PASS" if tech_pass else "FAIL",
        "renders": st.records, "sheets": {p.name: sha(p) for p in sorted(OUT.glob("SHEET_*.png"))},
        "G1": "PASS for source preservation only (Layer 0 front SHA verified; v5.61 binary unavailable -> full canon BLOCKED)",
        "G2": "NOT_RUN - independent art review mandatory", "G3": "PASS" if tech_pass else "FAIL", "G4": "NOT_RUN",
    }
    for o in bpy.context.scene.objects:
        m_ = o.modifiers.get("TOON_OUTLINE_HULL") if o.type == "MESH" else None
        if m_ is not None:
            o.modifiers.remove(m_)
    R4.set_state(face, None)
    bpy.ops.wm.save_as_mainfile(filepath=str((OUT / "MORWEN_EYELID_05_CANDIDATE.blend").resolve()), compress=True, copy=True)
    (OUT / "EYELID_05_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=float) + "\n")
    assert sha(M3.SRC) == M3.VRM_SHA256
    print("EYELID05 technical:", report["technical_result"], json.dumps(checks, default=float))


def sheets(targets_doc, T, s_px, scale, crop_px, k):
    Rr = OUT / "renders"
    f_ = lambda tag, s, v, m: Rr / f"{tag}_{s}" / f"{v}_{m}_face.png"  # noqa: E731
    st6 = ["neutral", "blink", "blink_l", "blink_r", "joy", "surprised"]
    R.grid([("#316 baseline toon", [(v, f_("base316", "neutral", v, "toon")) for v in VIEWS5]),
            ("candidate toon", [(v, f_("cand", "neutral", v, "toon")) for v in VIEWS5]),
            ("candidate clay", [(v, f_("cand", "neutral", v, "clay")) for v in VIEWS5]),
            ("candidate wire", [(v, f_("cand", "neutral", v, "wire")) for v in VIEWS5])],
           300, OUT / "SHEET_VIEWS_316_VS_05.png", "Neutral: #316 baseline vs eyelid candidate - front, 45 L/R, full sides (validation toon / clay / wire)")
    rows = []
    for tag, lab in (("base316", "#316"), ("cand", "cand")):
        for v in ("front", "q3L"):
            rows.append((f"{lab} {v}", [(s, f_(tag, s, v, "toon")) for s in st6]))
    R.grid(rows, 260, OUT / "SHEET_EYELID_STATES_TOON.png", "Blink / Blink_L / Blink_R / Joy / Surprised - #316 vs candidate (validation toon)")
    rows = []
    for side in ("R", "L"):
        for tag, lab in (("base316", "#316"), ("cand", "cand")):
            rows.append((f"{lab} eye {side} clay", [(s, f_(f"{tag}_eye{side}", s, "front", "clay")) for s in st6]))
        rows.append((f"cand eye {side}", [(f"{s} wire", f_(f"cand_eye{side}", s, "front", "wire")) for s in ("neutral", "blink")]
                     + [(f"{v} {m}", f_(f"cand_eye{side}", "neutral", v, m)) for v in ("q3L", "q3R") for m in ("clay", "toon")]))
    R.grid(rows, 240, OUT / "SHEET_EYE_CLOSEUPS.png", "Per-eye close-ups: canthus corners and lid edge under the required states (clay, wire, 45 deg)")
    # Layer 0 overlay
    ref = Image.open(MT.C.MANIFEST.parent / "references" / targets_doc["source"]["file"]).convert("RGBA")
    mx, ey = targets_doc["mid_pupil_x_px"], targets_doc["eye_line_y_px"]
    cy_px = ey - (T["R"]["pupil_xz"][1] - 1.44589) * s_px
    box = (int(round(mx - crop_px[0] / 2)), int(round(cy_px - crop_px[1] / 2)))
    crop = ref.crop((box[0], box[1], box[0] + crop_px[0], box[1] + crop_px[1]))
    bg = Image.new("RGBA", crop.size, (255, 255, 255, 255))
    bg.alpha_composite(crop)
    W, H = crop_px[0] * k, crop_px[1] * k
    ref_big = bg.convert("RGB").resize((W, H), Image.NEAREST)
    cand = Image.open(f_("cand_l0", "neutral", "front", "toon")).convert("RGB")
    cw = cand.size[0]
    cc = cand.crop((0, (cw - cw * crop_px[1] // crop_px[0]) // 2, cw, (cw + cw * crop_px[1] // crop_px[0]) // 2)).resize((W, H), Image.LANCZOS)

    def draw(img):
        d = ImageDraw.Draw(img)
        for s in ("R", "L"):
            for nm, col in (("upper_xz", (0, 200, 255)), ("lower_xz", (255, 150, 0))):
                pts = [((mx - (x - M3.MID_X) * s_px - box[0]) * k, (ey - (z - 1.44589) * s_px - box[1]) * k) for x, z in T[s][nm]]
                d.line(pts, fill=col, width=3)
        return img
    out = Image.new("RGB", (W, H * 2 + 40), (232, 232, 228))
    out.paste(draw(ref_big), (0, 20))
    out.paste(draw(cc), (0, H + 40))
    d = ImageDraw.Draw(out)
    d.text((4, 4), "Layer 0 front (SHA-verified) + target lid margins", fill=(0, 0, 0))
    d.text((4, H + 24), "candidate front toon, same pixel scale + the same target curves", fill=(0, 0, 0))
    out.save(OUT / "SHEET_LAYER0_FIT.png")
    big = {tag: Image.open(f_(tag, "neutral", "front", "toon")).convert("RGB") for tag in ("base316", "cand")}
    rows = []
    for tag, lab in (("base316", "#316"), ("cand", "candidate")):
        rows.append((lab, [(f"{px}px", big[tag].resize((px, px), Image.LANCZOS).resize((300, 300), Image.NEAREST)) for px in (128, 64, 32)]))
    R.grid(rows, 300, OUT / "SHEET_GAME_SIZE_64_32.png", "Game-size check: toon face crop at 128 / 64 / 32 px (nearest upscale), #316 vs candidate")


if __name__ == "__main__":
    main()
