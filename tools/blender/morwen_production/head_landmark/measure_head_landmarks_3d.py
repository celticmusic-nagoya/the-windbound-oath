"""MORWEN-HEAD-LANDMARK-02: measure facial landmarks on the complete VRoid Face+Body head.

Read-only. Measurements are taken in Blender world metres after glTF import (model faces +Y,
character right = +X). Basis shape, rest pose. Source VRM SHA-256 is asserted unchanged.

Each landmark carries a status:
  MEASURED                 deterministic rule on geometry or visible texture texels
  MEASURED_IN_DEFINED_ROI  deterministic rule inside a region derived from other measured landmarks
  ESTIMATED                no clear geometric feature in this mesh; value is a documented approximation
Visible texels: overlay materials (eye white, iris) are planes with alpha textures, so their
mesh bounds are NOT the visible eye. We sample each triangle on a fixed barycentric grid and keep
points whose texture alpha >= ALPHA_MIN (nearest-texel lookup, no randomness).

Output: $MORWEN_OUT/HEAD_LANDMARKS_3D.json
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

SRC = Path(os.environ.get("MORWEN_VRM", "render_output/morwen_vroid_review/Base_Female.vrm"))
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_head_landmark_02"))
VRM_SHA256 = "1995f174f6c8f2211f3c56c9e5fe4f9daf27ee5e648f129479582a259238149b"
ALPHA_MIN = 0.5
GRID = 12          # barycentric samples per triangle edge
MID_X = 0.00026  # VRoid symmetry plane; verified each run by mirror_deviation
SEED = 20261114
CHIN_BAND_M = 3.0 / 560.0  # 3 sheet px at the calibrated 560 px/m (recomputed in comparison)    # recorded; the algorithm itself draws no random numbers
np.random.seed(SEED)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def r(v, n=5):
    return [round(float(x), n) for x in v]


def load():
    assert SRC.is_file(), f"source missing: {SRC}"
    assert sha(SRC) == VRM_SHA256, "pinned VRM SHA-256 mismatch"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SRC.resolve()))


def slot_index(obj, key):
    hits = [i for i, s in enumerate(obj.material_slots) if s.material and key in s.material.name]
    assert hits, f"{obj.name}: no material containing {key}"
    return hits[0]


def image_of(mat):
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image:
            return n.image
    raise AssertionError(f"no image on {mat.name}")


def tex_alpha(img):
    w, h = img.size
    return np.asarray(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., 3], w, h


class FrontOcclusion:
    """Ray test toward the front camera (+Y) through the Face mesh. Eye parts (white, iris,
    highlight, extra) never occlude; every other Face material occludes where its texel alpha >= ALPHA_MIN."""
    EYE_PARTS = ("EyeWhite", "EyeIris", "EyeHighlight", "EyeExtra")

    def __init__(self, obj):
        me = obj.data
        me.calc_loop_triangles()
        mw = obj.matrix_world
        self.co = [mw @ v.co for v in me.vertices]
        uv = me.uv_layers.active.data
        self.tris = [(t.vertices[:], [uv[li].uv.to_3d() for li in t.loops], t.material_index) for t in me.loop_triangles]
        self.bvh = BVHTree.FromPolygons(self.co, [t[0] for t in self.tris])
        self.alpha = {}
        for i, s in enumerate(obj.material_slots):
            if any(k in s.material.name for k in self.EYE_PARTS):
                self.alpha[i] = None
            else:
                self.alpha[i] = tex_alpha(image_of(s.material))

    def visible(self, p, direction=Vector((0, 1, 0))):
        origin = p + direction * 1e-5
        for _ in range(32):
            hit, _, idx, _ = self.bvh.ray_cast(origin, direction)
            if hit is None:
                return True
            vs, uvs, mi = self.tris[idx]
            a = self.alpha[mi]
            if a is not None:
                arr, w, h = a
                u = barycentric_transform(hit, *(self.co[v] for v in vs), *uvs)
                px = min(w - 1, max(0, int(u.x * w)))
                py = min(h - 1, max(0, int(u.y * h)))
                if arr[py, px] >= ALPHA_MIN:
                    return False
            origin = hit + direction * 1e-5
        return False


def visible_points(obj, key, occ=None):
    """World positions of texels with alpha >= ALPHA_MIN on faces of material `key`;
    with `occ`, only texels not hidden from the front camera."""
    si = slot_index(obj, key)
    alpha, w, h = tex_alpha(image_of(obj.material_slots[si].material))
    me = obj.data
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    mw = obj.matrix_world
    bary = [(i / GRID, j / GRID) for i in range(GRID + 1) for j in range(GRID + 1 - i)]
    pts = []
    for t in me.loop_triangles:
        if t.material_index != si:
            continue
        P = [mw @ me.vertices[v].co for v in t.vertices]
        U = [uv[li].uv for li in t.loops]
        for a, b in bary:
            c = 1.0 - a - b
            u = U[0] * a + U[1] * b + U[2] * c
            px = min(w - 1, max(0, int(u.x * w)))
            py = min(h - 1, max(0, int(u.y * h)))
            if alpha[py, px] >= ALPHA_MIN:
                q = P[0] * a + P[1] * b + P[2] * c
                if occ is None or occ.visible(q):
                    pts.append(q)
    return pts


def skin_vertices():
    out = []
    for name in ("Face", "Body"):
        o = bpy.data.objects[name]
        si = slot_index(o, "_SKIN")
        mw = o.matrix_world
        idx = {v for p in o.data.polygons if p.material_index == si for v in p.vertices}
        out += [mw @ o.data.vertices[i].co for i in idx]
    return out


def face_skin_triangles(face):
    me = face.data
    me.calc_loop_triangles()
    si = slot_index(face, "Face_00_SKIN")
    mw = face.matrix_world
    co = np.array([tuple(mw @ v.co) for v in me.vertices])
    idx = np.array([t.vertices[:] for t in me.loop_triangles if t.material_index == si])
    return co[idx]  # (n, 3, 3)


def slice_plane(tri, axis, value):
    """Intersection points of triangles with the plane coord[axis] == value."""
    d = tri[:, :, axis] - value
    out = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        m = (d[:, i] * d[:, j]) < 0
        t = d[m, i] / (d[m, i] - d[m, j])
        out.append(tri[m, i] + (tri[m, j] - tri[m, i]) * t[:, None])
    return np.concatenate(out) if out else np.zeros((0, 3))


def lm(pos, status, method, views):
    return {"position": r(pos), "status": status, "method": method, "views": views}


def side_split(pts):
    # character right = +X; split at the model's own symmetry plane (x = 0.00026 m measured)
    return {"R": [p for p in pts if p.x > MID_X], "L": [p for p in pts if p.x < MID_X]}


def centroid(pts):
    return sum(pts, Vector()) / len(pts)


def measure():
    """Measure the head currently in the scene (source import or an in-memory candidate)."""
    face = bpy.data.objects["Face"]
    arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    neck_joint = arm.matrix_world @ arm.data.bones["J_Bip_C_Neck"].head_local
    head_joint = arm.matrix_world @ arm.data.bones["J_Bip_C_Head"].head_local
    # head region only: above the neck joint and inside the shoulders (T-pose arms excluded)
    skin = [p for p in skin_vertices() if p.z > neck_joint.z and abs(p.x) < 0.2]
    face_skin = [face.matrix_world @ face.data.vertices[v].co for p in face.data.polygons
                 if p.material_index == slot_index(face, "Face_00_SKIN") for v in p.vertices]
    L = {}

    # --- eyes (visible texels) -------------------------------------------------
    occ = FrontOcclusion(face)
    white = side_split(visible_points(face, "EyeWhite", occ))
    iris = side_split(visible_points(face, "EyeIris", occ))
    brow = side_split(visible_points(face, "FaceBrow"))
    for s in ("R", "L"):
        opening = white[s] + iris[s]
        inner = min(opening, key=lambda p: abs(p.x))
        outer = max(opening, key=lambda p: abs(p.x))
        L[f"eye_inner_{s}"] = lm(inner, "MEASURED", "min |x| of front-visible eye-white+iris texels (ray occlusion by lids/lines)", ["front"])
        L[f"eye_outer_{s}"] = lm(outer, "MEASURED", "max |x| of front-visible eye-white+iris texels", ["front", "side"])
        L[f"pupil_{s}"] = lm(centroid(iris[s]), "MEASURED", "centroid of front-visible iris texels", ["front", "side"])
        L[f"eye_top_{s}"] = lm(max(opening, key=lambda p: p.z), "MEASURED", "max z of front-visible eye opening", ["front"])
        L[f"eye_bottom_{s}"] = lm(min(opening, key=lambda p: p.z), "MEASURED", "min z of front-visible eye opening", ["front"])
        L[f"brow_top_{s}"] = lm(max(brow[s], key=lambda p: p.z), "MEASURED", "max z of visible brow texels", ["front"])
    eye_line_z = (L["pupil_R"]["position"][2] + L["pupil_L"]["position"][2]) / 2
    eye_bottom_z = min(L["eye_bottom_R"]["position"][2], L["eye_bottom_L"]["position"][2])
    brow_top_z = max(L["brow_top_R"]["position"][2], L["brow_top_L"]["position"][2])

    # --- centre-line profile (|x| < 2 mm) ---------------------------------------
    mid_x = (L["pupil_R"]["position"][0] + L["pupil_L"]["position"][0]) / 2
    mid = sorted((p for p in face_skin + skin if abs(p.x - mid_x) < 0.002), key=lambda p: p.z)
    front_mid = [p for p in mid if p.y > head_joint.y]
    pron = max((p for p in front_mid if eye_bottom_z - 0.04 < p.z < eye_bottom_z), key=lambda p: p.y)
    L["pronasale"] = lm(pron, "MEASURED", "max y on centre line below eye opening", ["front", "side"])
    nas = min((p for p in front_mid if pron.z < p.z < brow_top_z), key=lambda p: p.y)
    L["nasion"] = lm(nas, "MEASURED", "min y on centre line between nose tip and brow top", ["side"])
    men = min((p for p in front_mid if p.y > nas.y - 0.03), key=lambda p: p.z)
    L["menton"] = lm(men, "MEASURED", "lowest centre-line skin point in front of nasion-30mm (front-view chin tip)", ["front", "side"])
    top = max(skin, key=lambda p: p.z)
    L["vertex_skull"] = lm(top, "MEASURED", "highest Face/Body skin vertex (skull, under hair)", ["front", "side", "back"])
    hair = [bpy.data.objects["Body"].matrix_world @ v.co for v in bpy.data.objects["Body"].data.vertices]
    hb = slot_index(bpy.data.objects["Body"], "HairBack")
    hair = [hair[v] for p in bpy.data.objects["Body"].data.polygons if p.material_index == hb for v in p.vertices]
    L["hair_cap_top"] = lm(max(hair, key=lambda p: p.z), "MEASURED", "highest HairBack vertex (stock texture cap; REBUILD)", ["front", "side", "back"])

    # --- mouth: junction ring between skin and mouth interior -------------------
    si_skin = slot_index(face, "Face_00_SKIN")
    si_mouth = slot_index(face, "FaceMouth")
    mats_at = {}
    for p in face.data.polygons:
        for v in p.vertices:
            key = tuple(round(c * 1e6) for c in face.data.vertices[v].co)
            mats_at.setdefault(key, set()).add(p.material_index)
    ring = [face.matrix_world @ v.co for v in face.data.vertices
            if {si_skin, si_mouth} <= mats_at[tuple(round(c * 1e6) for c in v.co)]]
    ring = [p for p in ring if p.y > pron.y - 0.03]
    for s, pts in side_split(ring).items():
        L[f"mouth_corner_{s}"] = lm(max(pts, key=lambda p: abs(p.x)), "MEASURED",
                                    "max |x| of skin/mouth-interior junction ring (lip seam)", ["front"])
    stom = [p for p in ring if abs(p.x - mid_x) < 0.003]
    L["stomion"] = lm(centroid(stom), "MEASURED", "centre of lip-seam ring points with |x|<3 mm", ["front", "side"])

    # --- widths: cheek, temple, alar, ears, neck --------------------------------
    front_skin = [p for p in skin if p.y > 0.0]
    band = [p for p in front_skin if pron.z <= p.z <= eye_bottom_z]
    for s, pts in side_split(band).items():
        L[f"cheek_{s}"] = lm(max(pts, key=lambda p: abs(p.x)), "MEASURED_IN_DEFINED_ROI",
                             "max |x| of skin with y>0 between nose-tip z and eye-bottom z", ["front"])
    band = [p for p in front_skin if eye_line_z <= p.z <= brow_top_z]
    for s, pts in side_split(band).items():
        L[f"temple_{s}"] = lm(max(pts, key=lambda p: abs(p.x)), "MEASURED_IN_DEFINED_ROI",
                              "max |x| of skin with y>0 between eye-line z and brow-top z", ["front"])
    band = [p for p in face_skin if abs(p.z - pron.z) < 0.006 and p.y > pron.y - 0.01]
    for s, pts in side_split(band).items():
        L[f"alar_{s}"] = lm(max(pts, key=lambda p: abs(p.x)), "ESTIMATED",
                            "VRoid nose has no modelled ala; max |x| within 6 mm of nose-tip z and 10 mm of its y", ["front"])
    half_w = max(abs(p.x) for p in skin if men.z < p.z < brow_top_z)
    ear_pts = [p for p in skin if abs(p.x) > 0.85 * half_w and p.y < head_joint.y + 0.015 and men.z < p.z < brow_top_z]
    for s, pts in side_split(ear_pts).items():
        c = centroid(pts)
        L[f"ear_center_{s}"] = lm(c, "MEASURED_IN_DEFINED_ROI",
                                  "centroid of skin with |x|>0.85*max head half-width behind the head joint", ["side", "front"])
        L[f"ear_top_{s}"] = lm(max(pts, key=lambda p: p.z), "MEASURED_IN_DEFINED_ROI", "ear ROI max z", ["side"])
        L[f"ear_bottom_{s}"] = lm(min(pts, key=lambda p: p.z), "MEASURED_IN_DEFINED_ROI", "ear ROI min z", ["side"])
    ring_n = [p for p in skin_vertices() if abs(p.z - neck_joint.z) < 0.003 and abs(p.x) < 0.2]
    L["neck_joint"] = lm(neck_joint, "MEASURED", "J_Bip_C_Neck head joint (rig)", ["front", "side", "back"])
    neck_section = {"z": round(neck_joint.z, 5),
                    "half_width_x": round(max(abs(p.x) for p in ring_n), 5),
                    "front_y": round(max(p.y for p in ring_n), 5), "back_y": round(min(p.y for p in ring_n), 5)}

    # --- exact plane-slice profiles of the Face skin (ears excluded) -----------
    tri = face_skin_triangles(face)
    ear_lo = min(L["ear_bottom_R"]["position"][2], L["ear_bottom_L"]["position"][2])
    ear_hi = max(L["ear_top_R"]["position"][2], L["ear_top_L"]["position"][2])
    ear_y = head_joint.y + 0.015
    ear_x = 0.85 * half_w
    width, side = [], []
    for z in np.arange(round(men.z, 3), round(brow_top_z + 0.0005, 3), 0.001):
        pts = slice_plane(tri, 2, z)
        if not len(pts):
            continue
        in_ear = (np.abs(pts[:, 0]) > ear_x) & (pts[:, 1] < ear_y) & (ear_lo <= z) & (z <= ear_hi)
        q = pts[~in_ear]
        if len(q):
            width.append([round(float(z), 4), round(float(np.abs(q[:, 0] - MID_X).max()), 5)])
    centre = slice_plane(tri, 0, MID_X)
    low = centre[(centre[:, 2] >= men.z) & (centre[:, 2] <= men.z + CHIN_BAND_M) & (centre[:, 1] > nas.y - 0.03)]
    cp = low[np.argmax(low[:, 1])]
    L["chin_profile"] = lm(Vector(cp), "MEASURED",
                           "side-view chin: front-most centre-slice point within %.4f m above menton "
                           "(mirrors the 2D rule: front-most pixel of the lowest 3 face rows)" % CHIN_BAND_M, ["side"])
    for z in np.arange(round(men.z - 0.01, 3), round(top.z, 3), 0.001):
        pts = centre
        seg = pts[np.abs(pts[:, 2] - z) < 0.0006] if len(pts) else pts
        if len(seg):
            side.append([round(float(z), 4), round(float(seg[:, 1].max()), 5)])

    # --- symmetry record (G1: do not mirror canonical asymmetry onto this base) --
    pairs = [k[:-2] for k in L if k.endswith("_R") and k[:-2] + "_L" in L]
    sym = {k: round(abs(L[k + "_R"]["position"][0] + L[k + "_L"]["position"][0] - 2 * MID_X), 5) for k in pairs}

    eye_chin = eye_line_z - men.z
    report = {
        "task_id": "MORWEN-HEAD-LANDMARK-02",
        "source_vrm_sha256": sha(SRC), "source_modified": False,
        "measured_scene": "in-memory import of the pinned VRM (or in-memory candidate when called by fit_head_rbf.py)",
        "blender_version": bpy.app.version_string, "python": sys.version.split()[0],
        "seed": SEED, "alpha_min": ALPHA_MIN, "texel_grid": GRID,
        "frame": "Blender world metres; +Y = face forward; +X = character right; +Z up",
        "normalisation": {"unit_U_m": round(eye_chin, 5),
                          "definition": "U = eye-line z (mean pupil z) - menton z",
                          "eye_line_z": round(eye_line_z, 5), "mid_pupil_x": round(
                              (L["pupil_R"]["position"][0] + L["pupil_L"]["position"][0]) / 2, 5)},
        "landmarks": L,
        "neck_section": neck_section,
        "rig": {"head_joint": r(head_joint), "neck_joint": r(neck_joint)},
        "profiles": {"front_half_width_by_z": width, "front_half_width_rule": "Face skin plane-slice at each z (1 mm), max |x - MID_X| excluding the ear ROI",
                     "centre_profile_front_y_by_z": side, "centre_profile_rule": "Face skin slice at x = MID_X, max y within 0.6 mm of z"},
        "mirror_deviation_abs_x_m": sym,
    }
    return report


def main():
    load()
    OUT.mkdir(parents=True, exist_ok=True)
    report = measure()
    (OUT / "HEAD_LANDMARKS_3D.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    assert sha(SRC) == VRM_SHA256
    print("landmarks:", len(report["landmarks"]), "U =", report["normalisation"]["unit_U_m"])


if __name__ == "__main__":
    main()
