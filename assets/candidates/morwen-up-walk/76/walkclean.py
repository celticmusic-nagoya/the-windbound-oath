"""1-px island clean-up shared by the 4-direction walks (same rule as ART-74G): an opaque pixel whose four opaque
neighbours all differ from it and agree among themselves (>= 3) takes that neighbour colour. Silhouette edge pixels and
the optional protect mask are never changed."""
import numpy as np


def clean_islands_generic(img, protect=None):
    h, w = img.shape[:2]; op = img[:, :, 3] > 0; c = img[:, :, :3]
    out = img.copy(); n = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not op[y, x] or (protect is not None and protect[y, x]): continue
            nbp = ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1))
            if not all(op[p] for p in nbp): continue
            nb = [tuple(c[p]) for p in nbp]; me = tuple(c[y, x])
            if me in nb: continue
            best = max(set(nb), key=nb.count)
            if nb.count(best) >= 3: out[y, x, :3] = best; n += 1
    return out, n


def fill_small_holes(img, max_px=2):
    """enclosed transparent specks (<= max_px, not touching the border) take the most common surrounding colour."""
    import cv2
    t = (img[:, :, 3] == 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(t, connectivity=4)
    out = img.copy(); filled = 0; h, w = t.shape
    for i in range(1, n):
        x, y, bw, bh, area = st[i]
        if area > max_px or x == 0 or y == 0 or x + bw >= w or y + bh >= h: continue
        ys, xs = np.where(lab == i)
        nb = []
        for yy, xx in zip(ys, xs):
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = out[yy + dy, xx + dx]
                if p[3]: nb.append(tuple(p))
        if nb:
            c = max(set(nb), key=nb.count)
            for yy, xx in zip(ys, xs): out[yy, xx] = c
            filled += 1
    return out, filled
