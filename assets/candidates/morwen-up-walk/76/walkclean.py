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
