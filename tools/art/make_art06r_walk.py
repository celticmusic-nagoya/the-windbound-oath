#!/usr/bin/env python3
"""DIRECTIVE-ART-06R: soldier walk frames by part-offsetting the ADOPTED front idle (no redraw of the character).

Source (read-only): img/field/moss/props/npc_soldier_idle_v2.png (112x168, display 47.6x71.4 world, feet y=165, centre x=56).
Method: split the idle into  upper body + equipment (incl. spear, shield, cape, tunic hem)  /  image-left leg  /  image-right leg
with fixed masks measured on the idle; legs are drawn BEHIND the upper body, so a raised leg slides under the tunic hem.
  walk_01 (contact, character's right foot = image-left forward): image-left leg stays on the ground line y=165,
           image-right leg is the trailing leg: lifted (heel up, farther away) and slightly darkened.
  walk_04 = the same with the legs swapped.  Upper body, spear and shield are never mirrored.
  Contact frames sink the upper body by 1 px (the idle plume already touches y=0, so the bob only goes down; 1 px keeps the
  spear butt inside the canvas).
Pixels are moved/copied, never repainted; the only new pixels are the vacated area (left transparent = ground).
Output: docs/art/candidates/art-06r/ (candidates only).
"""
import hashlib, json, pathlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

R = pathlib.Path(__file__).resolve().parents[2]
SRC = R / 'img/field/moss/props/npc_soldier_idle_v2.png'
OUT = R / 'docs/art/candidates/art-06r'
W, H = 112, 168
LIFT = 9        # trailing-leg lift in px (≈3.8 world)
SQUASH = .93    # trailing-leg vertical scale (farther from the camera)
DARK = .82      # trailing-leg value (in shade, behind the body)
SINK = 1        # upper-body sink on contact frames


def mask_poly(pts):
    im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).polygon(pts, fill=255); return np.array(im) > 0


# Leg regions measured on the idle (x right, y down). Above y~131 the tunic hem covers the thighs, so legs start there.
# The spear (x 24-32) and the capes (x<34 down to y145 / x>=84 down to y146) are excluded from the leg masks.
LEG_L = mask_poly([(34, 131), (53, 131), (54, 150), (54, 167), (33, 167), (33, 146), (34, 140)])
LEG_R = mask_poly([(60, 129), (82, 129), (83, 146), (92, 146), (92, 167), (60, 167)])


def load():
    return np.array(Image.open(SRC).convert('RGBA'))


def part(a, m):
    p = np.zeros_like(a); p[m] = a[m]; return p


def shift(p, dy):
    o = np.zeros_like(p)
    if dy > 0: o[dy:] = p[:-dy]
    elif dy < 0: o[:dy] = p[-dy:]
    else: o = p.copy()
    return o


def trailing(p):
    """Lift + slight vertical squash (anchored at the leg top) + shade. Nearest-neighbour only, alpha kept."""
    ys, xs = np.nonzero(p[..., 3]); top, bot = ys.min(), ys.max()
    crop = Image.fromarray(p[top:bot + 1])
    nh = max(1, round(crop.height * SQUASH)); crop = crop.resize((crop.width, nh), Image.NEAREST)
    c = np.array(crop).astype(float); c[..., :3] *= DARK; c = c.astype(np.uint8)
    c[c[..., 3] < 64] = 0   # squashing breaks the faint AA rim into loose specks: keep only the leg's solid pixels
    lab, n = ndimage.label(c[..., 3] > 0)   # and no loose fragments: keep only the main body of the leg
    if n > 1:
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)); keep = 1 + int(np.argmax(sizes)); c[(lab != keep) & (lab > 0)] = 0
    o = np.zeros_like(p); y0 = top + (bot + 1 - top - nh) - LIFT   # keep the foot below the hem: bottom rises by LIFT + squash
    o[y0:y0 + nh, :] = c; return o


def over(dst, src):
    a = src[..., 3:4].astype(float) / 255; out = dst.copy().astype(float)
    out[..., :3] = src[..., :3] * a + out[..., :3] * (1 - a); out[..., 3] = np.maximum(dst[..., 3], src[..., 3])
    return out.astype(np.uint8)


def frame(a, forward):
    body = a.copy(); legs = LEG_L | LEG_R; body[legs] = 0
    # faint anti-alias dust (alpha < 64) hugging the legs was hidden behind them in the idle; once a leg moves it would show
    # as grey specks, so it leaves with the legs (only near-transparent pixels within 2 px; nothing opaque is touched)
    near = legs.copy()
    for _ in range(2):
        n = near.copy(); n[1:] |= near[:-1]; n[:-1] |= near[1:]; n[:, 1:] |= near[:, :-1]; n[:, :-1] |= near[:, 1:]; near = n
    body[near & (a[..., 3] < 64)] = 0
    op = body[..., 3] >= 64; nb = np.zeros_like(op)
    nb[1:] |= op[:-1]; nb[:-1] |= op[1:]; nb[:, 1:] |= op[:, :-1]; nb[:, :-1] |= op[:, 1:]
    body[near & (body[..., 3] > 0) & ~nb] = 0   # orphan pixels left where a leg was cut out (no 4-neighbour in the body layer)
    lp, rp = part(a, LEG_L), part(a, LEG_R)
    fwd, back = (lp, rp) if forward == 'L' else (rp, lp)
    canvas = np.zeros_like(a)
    canvas = over(canvas, trailing(back))     # farthest first
    canvas = over(canvas, fwd)                # planted leg on the ground line
    canvas = over(canvas, shift(body, SINK))  # body (tunic hem, capes, spear, shield) in front of the legs
    return canvas, body, lp, rp


def stats(arr):
    al = arr[..., 3]; boot = (al > 200) & (arr[..., 0] > 90) & (arr[..., 1] > 50) & (arr[..., 2] < 70) & (arr[..., 0] > arr[..., 1])
    def foot(x0, x1):
        ys = np.nonzero(boot[:, x0:x1].any(1))[0]; return int(ys.max()) if len(ys) else None
    return dict(alpha_values=sorted({int(v) for v in np.unique(al)} & {0, 255}), semi=int(((al > 0) & (al < 255)).sum()),
                bottom_left_boot=foot(33, 55), bottom_right_boot=foot(60, 93), top_row_alpha=int(al[0].max()), bottom_row_alpha=int(al[-1].max()))


def main():
    OUT.mkdir(parents=True, exist_ok=True); a = load(); info = {}
    f01, body, lp, rp = frame(a, 'L'); f04, *_ = frame(a, 'R')
    for name, arr in (('soldier_walk_01_candidate.png', f01), ('soldier_walk_04_candidate.png', f04)):
        Image.fromarray(arr, 'RGBA').save(OUT / name); info[name] = dict(sha256=hashlib.sha256((OUT / name).read_bytes()).hexdigest(), **stats(arr))
    info['idle'] = dict(sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(), **stats(a))
    # upper body identity check: everything outside the two leg masks must equal the idle shifted by SINK (where not covered)
    sb = shift(np.where((LEG_L | LEG_R)[..., None], 0, a), SINK)   # (dust pixels are alpha<64, so the alpha==255 check below is unaffected)
    for name, arr in (('walk_01', f01), ('walk_04', f04)):
        m = sb[..., 3] == 255
        info[name + '_upper_body_pixels_identical'] = bool((arr[m] == sb[m]).all())
    # parts sheet (visual aid)
    F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 13)
    K = 3; cells = [('上半身・装備（脚を除く）', body), ('画面左の脚（キャラの右脚）', lp), ('画面右の脚（キャラの左脚）', rp)]
    S = Image.new('RGB', (len(cells) * (W * K + 16) + 16, H * K + 40), (20, 24, 22)); d = ImageDraw.Draw(S)
    for i, (t, arr) in enumerate(cells):
        B = Image.new('RGBA', (W, H), (255, 0, 255, 255)); B.alpha_composite(Image.fromarray(arr, 'RGBA')); x = 16 + i * (W * K + 16)
        S.paste(B.resize((W * K, H * K), Image.NEAREST).convert('RGB'), (x, 32)); d.text((x, 8), t, fill=(240, 228, 190), font=F)
    S.save(OUT / 'parts_split_x3.png')
    (OUT / 'qa.json').write_text(json.dumps(dict(method='part offset of the adopted idle', lift_px=LIFT, squash=SQUASH, dark=DARK, sink_px=SINK, **info), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(info, ensure_ascii=False, indent=0)[:1200])


if __name__ == '__main__':
    main()
