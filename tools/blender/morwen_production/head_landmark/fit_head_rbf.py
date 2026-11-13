"""MORWEN-HEAD-LANDMARK-02: landmark-constrained, topology-locked RBF warp of the VRoid head.

Production base for method 1 (constrained deformation). TECHNICAL CANDIDATE ONLY - never an art
approval. All work happens on the in-memory import; the source VRM is never saved or exported.

Inputs (in $MORWEN_OUT): HEAD_LANDMARKS_3D.json, CANONICAL_LANDMARKS_2D.json, LANDMARK_COMPARISON.json
Params: fit_params_v1.json (next to this script; override with MORWEN_FIT_PARAMS)
Outputs: FIT_CANDIDATE_REPORT.json, HEAD_LANDMARKS_3D_CANDIDATE.json, LANDMARK_COMPARE_CANDIDATE_*.png

Displacement targets come only from the calibrated comparison: for a delta d (model_px - canonical_px)
  front view: dX = +dx/s, dZ = +dy/s      right view: dY = -dx/s      left view: dY = +dx/s
Axes not listed for a handle keep zero displacement. The field is evaluated on Face (all parts,
basis + every shape key) and on Body vertices above the neck with a smooth falloff, so the
Face/Body border (coincident vertices) receives identical displacement.
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

HERE = Path(__file__).resolve().parent


def _load(name):
    spec = importlib.util.spec_from_file_location(f"morwen_lm_{name}", HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


M3 = _load("measure_head_landmarks_3d")
CMP = _load("compare_head_landmarks")
OUT = M3.OUT
PARAMS = Path(os.environ.get("MORWEN_FIT_PARAMS", HERE / "fit_params_v1.json"))


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def targets(params, l3, l2, cmp):
    s = cmp["calibration"]["s_px_per_m"]
    d = {}
    for r in cmp["landmark_deltas"]:
        if "delta_px" in r:
            d[(r["view"], r["landmark"])] = (r["delta_px"], r["status"])
    L = l3["landmarks"]
    handles, log = [], {}
    for name, spec in params["handles"].items():
        disp = [0.0, 0.0, 0.0]
        used = {}
        for axis, src in spec["axes"].items():
            vals = []
            if src == "front":
                dp, st = d[("front", name)]
                assert st in ("MEASURED", "ANCHOR_PAIR"), f"{name} front delta is {st}"
                vals.append(dp[0] / s if axis == "x" else dp[1] / s)
            elif src == "sides":
                for view, sign in (("right", -1), ("left", 1)):
                    key = (view, name)
                    if key not in d:
                        continue
                    dp, st = d[key]
                    assert st == "MEASURED", f"{name} {view} delta is {st}"
                    vals.append(sign * dp[0] / s if axis == "y" else dp[1] / s)
            i = "xyz".index(axis)
            disp[i] = float(np.mean(vals))
            used[axis] = {"source": src, "values_m": [round(v, 5) for v in vals]}
        handles.append((Vector(L[name]["position"]), Vector(disp)))
        log[name] = {"displacement_m": [round(v, 5) for v in disp], "from": used}
    anchors = [Vector(L[k]["position"]) for k in params["zero_anchors"] if k in L]
    nj = Vector(L["neck_joint"]["position"])
    ns = l3["neck_section"]
    for dz in params["zero_anchor_rings"]["neck_ring_z_offset_m"]:
        for ang in range(0, 360, 45):
            a = np.radians(ang)
            anchors.append(Vector((nj.x + ns["half_width_x"] * np.cos(a),
                                   (ns["front_y"] + ns["back_y"]) / 2 + (ns["front_y"] - ns["back_y"]) / 2 * np.sin(a),
                                   nj.z + dz)))
    sk = Vector(L["vertex_skull"]["position"])
    hj = Vector(l3["rig"]["head_joint"])
    n = params["zero_anchor_rings"]["back_of_head_samples"]
    for i in range(n):
        a = np.pi * (i + 0.5) / n
        anchors.append(Vector((hj.x + 0.08 * np.cos(a), hj.y - 0.09 * np.sin(a), (hj.z + sk.z) / 2)))
    return handles, anchors, log


class RBF:
    def __init__(self, centres, disp, reg):
        C = np.array(centres, dtype=np.float64)
        D = np.array(disp, dtype=np.float64)
        n = len(C)
        K = np.linalg.norm(C[:, None] - C[None], axis=-1)
        P = np.hstack([np.ones((n, 1)), C])
        A = np.zeros((n + 4, n + 4))
        A[:n, :n] = K + reg * np.eye(n)
        A[:n, n:] = P
        A[n:, :n] = P.T
        rhs = np.zeros((n + 4, 3))
        rhs[:n] = D
        sol = np.linalg.solve(A, rhs)
        self.C, self.w, self.a = C, sol[:n], sol[n:]

    def __call__(self, X):
        X = np.asarray(X, dtype=np.float64)
        K = np.linalg.norm(X[:, None] - self.C[None], axis=-1)
        return K @ self.w + np.hstack([np.ones((len(X), 1)), X]) @ self.a


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def snapshot(obj):
    me = obj.data
    return {"polys": sha_bytes(np.array([v for p in me.polygons for v in p.vertices], dtype=np.int32).tobytes()),
            "nverts": len(me.vertices),
            "shape_keys": [k.name for k in me.shape_keys.key_blocks] if me.shape_keys else [],
            "vgroups": [g.name for g in obj.vertex_groups]}


def world_co(obj, coords):
    mw = np.array(obj.matrix_world)
    X = np.hstack([coords, np.ones((len(coords), 1))]) @ mw.T
    return X[:, :3]


def to_local(obj, world):
    mi = np.array(obj.matrix_world.inverted())
    return (np.hstack([world, np.ones((len(world), 1))]) @ mi.T)[:, :3]


def apply_field(obj, field, weight_fn):
    me = obj.data
    blocks = list(me.shape_keys.key_blocks) if me.shape_keys else [None]
    base = np.array([v.co[:] for v in me.vertices])
    moved = {}
    for kb in blocks:
        local = np.array([d.co[:] for d in kb.data]) if kb else base.copy()
        W = world_co(obj, local)
        w = weight_fn(world_co(obj, base))  # weight from basis position: identical per vertex across keys
        newW = W + field(W) * w[:, None]
        new = to_local(obj, newW)
        if kb:
            kb.data.foreach_set("co", new.ravel())
        moved[kb.name if kb else "basis"] = float(np.abs(new - local).max())
    if not me.shape_keys:
        me.vertices.foreach_set("co", np.array(new).ravel())
    else:
        me.vertices.foreach_set("co", np.array([d.co[:] for d in me.shape_keys.key_blocks[0].data]).ravel())
    me.update()
    return moved


def tri_stats(obj, before_world, si=None):
    me = obj.data
    me.calc_loop_triangles()
    tris = np.array([t.vertices[:] for t in me.loop_triangles if si is None or t.material_index == si])
    after = world_co(obj, np.array([v.co[:] for v in me.vertices]))

    def normals(P):
        a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
        return np.cross(b - a, c - a)
    n0, n1 = normals(before_world), normals(after)
    flips = int(((n0 * n1).sum(1) < 0).sum())
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    l0 = np.linalg.norm(before_world[e[:, 0]] - before_world[e[:, 1]], axis=1)
    l1 = np.linalg.norm(after[e[:, 0]] - after[e[:, 1]], axis=1)
    ok = l0 > 1e-7
    ratio = l1[ok] / l0[ok]
    return {"triangles": int(len(tris)), "flipped": flips,
            "edge_ratio_p1": round(float(np.percentile(ratio, 1)), 4),
            "edge_ratio_p50": round(float(np.percentile(ratio, 50)), 4),
            "edge_ratio_p99": round(float(np.percentile(ratio, 99)), 4),
            "max_displacement_m": round(float(np.linalg.norm(after - before_world, axis=1).max()), 5)}


def main():
    params = json.loads(PARAMS.read_text())
    np.random.seed(params["seed"])
    l3 = json.loads((OUT / "HEAD_LANDMARKS_3D.json").read_text())
    l2 = json.loads((OUT / "CANONICAL_LANDMARKS_2D.json").read_text())
    cmp = json.loads((OUT / "LANDMARK_COMPARISON.json").read_text())
    handles, anchors, log = targets(params, l3, l2, cmp)
    centres = [h[0] for h in handles] + anchors
    disp = [h[1] for h in handles] + [Vector()] * len(anchors)
    field = RBF(centres, disp, params["regularisation"])

    M3.load()
    face, body = bpy.data.objects["Face"], bpy.data.objects["Body"]
    snap0 = {o.name: snapshot(o) for o in (face, body)}
    before = {o.name: world_co(o, np.array([v.co[:] for v in o.data.vertices])) for o in (face, body)}
    nz = l3["rig"]["neck_joint"][2]
    moved = {
        "Face": apply_field(face, field, lambda W: np.ones(len(W))),
        "Body": apply_field(body, field, lambda W: smoothstep(nz - 0.01, nz + 0.02, W[:, 2]) * (np.abs(W[:, 0]) < 0.2)),
    }
    snap1 = {o.name: snapshot(o) for o in (face, body)}
    si_face = M3.slot_index(face, "Face_00_SKIN")
    stats = {"Face_skin": tri_stats(face, before["Face"], si_face), "Body": tri_stats(body, before["Body"])}
    # Face/Body seam coincidence after the warp
    bw = world_co(body, np.array([v.co[:] for v in body.data.vertices]))
    from mathutils.kdtree import KDTree
    kd = KDTree(len(bw))
    for i, p in enumerate(bw):
        kd.insert(p, i)
    kd.balance()
    border0 = before["Face"]
    kd0 = KDTree(len(before["Body"]))
    for i, p in enumerate(before["Body"]):
        kd0.insert(p, i)
    kd0.balance()
    seam_idx = [i for i, p in enumerate(border0) if kd0.find(p)[2] < 1e-4]
    after_face = world_co(face, np.array([v.co[:] for v in face.data.vertices]))
    gaps = [kd.find(after_face[i])[2] for i in seam_idx]

    cand = M3.measure()
    (OUT / "HEAD_LANDMARKS_3D_CANDIDATE.json").write_text(json.dumps(cand, ensure_ascii=False, indent=2) + "\n")
    mp = CMP.Mapping(l3, l2)           # baseline calibration frame (fixed s and anchors)
    mp.L = {k: Vector(v["position"]) for k, v in cand["landmarks"].items()}
    mp.st3 = {k: v["status"] for k, v in cand["landmarks"].items()}
    rows = CMP.compare(mp)
    renders = CMP.render(mp, reload=False, tag="_CANDIDATE")
    CMP.draw(mp, renders, rows, tag="_CANDIDATE")

    base_rows = {(r["view"], r["landmark"]): r for r in cmp["landmark_deltas"] if "delta_U" in r}
    resid = []
    for r in rows:
        if "delta_U" not in r:
            continue
        b = base_rows.get((r["view"], r["landmark"]))
        resid.append({"view": r["view"], "landmark": r["landmark"], "status": r["status"],
                      "baseline_delta_U": b["delta_U"] if b else None, "candidate_delta_U": r["delta_U"],
                      "is_handle": r["landmark"] in params["handles"]})
    acc = params["acceptance_technical"]
    checks = {
        "topology_unchanged": all(snap0[k]["polys"] == snap1[k]["polys"] and snap0[k]["nverts"] == snap1[k]["nverts"] for k in snap0),
        "shape_key_names_unchanged": all(snap0[k]["shape_keys"] == snap1[k]["shape_keys"] for k in snap0),
        "vertex_groups_unchanged": all(snap0[k]["vgroups"] == snap1[k]["vgroups"] for k in snap0),
        "flipped_triangles": stats["Face_skin"]["flipped"] + stats["Body"]["flipped"],
        "face_body_seam_max_gap_m": round(max(gaps), 7) if gaps else None,
        "seam_vertices_checked": len(gaps),
        "edge_ratio_p99": stats["Face_skin"]["edge_ratio_p99"],
        "edge_ratio_p1": stats["Face_skin"]["edge_ratio_p1"],
    }
    tech_pass = (checks["topology_unchanged"] and checks["shape_key_names_unchanged"] and checks["vertex_groups_unchanged"]
                 and checks["flipped_triangles"] <= acc["max_flipped_triangles"]
                 and checks["face_body_seam_max_gap_m"] is not None and checks["face_body_seam_max_gap_m"] <= acc["face_body_seam_max_gap_m"]
                 and checks["edge_ratio_p99"] <= acc["edge_length_ratio_p99_max"] and checks["edge_ratio_p1"] >= acc["edge_length_ratio_p1_min"])
    report = {
        "task_id": "MORWEN-HEAD-LANDMARK-02", "method_id": params["method_id"], "method_family": params["method_family"],
        "params_sha256": sha_bytes(PARAMS.read_bytes()), "seed": params["seed"],
        "blender_version": bpy.app.version_string, "source_vrm_sha256": M3.VRM_SHA256, "source_modified": False,
        "candidate_saved_to_disk": False,
        "handles": log, "zero_anchor_count": len(anchors),
        "max_shape_key_vertex_move_m": moved, "mesh_stats": stats, "technical_checks": checks,
        "technical_result": "PASS" if tech_pass else "FAIL",
        "landmark_residuals": resid,
        "G1": "PASS (source and Layer 0 SHA verified; v5.61 canon binary not in GitHub -> design-canon comparison BLOCKED)",
        "G2": "NOT_RUN - candidate is a warped stock VRoid face without canonical eyes, hair, hat or glasses; art review required",
        "G3": "PASS" if tech_pass else "FAIL", "G4": "NOT_RUN",
    }
    (OUT / "FIT_CANDIDATE_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    assert M3.sha(M3.SRC) == M3.VRM_SHA256
    print("fit technical:", report["technical_result"], checks)


if __name__ == "__main__":
    main()
