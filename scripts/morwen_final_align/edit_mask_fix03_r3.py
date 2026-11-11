"""MORWEN FIX-03 edit mask R3 (C3/C4/C5/C8 repaired with traced contours instead of straight cuts).
Input: fix01/morwen_back_fix01.png. Output: fix03/EDIT_MASK_FIX03.png (+ layers.json, preview, derived revealed areas).
Layer priority (top first): hat_move, hair_redraw, strap_reroute, cuff_hand_move, bag_protect, slit_protect, capelet_move, band_redraw."""
import json
import numpy as np
from PIL import Image, ImageDraw
from skimage import color
from scipy import ndimage as ndi

B = "assets/candidates/morwen/real-canon-final-04/"; F = B + "fix03/"
a = np.asarray(Image.open(B + "fix01/morwen_back_fix01.png")).astype(float); al = a[..., 3] > 0
lab = color.rgb2lab(a[..., :3] / 255); L = lab[..., 0]; C = np.hypot(lab[..., 1], lab[..., 2]); h = np.degrees(np.arctan2(lab[..., 2], lab[..., 1]))
H, W = al.shape; yy, xx = np.mgrid[0:H, 0:W]
def poly(pts):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=1); return np.asarray(m).astype(bool)
def band(pts, w):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).line(pts, fill=1, width=w, joint="curve"); return np.asarray(m).astype(bool)
def flood(region, seeds):
    lb, _ = ndi.label(region); ids = {lb[y, x] for y, x in seeds if lb[y, x] > 0}
    return ndi.binary_fill_holes(np.isin(lb, list(ids)))
gold = (h > 40) & (h < 110) & (L > 45)
gold_rim = (h > 55) & (h < 100) & (L > 55) & (C > 25)

# --- hat (move only): above the traced brim rim; includes ribbon and the tip crystal
rib = al & (xx >= 690) & (xx <= 790) & (yy >= 230) & (yy <= 500) & (C > 30) & (L > 30) & (h < -15) & (h > -90)
rib = ndi.binary_fill_holes(ndi.binary_closing(rib, iterations=3)) & al
brim = np.full(W, np.nan)
for x in range(W):
    g = np.nonzero(gold_rim[200:385, x])[0]
    if len(g): brim[x] = g.max() + 200
bs = np.array([np.nanmax(brim[max(0, x - 6):x + 7]) if np.isfinite(brim[max(0, x - 6):x + 7]).any() else 330.0 for x in range(W)])
below_brim = yy > bs[None, :]
hat = (al & ~below_brim & (yy < 400)) | rib | (al & (yy < 400) & (xx >= 745))

# --- C3: hair lower edge traced by eye on a 4x zoom (strand tips + the dark gaps between them belong to hair);
#         the capelet collar starts directly below this curve (no straight row cut)
HAIR_EDGE = [(400, 428), (430, 423), (470, 426), (520, 424), (560, 423), (600, 426), (640, 423), (680, 421), (720, 423), (745, 426)]
hb = np.full(W, np.nan)
xs_, ys_ = zip(*HAIR_EDGE)
hb[400:746] = np.interp(np.arange(400, 746), xs_, ys_)
hair = al & below_brim & ~rib & ~hat & (xx >= 400) & (xx <= 745) & (yy <= np.nan_to_num(hb, nan=-1)[None, :])
hair &= ~(gold & (yy >= 430))

# --- strap (one piece along the strap line, leather only)
strap = al & band([(505, 425), (560, 520), (622, 645), (668, 700)], 30) & (h > -10) & (h < 70) & (L < 62) & (C > 6) & ~gold_rim
strap = ndi.binary_closing(strap, iterations=2) & al & band([(505, 425), (560, 520), (622, 645), (668, 700)], 30)
lb, n = ndi.label(strap); sz = np.bincount(lb.ravel()); sz[0] = 0; strap = lb == sz.argmax()

# --- bag (protect): leather/gold in the bag box, minus the robe embroidery behind the handle
bagbox = poly([(648, 668), (805, 668), (805, 850), (648, 850)])
bag = al & bagbox & (((h > -10) & (h < 70) & (L < 62) & (C > 6) & ~gold_rim) | (gold_rim & (xx > 655) & (yy > 690)))
bag = ndi.binary_fill_holes(ndi.binary_closing(bag, iterations=4)) & al & bagbox
lb, n = ndi.label(bag); sz = np.bincount(lb.ravel()); sz[0] = 0; bag = lb == sz.argmax()
bag &= ~((xx >= 735) & (xx <= 762) & (yy >= 668) & (yy <= 700))

# --- C5: cuffs + frills + hands only (flood fill bounded by the dark outline, robe excluded by traced edge polygons)
PL = poly([(328, 714), (350, 702), (386, 704), (322, 856), (296, 850), (292, 800), (310, 760), (320, 725)])
PR = poly([(814, 704), (850, 702), (872, 714), (880, 725), (892, 760), (908, 800), (905, 850), (880, 860), (878, 856)])
barrier = (L < 15) | ~al
cuff = np.zeros_like(al)
for P, S in ((PL, [(815, 310), (768, 330), (725, 350), (745, 360), (733, 343), (712, 360), (738, 355), (725, 368), (750, 372), (730, 375), (742, 365)]),
             (PR, [(800, 880), (765, 860), (722, 835), (745, 855), (733, 858), (712, 840), (740, 830), (725, 845), (728, 825), (735, 822), (745, 838)])):
    reg = flood(P & ~barrier, S)
    cuff |= ndi.binary_dilation(reg, iterations=2) & al & P

# --- C8: slit = skirt/legs between the two gold-trimmed robe edges (flood fill bounded by the trims), apex clipped
PS = poly([(594, 628), (608, 628), (662, 790), (542, 790)])
slit = flood(PS & al & ~ndi.binary_dilation(gold, iterations=1) & (L < 55), [(720, 600), (770, 600), (700, 598), (760, 620), (760, 580)]) & PS & (yy >= 648)

# --- C4: capelet tier-1 lower edge traced along its gold hem (per column lowest gold-rim pixel in rows 540-615)
hem = np.full(W, np.nan)
for x in range(370, 830):
    g = np.nonzero(gold_rim[540:615, x])[0]
    if len(g): hem[x] = g.max() + 540 + 2
hem_s = np.array([np.nanmedian(hem[max(0, x - 4):x + 5]) if np.isfinite(hem[max(0, x - 4):x + 5]).any() else np.nan for x in range(W)])
ok = np.isfinite(hem_s); xs_ok = np.nonzero(ok)[0]
gap = (~ok) & (np.arange(W) > xs_ok.min()) & (np.arange(W) < xs_ok.max())   # e.g. where the strap crosses the hem
hem_s[gap] = np.interp(np.nonzero(gap)[0], xs_ok, hem_s[ok])
cap_top = np.where(np.isfinite(hb), hb, 0)
cap = al & (yy > cap_top[None, :]) & (yy <= np.nan_to_num(hem_s, nan=-1)[None, :]) & (yy >= 380) & ~hat & ~hair & ~strap
cap = ndi.binary_fill_holes(cap) & al & ~hat & ~hair & ~strap & (yy <= np.nan_to_num(hem_s, nan=-1)[None, :])

redraw = al & (yy < 790) & ~hat & ~hair & ~strap & ~cuff & ~bag & ~slit & ~cap & (yy >= 380)

layers = {"hat_move": hat, "hair_redraw": hair, "strap_reroute": strap, "cuff_hand_move": cuff, "bag_protect": bag,
          "slit_protect": slit, "capelet_move": cap, "band_redraw": redraw}
cols = {"hat_move": (255, 230, 0), "hair_redraw": (255, 0, 255), "strap_reroute": (150, 75, 0), "cuff_hand_move": (255, 255, 255),
        "bag_protect": (0, 200, 0), "slit_protect": (0, 90, 255), "capelet_move": (255, 140, 0), "band_redraw": (0, 200, 255)}
lab_img = np.zeros((H, W), np.uint8); rgba = np.zeros((H, W, 4), np.uint8)
for i, k in enumerate(layers, 1):
    m = layers[k] & (lab_img == 0); lab_img[m] = i; rgba[m] = cols[k] + (255,)
unassigned = al & (yy < 790) & (lab_img == 0)
Image.fromarray(rgba, "RGBA").save(F + "EDIT_MASK_FIX03.png", optimize=True)
base = Image.open(B + "fix01/morwen_back_fix01.png"); bg = Image.new("RGBA", base.size, (255, 255, 255, 255)); bg.alpha_composite(base)
ov = rgba.copy(); ov[..., 3] = (ov[..., 3] * 0.5).astype(np.uint8); bg.alpha_composite(Image.fromarray(ov, "RGBA"))
r = np.zeros((H, W, 4), np.uint8); r[unassigned] = (255, 0, 0, 255); bg.alpha_composite(Image.fromarray(r, "RGBA"))
bg.crop((150, 0, 1050, 900)).convert("RGB").save(F + "EDIT_MASK_FIX03_preview.png", optimize=True)
# derived revealed areas (computed from the final layers)
def shift_up(m, d): s = np.zeros_like(m); s[:-d] = m[d:]; return s
capm = lab_img == 7; hatm = lab_img == 1
vacated = capm & ~shift_up(capm, 48)
under_brim = hatm & ~shift_up(hatm, 16)
rib_rev = rib & (yy >= 430) & ~vacated & ~under_brim
cuffm = lab_img == 4
cuff_new = np.zeros_like(cuffm); cuff_new[:-9, 11:] |= cuffm[9:, :-11] & (xx[9:, :-11] < 600); cuff_new[:-9, :-11] |= cuffm[9:, 11:] & (xx[9:, 11:] >= 600)
cuff_uncovered = cuffm & ~cuff_new
cuff_over_790 = cuff_new & (yy >= 790) & ~cuffm
d = np.zeros((H, W, 4), np.uint8)
d[vacated] = (255, 0, 0, 255); d[under_brim & ~vacated] = (0, 0, 255, 255); d[rib_rev] = (0, 160, 0, 255); d[cuff_uncovered] = (255, 160, 0, 255)
Image.fromarray(d, "RGBA").save(F + "EDIT_MASK_FIX03_derived_revealed.png", optimize=True)
lb, nstrap = ndi.label(lab_img == 3)
holes = int((ndi.binary_fill_holes(capm) & ~capm & (lab_img != 3)).sum())
px = {k: int((lab_img == i).sum()) for i, k in enumerate(layers, 1)}
out = {"revision": "R3", "order_top_to_bottom": list(layers), "colours": {k: list(v) for k, v in cols.items()}, "px": px,
       "checks": {"unassigned_subject_px_above_790": int(unassigned.sum()), "strap_components": int(nstrap),
                  "capelet_holes_not_strap": holes, "emblem_gold_in_hair": int(((lab_img == 2) & gold & (yy >= 430)).sum()),
                  "capelet_top_cut": "traced: hair tip curve %s (no straight row cut); capelet collar and emblem star are in capelet_move" % HAIR_EDGE,
                  "capelet_bottom_cut": "traced: per-column lowest gold-rim pixel of the tier-1 hem in rows 540-615 (+2 px), median-smoothed, interpolated where the strap crosses the hem",
                  "cuff_hand": "flood-filled cuff/frill/hand bounded by the dark outline; robe excluded by polygons traced along the robe edge",
                  "slit": "flood-filled skirt/legs between the two gold-trimmed robe edges, rows 648-789"},
       "y790_exception": {"rule": "only the exact alpha of the moved cuff/hand pixels may change below row 790 (move ~11 px inward, ~9 px up)",
                          "moved_px_landing_below_790": int(cuff_over_790.sum()), "uncovered_px_to_repaint": int(cuff_uncovered.sum()),
                          "note": "uncovered pixels (orange in the derived file) are repainted as robe/background; other lower-body pixels stay protected"},
       "derived_revealed": {"file": "EDIT_MASK_FIX03_derived_revealed.png", "red_capelet_vacated": int(vacated.sum()),
                            "blue_under_raised_brim": int((under_brim & ~vacated).sum()), "green_under_ribbon": int(rib_rev.sum()),
                            "orange_uncovered_by_cuff_move": int(cuff_uncovered.sum())},
       "rules": {"hat_move": "move only, up 14-20 px", "hair_redraw": "redraw; tips ~370-380; width redesigned per director (natural back-of-head width, final width by QA/director)",
                 "strap_reroute": "re-route from raised shoulder to bag ring; buckle shape protected", "cuff_hand_move": "move only (initial target wrists (356,786)/(844,786), fine-tune allowed and recorded)",
                 "bag_protect": "no change", "slit_protect": "no change", "capelet_move": "move only, up ~48 px; emblem/star/gold patterns protected",
                 "band_redraw": "redraw (tier 2, upper arms, sleeves, robe upper part, collar); robe edges overlap sleeves naturally",
                 "layer_priority_at_boundaries": "hat > hair > strap > cuff/hand > bag > slit > capelet > band"}}
json.dump(out, open(F + "EDIT_MASK_FIX03_layers.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out["px"])); print(json.dumps(out["checks"])); print(json.dumps(out["y790_exception"])); print(json.dumps(out["derived_revealed"]))
