"""HD pixel re-draw for the front / back field walks (MORWEN-WALK-4DIR-ART-FIX-02).

Not a downscale: the official painting is only used to decide, per sprite pixel, WHICH PART is there (part labels
by colour + position) and roughly how lit it is. Every sprite pixel is then painted from the side walks' own colour
ramps (74G / 75: same purples, gold, skin, hair, leather), with
  - posterised cel shading (3-5 tones per part, smoothed so single pixels do not flicker),
  - a 1-px dark outline on the silhouette and selective inner lines between parts (side-walk line weight),
  - gold trims kept as continuous 1-px lines (a block becomes gold when gold covers >= 22 % of it),
  - a constructed face for the front (bangs, violet eyes with highlight, round gold glasses, mouth),
at the side walks' chibi layout (hat 2-36 / 60 px brim, neck ~52, cape hem ~112, ground 124).
48x64 is drawn the same way on its own grid (not sampled from 96)."""
import numpy as np
from PIL import Image
from oklab import rgb2oklab, lch

CLASSES = ['purple', 'violet', 'gold', 'skin', 'white', 'brown', 'hair']
OUTLINE = (12, 2, 12)


def classify(rgb, alpha, hair_rows=None):
    """per-pixel part label (index into CLASSES, -1 transparent)."""
    h_, w_ = alpha.shape
    L, C, h = (v.reshape(h_, w_) for v in lch(rgb2oklab(rgb.reshape(-1, 3).astype(float))))
    lab = np.full((h_, w_), CLASSES.index('purple'), int)
    gold = (h > 45) & (h < 115) & (C >= 0.075) & (L > 0.36)
    white = (L > 0.86) & (C < 0.045) & ~((h > 20) & (h < 90) & (C > 0.012))
    skin = (h > 20) & (h < 90) & (C > 0.012) & (C < 0.12) & (L > 0.70) & ~gold
    brown = ((h < 80) | (h > 352)) & (C > 0.03) & (C < 0.11) & (L > 0.25) & (L <= 0.70) & ~gold
    violet = (C > 0.13) & ((h > 280) & (h < 340))
    hair = (L < 0.42) & (C < 0.075)
    if hair_rows is not None:
        yy = np.mgrid[0:h_, 0:w_][0]; hair &= (yy >= hair_rows[0]) & (yy < hair_rows[1])
    else:
        hair[:] = False
    for name, m in (('violet', violet), ('brown', brown), ('hair', hair), ('skin', skin), ('white', white), ('gold', gold)):
        lab[m] = CLASSES.index(name)
    lab[alpha < 128] = -1
    return lab, L


def side_ramps(paths):
    """colour ramps per part from the side walk frames (actual pixel colours at L quantiles)."""
    px = []
    for p in paths:
        a = np.array(Image.open(p).convert('RGBA')); px.append(a[a[:, :, 3] > 0][:, :3])
    px = np.concatenate(px)
    lab, L = classify(px[None], np.full((1, len(px)), 255), hair_rows=(0, 1))
    lab = lab[0]; L = L[0]
    # hair is position-dependent in sprites: take dark low-chroma pixels as hair
    Lx, Cx, hx = lch(rgb2oklab(px.astype(float)))
    lab[(Lx < 0.40) & (Cx < 0.075) & (lab == CLASSES.index('purple'))] = CLASSES.index('hair')
    n = {'purple': 4, 'violet': 4, 'gold': 3, 'skin': 4, 'white': 3, 'brown': 4, 'hair': 4}
    span = {'purple': (8, 82), 'gold': (20, 90), 'violet': (10, 70)}
    ramps = {}
    for i, c in enumerate(CLASSES):
        m = lab == i
        if c == 'purple': m &= (hx > 280) & (hx < 340) & (Cx > 0.05)        # cloth purples only (no grey-brown shadows)
        if m.sum() < 20: continue
        qs = np.linspace(*span.get(c, (12, 92)), n[c])
        tones = []
        for q in qs:
            t = np.percentile(L[m], q); j = np.argmin(np.abs(L[m] - t)); tones.append(tuple(int(v) for v in px[m][j]))
        ramps[c] = tones
    return ramps


def block_render(src_rgb, src_a, src_lab, src_L, segs, size, cx_src, cx_dst, gold_frac=0.33):
    """segs: list of ((sy0, sy1), (dy0, dy1), s_h). Returns label map (-1 = empty) and lightness map on the grid."""
    W, H = size
    lab = np.full((H, W), -1, int); Lm = np.zeros((H, W))
    gi, si = CLASSES.index('gold'), CLASSES.index('skin')
    for (sy0, sy1), (dy0, dy1), sh in segs:
        rows = dy1 - dy0
        if rows <= 0: continue
        ys = np.linspace(sy0, sy1, rows + 1)
        for r in range(rows):
            y0, y1 = int(ys[r]), max(int(ys[r]) + 1, int(ys[r + 1]))
            for x in range(W):
                xs0 = cx_src + (x - cx_dst) / sh; xs1 = cx_src + (x + 1 - cx_dst) / sh
                x0, x1 = int(max(0, xs0)), int(min(src_a.shape[1], max(xs0 + 1, xs1)))
                if x1 <= x0: continue
                bl = src_lab[y0:y1, x0:x1]; op = bl >= 0
                if op.mean() < 0.5: continue
                v = bl[op]; cnt = np.bincount(v, minlength=len(CLASSES))
                if cnt[gi] >= gold_frac * op.sum(): k = gi
                elif cnt[si] >= 0.40 * op.sum(): k = si
                else: k = int(np.argmax(cnt))
                lab[dy0 + r, x] = k
                Lm[dy0 + r, x] = float(src_L[y0:y1, x0:x1][bl == k].mean())
    return lab, Lm


def mode3(a, valid):
    """3x3 mode filter on small ints (only where valid)."""
    h, w = a.shape; out = a.copy()
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not valid[y, x]: continue
            nb = a[y - 1:y + 2, x - 1:x + 2][valid[y - 1:y + 2, x - 1:x + 2]]
            vals, cnt = np.unique(nb, return_counts=True)
            if cnt.max() >= 5: out[y, x] = vals[np.argmax(cnt)]
    return out


def paint(lab, Lm, ramps, src_L_by_class, inner_lines=True, protect=None):
    """cel-shade every pixel from the side ramps, then outline."""
    H, W = lab.shape
    lab = lab.copy()
    for _ in range(2):            # part labels: 3x3 mode filter (removes 1-px part speckle; silhouette kept)
        gi = CLASSES.index('gold')
        m = (lab >= 0) & (lab != gi)                      # gold trims are never smoothed away or grown
        if protect is not None: m &= ~protect
        f = mode3(np.where(lab >= 0, lab, 99), m); lab[m] = np.where((f[m] == 99) | (f[m] == gi), lab[m], f[m])
    img = np.zeros((H, W, 4), np.uint8)
    tone = np.zeros((H, W), int)
    for i, c in enumerate(CLASSES):
        m = lab == i
        if not m.any() or c not in ramps: continue
        n = len(ramps[c]); qs = src_L_by_class[c]
        edges = np.percentile(qs, np.linspace(0, 100, n + 1)[1:-1]) if len(qs) else np.linspace(0.2, 0.8, n - 1)
        tone[m] = np.digitize(Lm[m], edges)
    # smooth tones inside each part (no 1-px flicker)
    for i in range(len(CLASSES)):
        m = lab == i
        if m.any():
            t = mode3(np.where(m, tone, -9), m); tone[m] = t[m]
    for i, c in enumerate(CLASSES):
        m = lab == i
        if not m.any() or c not in ramps: continue
        r = np.array(ramps[c]); img[m, :3] = r[np.clip(tone[m], 0, len(r) - 1)]; img[m, 3] = 255
    op = lab >= 0
    pad = np.pad(op, 1)
    edge = op & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    img[edge, :3] = OUTLINE
    if inner_lines:   # line between two different non-gold, non-skin parts: the lower / right pixel takes the darkest tone
        noline = {CLASSES.index(c) for c in ('gold', 'skin', 'white')}
        for y in range(1, H):
            for x in range(1, W):
                a, up, lf = lab[y, x], lab[y - 1, x], lab[y, x - 1]
                if a < 0 or edge[y, x] or a in noline: continue
                if (up >= 0 and up != a and up not in noline) or (lf >= 0 and lf != a and lf not in noline):
                    c = CLASSES[a]
                    if c in ramps: img[y, x, :3] = ramps[c][0]
    return img, tone, lab


def class_L(src_lab, src_L):
    return {c: src_L[src_lab == i][::7] for i, c in enumerate(CLASSES)}


def face_front(img, k, ramps, lab=None):
    """constructed front face (96: k=1, 48: k=2): violet eyes with a white catch-light, round gold glasses, mouth.
    Placed on the skin area under the bangs; returns the face box used (for island protection)."""
    H, W = img.shape[:2]
    skin = np.array(ramps['skin']); vio = np.array(ramps['violet']); gold = np.array(ramps['gold'])
    L, C, h = lch(rgb2oklab(img[:, :, :3].reshape(-1, 3).astype(float)))
    L = L.reshape(H, W); C = C.reshape(H, W); h = h.reshape(H, W)
    sk = (lab == CLASSES.index('skin')) if lab is not None else ((img[:, :, 3] > 0) & (h > 25) & (h < 85) & (L > 0.70) & (C < 0.085))
    yy, xx = np.mgrid[0:H, 0:W]
    sk &= (yy < 56 // k) & (abs(xx - W // 2) < 12 // k)
    if sk.sum() < 6 // k: return None
    ys, xs = np.where(sk); top, bot = ys.min(), ys.max(); cxf = int(round(xs.mean()))
    ey = top + max(1, (bot - top) * 2 // 5)
    if k == 1:
        for sx in (-4, 3):       # eye 2x3 (dark top, violet, light) + catch-light
            x0 = cxf + sx
            img[ey, x0:x0 + 2, :3] = vio[0]; img[ey + 1, x0:x0 + 2, :3] = vio[1]; img[ey + 2, x0:x0 + 2, :3] = vio[2]
            img[ey + 1, x0, :3] = (255, 255, 255)
            for gx, gy in ((x0 - 1, ey), (x0 - 1, ey + 1), (x0 - 1, ey + 2), (x0 + 2, ey), (x0 + 2, ey + 1), (x0 + 2, ey + 2),
                           (x0, ey - 1), (x0 + 1, ey - 1), (x0, ey + 3), (x0 + 1, ey + 3)):
                img[gy, gx, :3] = gold[1]; img[gy, gx, 3] = 255
        img[ey + 1, cxf - 1:cxf + 1, :3] = gold[1]                     # glasses bridge
        img[ey + 5, cxf - 1:cxf + 1, :3] = skin[0]                     # mouth
        return (cxf - 7, ey - 2, cxf + 7, ey + 6)
    else:
        for sx in (-2, 1):
            img[ey, cxf + sx, :3] = vio[0]; img[ey + 1, cxf + sx, :3] = vio[1]
        img[ey + 3, cxf - 1 if (bot - top) > 4 else cxf, :3] = skin[0]
        return (cxf - 4, ey - 1, cxf + 3, ey + 3)
