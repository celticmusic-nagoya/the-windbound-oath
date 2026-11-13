"""MORWEN-HEAD-LANDMARK-02: calibrated four-view comparison, 3D head vs Layer 0 references.

Calibration (one scale for the whole sheet, no free fitting):
  s [px/m] = U_px(front) / U_m,  U = eye-line -> chin (menton) vertical distance.
  front : x_px = mid_pupil_px - s*(X - mid_pupil_X)   (character right = +X is image-left)
          y_px = eye_line_px  - s*(Z - eye_line_Z)
  right : x_px = pupil_R_px   + s*(Y - pupil_R_Y)     (face points image-right)
  left  : x_px = pupil_L_px   - s*(Y - pupil_L_Y)
  back  : x_px = hair_mid_px  + s*(X - mid_pupil_X),  y uses the front eye line (same sheet framing)
Anchors are therefore zero-delta by construction; every other landmark delta is a real difference
under this calibration. Deltas involving an ESTIMATED landmark are labelled ESTIMATED.

Renders: the complete Face+Body head with imported (unlit) materials, Cycles CPU, orthographic
camera solved from the same mapping, so render pixels and sheet pixels coincide.
Outputs: LANDMARK_COMPARISON.json, LANDMARK_COMPARE_<view>.png, LANDMARK_COMPARE_SHEET.png
"""
import hashlib
import json
import os
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from PIL import Image, ImageDraw

OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_head_landmark_02"))
SRC = Path(os.environ.get("MORWEN_VRM", "render_output/morwen_vroid_review/Base_Female.vrm"))
MANIFEST = Path(os.environ.get("MORWEN_LAYER0_MANIFEST",
                               "tools/blender/production_mesh_08/layer0_reference_manifest.json"))
VRM_SHA256 = "1995f174f6c8f2211f3c56c9e5fe4f9daf27ee5e648f129479582a259238149b"
CROP = (0, 0, 384, 240)   # head band of the 384x1024 sheets
UPS = 3                   # output upscale
SEED = 20261114
VIEWS = ("front", "right", "back", "left")
CAM_DIR = {"front": (0, 1, 0), "right": (1, 0, 0), "back": (0, -1, 0), "left": (-1, 0, 0)}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Mapping:
    def __init__(self, l3, l2):
        self.L = {k: Vector(v["position"]) for k, v in l3["landmarks"].items()}
        self.st3 = {k: v["status"] for k, v in l3["landmarks"].items()}
        n = l3["normalisation"]
        self.U_m = n["unit_U_m"]
        self.eyeZ = n["eye_line_z"]
        self.midX = n["mid_pupil_x"]
        f = l2["views"]["front"]
        self.s = f["U_px"] / self.U_m
        self.front_eye_y = f["eye_line_y"]
        self.front_mid_x = f["mid_pupil_x"]
        self.v2 = l2["views"]
        b = l2["views"]["back"]["landmarks"]
        self.back_mid_x = (b["hair_max_width_left"]["px"][0] + b["hair_max_width_right"]["px"][0]) / 2

    def eye_y(self, view):
        return self.front_eye_y if view in ("front", "back") else self.v2[view]["eye_line_y"]

    def project(self, view, P):
        s = self.s
        y = self.eye_y(view) - s * (P.z - self.eyeZ)
        if view == "front":
            x = self.front_mid_x - s * (P.x - self.midX)
        elif view == "back":
            x = self.back_mid_x + s * (P.x - self.midX)
        elif view == "right":
            x = self.v2["right"]["landmarks"]["pupil_R"]["px"][0] + s * (P.y - self.L["pupil_R"].y)
        else:
            x = self.v2["left"]["landmarks"]["pupil_L"]["px"][0] - s * (P.y - self.L["pupil_L"].y)
        return x, y

    def unproject_centre(self, view, px, py):
        """World point on the head mid-plane that maps to sheet pixel (px, py)."""
        s = self.s
        z = self.eyeZ - (py - self.eye_y(view)) / s
        if view == "front":
            return Vector((self.midX - (px - self.front_mid_x) / s, 0, z))
        if view == "back":
            return Vector((self.midX + (px - self.back_mid_x) / s, 0, z))
        if view == "right":
            return Vector((0, self.L["pupil_R"].y + (px - self.v2["right"]["landmarks"]["pupil_R"]["px"][0]) / s, z))
        return Vector((0, self.L["pupil_L"].y - (px - self.v2["left"]["landmarks"]["pupil_L"]["px"][0]) / s, z))


def render(mp, reload=True, tag=""):
    """reload=False renders whatever head is in the scene (in-memory candidate)."""
    assert sha(SRC) == VRM_SHA256
    if reload:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(SRC.resolve()))
    sc = bpy.context.scene
    for o in sc.objects:
        if o.users_collection and o.users_collection[0].name == "glTF_not_exported":
            o.hide_render = True
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 8
    sc.cycles.seed = SEED
    if hasattr(sc.cycles, "use_denoising"):
        sc.cycles.use_denoising = False
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    for attr in dir(sc.render):  # no date/time/render-time metadata: byte-reproducible PNGs
        if attr.startswith("use_stamp"):
            setattr(sc.render, attr, False)
    w, h = (CROP[2] - CROP[0]) * UPS, (CROP[3] - CROP[1]) * UPS
    sc.render.resolution_x, sc.render.resolution_y = w, h
    cam = bpy.data.objects.get("CAM") or bpy.data.objects.new("CAM", bpy.data.cameras.new("CAM"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = (CROP[2] - CROP[0]) / mp.s
    cam.data.clip_end = 10
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    sc.camera = cam
    out = {}
    for v in VIEWS:
        cx, cy = (CROP[0] + CROP[2]) / 2, (CROP[1] + CROP[3]) / 2
        c = mp.unproject_centre(v, cx, cy)
        d = Vector(CAM_DIR[v])
        cam.location = c + d * 2.0
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        f = OUT / f"renders{tag}" / f"{v}.png"
        f.parent.mkdir(parents=True, exist_ok=True)
        sc.render.filepath = str(f.resolve())
        bpy.ops.render.render(write_still=True)
        Image.open(f).save(f)  # re-encode without Cycles timing metadata -> byte-reproducible
        out[v] = f
    assert sha(SRC) == VRM_SHA256
    return out


PAIRS = {  # 3D landmark -> 2D landmark per view
    "front": ["pupil_R", "pupil_L", "eye_inner_R", "eye_outer_R", "eye_inner_L", "eye_outer_L",
              "eye_top_R", "eye_bottom_R", "eye_top_L", "eye_bottom_L", "pronasale", "stomion",
              "mouth_corner_R", "mouth_corner_L", "menton", "cheek_R", "cheek_L"],
    "right": ["pupil_R", "eye_outer_R", "pronasale", "stomion", ("chin_profile", "menton"), "ear_center_R", "ear_top_R", "ear_bottom_R"],
    "left": ["pupil_L", "eye_outer_L", "pronasale", "stomion", ("chin_profile", "menton"), "ear_center_L", "ear_top_L", "ear_bottom_L"],
    "back": [],
}
ANCHORS = {"front": {"pupil_R", "pupil_L"}, "right": {"pupil_R"}, "left": {"pupil_L"}, "back": set()}


def compare(mp):
    rows = []
    for v in VIEWS:
        L2 = mp.v2[v]["landmarks"]
        for k in PAIRS[v]:
            k3, k2 = k if isinstance(k, tuple) else (k, k)
            a = L2.get(k2)
            k = k3
            if k not in mp.L or not a or a["px"] is None:
                rows.append({"view": v, "landmark": k, "status": "NOT_MEASURABLE"})
                continue
            x3, y3 = mp.project(v, mp.L[k])
            dx, dy = x3 - a["px"][0], y3 - a["px"][1]
            est = "ESTIMATED" in (a["status"], mp.st3[k])
            if v in ("front",) and k in ANCHORS[v]:
                kind = "ANCHOR_PAIR"   # mean of the two pupils is the anchor; individual residual is real IPD error
            elif k in ANCHORS[v]:
                kind = "ANCHOR"
            else:
                kind = "ESTIMATED" if est else "MEASURED"
            rows.append({"view": v, "landmark": k, "canonical_landmark": k2, "status": kind,
                         "canonical_px": a["px"], "model_px": [round(x3, 2), round(y3, 2)],
                         "delta_px": [round(dx, 2), round(dy, 2)],
                         "delta_U": [round(dx / mp.v2["front"]["U_px"], 4), round(dy / mp.v2["front"]["U_px"], 4)],
                         "delta_mm_at_model_scale": [round(dx / mp.s * 1000, 2), round(-dy / mp.s * 1000, 2)]})
    return rows


def ratios(mp):
    """Scale-free proportions (each divided by U) for front/side, canonical vs model."""
    f = mp.v2["front"]["landmarks"]
    U2 = mp.v2["front"]["U_px"]
    U3 = mp.U_m
    L = mp.L

    def d2(a, b, axis):
        return abs(f[a]["px"][axis] - f[b]["px"][axis]) / U2

    def d3(a, b, axis):
        return abs(L[a][axis] - L[b][axis]) / U3
    spec = [("interpupillary_width", "pupil_R", "pupil_L", 0, 0),
            ("eye_R_width", "eye_inner_R", "eye_outer_R", 0, 0),
            ("eye_L_width", "eye_inner_L", "eye_outer_L", 0, 0),
            ("eye_R_height", "eye_top_R", "eye_bottom_R", 1, 2),
            ("eye_L_height", "eye_top_L", "eye_bottom_L", 1, 2),
            ("inner_canthal_width", "eye_inner_R", "eye_inner_L", 0, 0),
            ("mouth_width", "mouth_corner_R", "mouth_corner_L", 0, 0),
            ("cheek_width_at_nose", "cheek_R", "cheek_L", 0, 0),
            ("eye_to_nose", "pupil_R", "pronasale", 1, 2),
            ("eye_to_mouth", "pupil_R", "stomion", 1, 2),
            ("mouth_to_chin", "stomion", "menton", 1, 2)]
    out = {}
    for name, a, b, ax2, ax3 in spec:
        if f.get(a, {}).get("px") is None or f.get(b, {}).get("px") is None:
            continue
        c, m = d2(a, b, ax2), d3(a, b, ax3)
        est = "ESTIMATED" in (f[a]["status"], f[b]["status"], mp.st3[a], mp.st3[b])
        out[name] = {"canonical_U": round(c, 4), "model_U": round(m, 4), "model_over_canonical": round(m / c, 3),
                     "status": "ESTIMATED" if est else "MEASURED"}
    for v, eye in (("right", "pupil_R"), ("left", "pupil_L")):
        s2 = mp.v2[v]["landmarks"]
        U2v = mp.v2[v]["U_px"]
        for name, k, k3 in (("nose_projection", "pronasale", "pronasale"), ("chin_projection", "menton", "chin_profile"),
                            ("ear_offset", f"ear_center_{eye[-1]}", f"ear_center_{eye[-1]}")):
            if s2.get(k, {}).get("px") is None:
                continue
            sign = 1 if v == "right" else -1
            c = sign * (s2[k]["px"][0] - s2[eye]["px"][0]) / U2v
            m = (L[k3].y - L[eye].y) / U3
            out[f"{v}_{name}"] = {"canonical_U": round(c, 4), "model_U": round(m, 4),
                                  "difference_U": round(m - c, 4), "status": "MEASURED",
                                  "note": "forward offset from pupil along view axis, per U (canonical side U)"}
    return out


def outline_profile(mp):
    """Front face half-width (U units) at fixed depths below the eye line; canonical outline vs model."""
    f = mp.v2["front"]
    rows = {r[0]: r for r in f["face_outline_rows"]}
    res = []
    for t in (0.25, 0.5, 0.75, 0.9):
        y = int(round(f["eye_line_y"] + t * f["U_px"]))
        if y not in rows:
            continue
        _, lx, rx, occ_l, occ_r = rows[y]
        c_r = (f["mid_pupil_x"] - lx) / f["U_px"]
        c_l = (rx - f["mid_pupil_x"]) / f["U_px"]
        z = mp.eyeZ - t * mp.U_m
        w = min(L3_PROFILE, key=lambda p: abs(p[0] - z))[1]
        m_half = w / mp.U_m  # model is mirror-symmetric about x=mid (deviation < 0.02 mm)
        res.append({"depth_below_eye_U": t, "canonical_half_width_R_U": round(c_r, 4),
                    "canonical_half_width_L_U": round(c_l, 4), "model_half_width_U": round(m_half, 4),
                    "hair_adjacent_R": occ_l, "hair_adjacent_L": occ_r,
                    "status": "MEASURED" if not (occ_l or occ_r) else "OCCLUSION_POSSIBLE"})
    return res


L3_PROFILE = []


def draw(mp, renders, rows, tag=""):
    man = json.loads(MANIFEST.read_text())
    tiles = []
    for v in VIEWS:
        meta = next(i for i in man["images"] if i["view"] == v)
        ref_path = MANIFEST.parent / "references" / meta["filename"]
        assert sha(ref_path) == meta["sha256"]
        ref = Image.open(ref_path).convert("RGBA").crop(CROP)
        W, H = ref.width * UPS, ref.height * UPS
        ref = ref.resize((W, H), Image.LANCZOS)
        bg = Image.new("RGBA", (W, H), (232, 232, 228, 255))
        left = bg.copy()
        left.alpha_composite(ref)
        rnd = Image.open(renders[v]).convert("RGBA")
        right = bg.copy()
        right.alpha_composite(rnd)
        ov = bg.copy()
        ov.alpha_composite(ref)
        r2 = rnd.copy()
        r2.putalpha(Image.eval(rnd.getchannel("A"), lambda a: int(a * 0.5)))
        ov.alpha_composite(r2)
        # model silhouette edge on canonical
        a = np.asarray(rnd.getchannel("A")) > 127
        edge = a ^ np.roll(a, 1, 0) | a ^ np.roll(a, 1, 1)
        e = Image.fromarray((edge * 255).astype(np.uint8))
        mag = Image.new("RGBA", (W, H), (230, 0, 160, 255))
        left.paste(mag, (0, 0), e)
        d = ImageDraw.Draw(ov)
        for r in rows:
            if r["view"] != v or "canonical_px" not in r:
                continue
            cx, cy = r["canonical_px"][0] * UPS, r["canonical_px"][1] * UPS
            mx, my = r["model_px"][0] * UPS, r["model_px"][1] * UPS
            col = (0, 170, 60, 255) if r["status"] != "ESTIMATED" else (230, 150, 0, 255)
            d.line([(cx, cy), (mx, my)], fill=(40, 40, 40, 255), width=1)
            d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], outline=col, width=2)
            d.line([(mx - 4, my - 4), (mx + 4, my + 4)], fill=(230, 0, 160, 255), width=2)
            d.line([(mx - 4, my + 4), (mx + 4, my - 4)], fill=(230, 0, 160, 255), width=2)
        for img, label in ((left, f"{v}: Layer0 + model silhouette (magenta)"), (right, f"{v}: model, same calibration"),
                           (ov, f"{v}: overlay 50%  o canonical  x model  (orange = ESTIMATED)")):
            ImageDraw.Draw(img).rectangle([0, 0, W, 16], fill=(255, 255, 255, 200))
            ImageDraw.Draw(img).text((4, 3), label, fill=(0, 0, 0, 255))
        tile = Image.new("RGB", (W * 3, H), (232, 232, 228))
        for i, img in enumerate((left, right, ov)):
            tile.paste(img.convert("RGB"), (i * W, 0))
        p = OUT / f"LANDMARK_COMPARE{tag}_{v}.png"
        tile.save(p)
        tiles.append(tile)
    sheet = Image.new("RGB", (tiles[0].width, sum(t.height for t in tiles)), (232, 232, 228))
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.height
    sheet.save(OUT / f"LANDMARK_COMPARE{tag}_SHEET.png")


def main():
    l3 = json.loads((OUT / "HEAD_LANDMARKS_3D.json").read_text())
    l2 = json.loads((OUT / "CANONICAL_LANDMARKS_2D.json").read_text())
    L3_PROFILE.extend(l3["profiles"]["front_half_width_by_z"])
    mp = Mapping(l3, l2)
    rows = compare(mp)
    renders = render(mp)
    draw(mp, renders, rows)
    res = {"task_id": "MORWEN-HEAD-LANDMARK-02", "source_vrm_sha256": VRM_SHA256, "source_modified": False,
           "blender_version": bpy.app.version_string, "seed": SEED,
           "calibration": {"s_px_per_m": round(mp.s, 3), "U_m": mp.U_m, "U_px_front": mp.v2["front"]["U_px"],
                           "per_view_U_px": {v: mp.v2[v].get("U_px") for v in ("front", "right", "left")},
                           "mapping": __doc__.split("Calibration")[1].split("Renders:")[0].strip()},
           "landmark_deltas": rows, "proportions": ratios(mp), "front_outline": outline_profile(mp),
           "outputs": {p.name: sha(p) for p in sorted(OUT.glob("LANDMARK_COMPARE_*.png"))
                       if not p.name.startswith("LANDMARK_COMPARE_CANDIDATE")}}
    (OUT / "LANDMARK_COMPARISON.json").write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    print("comparison rows:", len(rows))


if __name__ == "__main__":
    main()
