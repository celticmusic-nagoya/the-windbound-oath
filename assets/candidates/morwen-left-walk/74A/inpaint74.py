"""Exemplar (patch-copy) inpainting for pixel art: fills each hole pixel with the centre colour of the best-matching
fully-known 5x5 patch from an allowed source region (existing pixels only; no blending, no new colours)."""
import numpy as np
H, W = 128, 96
def exemplar(img, hole, source, rad=2, win=22):
    out = img.copy().astype(int); known = (img[:, :, 3] > 0) & ~hole
    todo = hole.copy()
    ys, xs = np.where(source & known)
    # candidate centres whose full patch is known and inside the source region
    cand = [(y, x) for y, x in zip(ys, xs) if rad <= y < H - rad and rad <= x < W - rad and (source & known)[y - rad:y + rad + 1, x - rad:x + rad + 1].all()]
    if not cand: return out.astype(np.uint8), todo
    cy = np.array([c[0] for c in cand]); cx = np.array([c[1] for c in cand])
    P = np.stack([out[y - rad:y + rad + 1, x - rad:x + rad + 1, :3] for y, x in cand]).astype(float)   # n,5,5,3
    while todo.any():
        # onion layer: hole pixels with >= 3 known 8-neighbours
        kn = known.astype(int); cnt = np.zeros((H, W), int)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy or dx: cnt += np.roll(np.roll(kn, dy, 0), dx, 1)
        front = todo & (cnt >= 3)
        if not front.any(): front = todo & (cnt >= 1)
        if not front.any(): break
        for y, x in zip(*np.where(front)):
            y0, y1, x0, x1 = y - rad, y + rad + 1, x - rad, x + rad + 1
            if y0 < 0 or x0 < 0 or y1 > H or x1 > W: out[y, x] = out[y, x]; todo[y, x] = False; known[y, x] = True; continue
            mk = known[y0:y1, x0:x1].astype(float)[None, :, :, None]
            pt = out[y0:y1, x0:x1, :3].astype(float)[None]
            near = (np.abs(cy - y) <= win) & (np.abs(cx - x) <= win)
            if not near.any(): near = np.ones_like(cy, bool)
            d = (((P[near] - pt) ** 2) * mk * np.array([0.3, 0.59, 0.11])).sum((1, 2, 3)) + 0.5 * np.hypot(cy[near] - y, cx[near] - x)
            i = int(np.argmin(d)); qy, qx = cy[near][i], cx[near][i]
            out[y, x, :3] = out[qy, qx, :3]; out[y, x, 3] = 255
            known[y, x] = True; todo[y, x] = False
    return out.astype(np.uint8), todo
def drop_islands(img, keep_mask_size=8):
    from collections import deque
    op = img[:, :, 3] > 0; seen = np.zeros_like(op); comps = []
    for y0, x0 in zip(*np.where(op)):
        if seen[y0, x0]: continue
        q = deque([(y0, x0)]); seen[y0, x0] = True; comp = []
        while q:
            y, x = q.popleft(); comp.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and op[yy, xx] and not seen[yy, xx]: seen[yy, xx] = True; q.append((yy, xx))
        comps.append(comp)
    comps.sort(key=len, reverse=True); n = 0
    for c in comps[1:]:
        for y, x in c: img[y, x] = 0; n += 1
    return n
