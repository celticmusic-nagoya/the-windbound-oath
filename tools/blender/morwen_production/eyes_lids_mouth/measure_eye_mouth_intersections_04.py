"""MORWEN-EYES-LIDS-MOUTH-04: measure eyelid / eye-card / skin intersections per expression state.

Read-only measurement module (also imported by the candidate builder for before/after).
For each state (neutral, Blink, Blink_L, Blink_R, Joy, Surprised, ...):
  * tri_intersections : skin triangles that geometrically intersect each overlay material
                        (BVH overlap of the deformed meshes), with affected face counts
  * line_penetration  : OPAQUE texels (alpha >= 0.5) of eyeline / eyelash cards BURIED under skin:
                        a ray from the texel toward the front camera (+Y) hits front-facing skin within
                        COVER_RANGE; depth = hit distance x n_y (normal depth below that skin), counted
                        when > 0.1 mm. (Nearest-point signed distance is ill-defined at the open lid
                        rim, so it is not used.)
  * eye_show_through  : eye-surface samples visible from the front camera through closed lids
                        (blink states), occlusion by skin + opaque card texels
All positions are Blender world metres; depths are reported in millimetres.
"""
import math

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ALPHA_MIN = 0.5
GRID = 8
PEN_TOL = 1e-4  # 0.1 mm
COVER_RANGE = 0.003  # 3 mm: cards sit within ~1 mm of the lid


def image_alpha(mat):
    if mat is None or not mat.use_nodes:
        return None
    img = next((n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
    if img is None:
        return None
    w, h = img.size
    return np.asarray(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., 3], w, h


def state_coords(obj, key_name=None, extra=None):
    """World coordinates of obj with one shape key at 1.0 (+ optional {key: value} extras)."""
    me = obj.data
    kb = me.shape_keys.key_blocks if me.shape_keys else None
    co = np.array([v.co[:] for v in (kb[0].data if kb else me.vertices)])
    base = co.copy()
    for name, val in ([(key_name, 1.0)] if key_name else []) + list((extra or {}).items()):
        co = co + val * (np.array([v.co[:] for v in kb[name].data]) - base)
    mw = np.array(obj.matrix_world)
    return (np.hstack([co, np.ones((len(co), 1))]) @ mw.T)[:, :3]


def tris_of(obj, slots):
    me = obj.data
    me.calc_loop_triangles()
    return [(t.vertices[:], t.loops[:], t.material_index, t.polygon_index) for t in me.loop_triangles if t.material_index in slots]


def bvh_from(W, tris):
    return BVHTree.FromPolygons([Vector(p) for p in W], [t[0] for t in tris]) if tris else None


def opaque_samples(obj, W, tris, alpha_by_slot):
    """Opaque texel sample points on the given triangles at coordinates W."""
    uv = obj.data.uv_layers.active.data
    bary = [(i / GRID, j / GRID) for i in range(GRID + 1) for j in range(GRID + 1 - i)]
    pts, src = [], []
    for vs, loops, mi, pi in tris:
        a = alpha_by_slot.get(mi)
        P = [W[v] for v in vs]
        U = [uv[li].uv for li in loops]
        for s, t in bary:
            r = 1 - s - t
            if a is not None:
                arr, w, h = a
                u = U[0] * s + U[1] * t + U[2] * r
                if arr[min(h - 1, max(0, int(u.y * h))), min(w - 1, max(0, int(u.x * w)))] < ALPHA_MIN:
                    continue
            pts.append(P[0] * s + P[1] * t + P[2] * r)
            src.append(pi)
    return np.array(pts), src


class Occluder:
    """Front-camera occlusion (+Y) through a set of triangles; texel alpha decides opacity."""

    def __init__(self, obj, W, tris, alpha_by_slot):
        self.obj, self.W, self.tris, self.alpha = obj, W, tris, alpha_by_slot
        self.bvh = bvh_from(W, tris)
        self.uv = obj.data.uv_layers.active.data

    def blocked(self, p, d=Vector((0, 1, 0))):
        origin = Vector(p) + d * 1e-5
        for _ in range(24):
            hit, _, idx, _ = self.bvh.ray_cast(origin, d)
            if hit is None:
                return False
            vs, loops, mi, _ = self.tris[idx]
            a = self.alpha.get(mi)
            if a is None:
                return True
            arr, w, h = a
            u = barycentric_transform(hit, *(Vector(self.W[v]) for v in vs), *(self.uv[li].uv.to_3d() for li in loops))
            if arr[min(h - 1, max(0, int(u.y * h))), min(w - 1, max(0, int(u.x * w)))] >= ALPHA_MIN:
                return True
            origin = hit + d * 1e-5
        return True


def covered(bvh, p):
    """(depth, normal) if front-facing skin covers point p toward +Y within COVER_RANGE, else None."""
    d = Vector((0, 1, 0))
    hit, nrm, _, dist = bvh.ray_cast(Vector(p) + d * 1e-6, d, COVER_RANGE)
    if hit is None or nrm.y <= 0:
        return None
    return dist * nrm.y, nrm


def measure_state(face, W, slot, eye_points=None):
    """slot: dict name -> material index on `face` (skin, eyeline, eyelash, brow, mouth, eye parts).
    eye_points: optional (n,3) world points of the eye surface at this state (None -> Face eye plates)."""
    alpha = {i: image_alpha(s.material) for i, s in enumerate(face.material_slots)}
    skin_t = tris_of(face, {slot["skin"]})
    skin_bvh = bvh_from(W, skin_t)
    out = {"tri_intersections": {}, "line_penetration": {}}
    for name in ("eyeline", "eyelash", "brow", "eye_white", "iris"):
        if name not in slot:
            continue
        ot = tris_of(face, {slot[name]})
        if not ot:
            continue
        pairs = skin_bvh.overlap(bvh_from(W, ot))
        out["tri_intersections"][name] = {"pairs": len(pairs),
                                          "overlay_faces": len({ot[b][3] for _, b in pairs}),
                                          "skin_faces": len({skin_t[a][3] for a, _ in pairs})}
    for name in ("eyeline", "eyelash"):
        if name not in slot:
            continue
        ot = tris_of(face, {slot[name]})
        pts, src = opaque_samples(face, W, ot, alpha)
        pen = []
        for p in pts:
            c = covered(skin_bvh, p)
            if c is not None and c[0] > PEN_TOL:
                pen.append((c[0], p))
        worst = max(pen, key=lambda x: x[0]) if pen else None
        out["line_penetration"][name] = {
            "opaque_samples": len(pts), "penetrating_samples": len(pen),
            "penetrating_ratio": round(len(pen) / max(1, len(pts)), 4),
            "max_depth_mm": round(worst[0] * 1000, 3) if worst else 0.0,
            "worst_position_m": [round(float(c), 5) for c in worst[1]] if worst else None}
    occ_slots = {slot[k] for k in ("skin", "eyeline", "eyelash", "brow", "mouth") if k in slot}
    occ = Occluder(face, W, tris_of(face, occ_slots), alpha)
    if eye_points is None:
        et = tris_of(face, {slot[k] for k in ("eye_white", "iris") if k in slot})
        eye_points, _ = opaque_samples(face, W, et, alpha)
    vis = [p for p in eye_points if not occ.blocked(p)]
    sides = {"R": [p for p in vis if p[0] > 0.00026], "L": [p for p in vis if p[0] < 0.00026]}
    out["eye_visible_samples"] = {k: len(v) for k, v in sides.items()}
    out["eye_visible_extent_m"] = {k: ([round(float(min(q[0] for q in v)), 5), round(float(max(q[0] for q in v)), 5),
                                        round(float(min(q[2] for q in v)), 5), round(float(max(q[2] for q in v)), 5)]
                                       if v else None) for k, v in sides.items()}
    return out


def face_slots(face):
    keys = {"skin": "Face_00_SKIN", "eyeline": "FaceEyeline", "eyelash": "FaceEyelash", "brow": "FaceBrow",
            "mouth": "FaceMouth", "eye_white": "EyeWhite", "iris": "EyeIris"}
    out = {}
    for k, key in keys.items():
        hits = [i for i, s in enumerate(face.material_slots) if s.material and key in s.material.name]
        if hits:
            out[k] = hits[0]
    return out
