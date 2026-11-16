"""MORWEN 7.5-8 head proportion design from the 2026-11-16 canonical Layer 0 front view.
Usage: python3 morwen_3d_proportion_design.py <canonical_dir> <out_dir>
Reads the canonical PNG read-only. Deterministic (no randomness). Output is a CANDIDATE design aid, not art.
"""
import sys, json, hashlib, os
import numpy as np
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
p = os.path.join(src, "LAYER0_FRONT.png"); im = Image.open(p).convert("RGBA"); a = np.asarray(im); al = a[..., 3] > 96
rows = np.where(al.any(1))[0]; crown, floor = int(rows.min()), int(rows.max()); H = floor - crown
width = al.sum(1)
def runs(y):
    xs = np.where(al[y])[0]
    if len(xs) == 0: return []
    cut = np.where(np.diff(xs) > 1)[0]; st = np.r_[xs[0], xs[cut + 1]]; en = np.r_[xs[cut], xs[-1]]
    return [(int(s), int(e)) for s, e in zip(st, en) if e - s > 6]
# torso run = widest run; arms are separate runs where they hang free
def torso_w(y):
    r = runs(y); return max((e - s for s, e in r), default=0)
# crotch: first row (scanning down from 40% of stature) where the central body splits into two leg runs
cx = int(np.where(al[crown + H // 2])[0].mean())
crotch = next(y for y in range(crown + int(H * .40), floor) if not al[y, cx - 2:cx + 3].any())
# waist: narrowest torso run between 25% and crotch
band = range(crown + int(H * .27), crotch - int(H * .05)); waist = min(band, key=torso_w)
# skin/sock boundary: mean luminance of opaque pixels drops sharply below the stocking top
lum = np.array([a[y, :, :3][al[y]].mean() if al[y].any() else 0 for y in range(a.shape[0])])
seg = range(crotch + 5, crotch + int(H * .2)); sock_top = int(min(seg, key=lambda y: lum[y + 4] - lum[y - 4]))
# chin: lowest row of bright skin on the midline above the neck = luminance-based; reported as estimate
col = a[:, cx, :3].mean(1); skin = (col > 170) & al[:, cx]
face_rows = np.where(skin[crown:crown + int(H * .3)])[0] + crown
# chin estimate = where central skin column narrows to the neck (min skin width between face and collarbone)
def skinw(y): 
    px = a[y, :, :3].astype(int); m = al[y] & (px[:, 0] > 190) & (px[:, 0] - px[:, 2] > 15) & (abs(np.arange(a.shape[1]) - cx) < 60); return int(m.sum())
sw = [skinw(y) for y in range(a.shape[0])]
neck = min(range(crown + int(H * .15), crown + int(H * .24)), key=lambda y: sw[y])
src_lm = {"crown_hair_top": crown, "waist_narrowest": int(waist), "crotch": int(crotch), "stocking_top": sock_top, "floor": floor}
CHIN_VISUAL = 178   # visual estimate (+-4 px) on the 384x1024 source, checked on the overlay; chin tip is not machine-separable from the neck
head = CHIN_VISUAL - crown
src_heads = H / head
TARGET = 7.75
# Rule: keep every Layer 0 body ratio below the chin; only the head:body ratio changes.
body_src = floor - CHIN_VISUAL
def tgt(y):   # landmark height above floor, in head units of the target figure
    return round((floor - y) / body_src * (TARGET - 1), 3)
target = {k: tgt(v) for k, v in src_lm.items() if k not in ("crown_hair_top",)}
target.update(chin=TARGET - 1, crown_hair_top=TARGET)
rep = {"schema": "TWO_MORWEN_3D_PROPORTION_DESIGN_V1", "status": "CANDIDATE_DESIGN_AID / NOT_ART / NOT_APPROVED",
       "source": "LAYER0_FRONT.png", "source_sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(),
       "source_px": {**src_lm, "chin_visual_estimate": CHIN_VISUAL, "chin_uncertainty_px": 4},
       "source_heads_incl_hair": round(src_heads, 2),
       "source_heads_range": [round(H / (head + 4), 2), round(H / (head - 4), 2)],
       "target_heads": TARGET, "target_range": [7.5, 8.0],
       "rule": "Preserve all Layer 0 body ratios below the chin; scale the head (crown-to-chin, hair included) to 1/7.75 of stature.",
       "head_scale_relative_to_body": round((H / TARGET) / head * body_src / (H - H / TARGET), 3),
       "target_landmarks_height_in_heads_from_floor": dict(sorted(target.items(), key=lambda kv: -kv[1])),
       "leg_length_crotch_to_floor_over_stature": {"source": round((floor - crotch) / H, 3), "target": round(target["crotch"] / TARGET, 3)},
       "garter": {"leg": "anatomical right", "front_view": "screen-left", "back_view": "screen-right", "facing_right_profile": "visible", "facing_left_profile": "hidden behind left leg"},
       "not_measured": ["shoulder line", "bust", "knee", "ankle", "elbow", "wrist: need artist-placed landmarks; not guessed"],
       "stature_cm": None, "stature_note": "163 cm appears only in an older unverified registry note; not adopted here."}
json.dump(rep, open(os.path.join(out, "MORWEN_3D_PROPORTION_DESIGN.json"), "w"), indent=1, ensure_ascii=False)
# diagram: source with landmark lines | target ladder at the same stature
W = 1100; S = Image.new("RGB", (W, 1100), (38, 38, 46)); d = ImageDraw.Draw(S)
bg = Image.new("RGBA", im.size, (70, 70, 78, 255)); bg.alpha_composite(im); S.paste(bg.convert("RGB"), (40, 50))
d.text((40, 20), "SOURCE Layer 0 front (canonical 2026-11-16) - %.2f heads incl. hair" % src_heads, fill=(235, 235, 235))
for k, y in {**src_lm, "chin (visual est.)": CHIN_VISUAL}.items():
    d.line((40, 50 + y, 424, 50 + y), fill=(255, 210, 90), width=1); d.text((430, 44 + y), k, fill=(255, 210, 90))
x0 = 680; top, bot = 50 + crown, 50 + floor; unit = (bot - top) / TARGET
d.text((x0 - 60, 20), "TARGET ladder %.2f heads (same stature) - CANDIDATE" % TARGET, fill=(235, 235, 235))
for i in range(int(TARGET) + 1):
    y = top + i * unit; d.line((x0, y, x0 + 160, y), fill=(120, 120, 135), width=1); d.text((x0 - 26, y - 6), str(i), fill=(160, 160, 175))
d.line((x0, bot, x0 + 160, bot), fill=(120, 120, 135)); d.rectangle((x0 + 40, top, x0 + 120, top + unit), outline=(190, 150, 255), width=2)
for k, hgt in target.items():
    y = bot - hgt * unit; d.line((x0, y, x0 + 300, y), fill=(120, 230, 170), width=1); d.text((x0 + 170, y - 12), "%s  %.2f" % (k, hgt), fill=(120, 230, 170))
S.save(os.path.join(out, "MORWEN_3D_PROPORTION_DESIGN.png")); print(json.dumps(rep, indent=1, ensure_ascii=False))
