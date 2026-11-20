"""UV QA helpers for C11 repair islands (pure numpy; importable inside Blender).

overlap_pairs: interior-overlapping triangle pairs in UV (2D SAT); triangles that
share a vertex are skipped only if their only contact is that shared vertex/edge
(handled by the strict penetration tolerance).
"""
import numpy as np


def signed_area(t):
    a, b, c = t
    return 0.5 * ((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))


def _proj(tri, ax):
    p = tri @ ax
    return p.min(), p.max()


def tri_overlap(t1, t2, tol):
    """True if the open interiors overlap by more than tol along every axis."""
    for tri in (t1, t2):
        for i in range(3):
            e = tri[(i + 1) % 3] - tri[i]
            ax = np.array([-e[1], e[0]])
            n = np.hypot(*ax)
            if n == 0:
                return False
            ax = ax / n
            a0, a1 = _proj(t1, ax)
            b0, b1 = _proj(t2, ax)
            if min(a1, b1) - max(a0, b0) <= tol:
                return False
    return True


def overlap_pairs(tris_uv, test_mask=None, tol=1e-7, cell=None):
    """tris_uv: (n,3,2). Counts pairs (i<j) with interior overlap where at least one
    of the two is in test_mask (default: all)."""
    n = len(tris_uv)
    if n == 0:
        return 0, []
    if test_mask is None:
        test_mask = np.ones(n, bool)
    lo = tris_uv.min(1)
    hi = tris_uv.max(1)
    if cell is None:
        cell = max(float(np.median(hi - lo)) * 2.0, 1e-6)
    grid = {}
    for i in range(n):
        for gx in range(int(lo[i, 0] // cell), int(hi[i, 0] // cell) + 1):
            for gy in range(int(lo[i, 1] // cell), int(hi[i, 1] // cell) + 1):
                grid.setdefault((gx, gy), []).append(i)
    seen = set()
    found = []
    for ids in grid.values():
        for a in range(len(ids)):
            i = ids[a]
            for b in range(a + 1, len(ids)):
                j = ids[b]
                if not (test_mask[i] or test_mask[j]):
                    continue
                k = (i, j) if i < j else (j, i)
                if k in seen:
                    continue
                seen.add(k)
                if (lo[i] > hi[j]).any() or (lo[j] > hi[i]).any():
                    continue
                if tri_overlap(tris_uv[i], tris_uv[j], tol):
                    found.append(k)
    return len(found), found


def jacobian_sv(tri3, triuv):
    """Singular values of the 3D-triangle -> UV affine map."""
    p0, p1, p2 = tri3
    e1, e2 = p1 - p0, p2 - p0
    x = e1 / (np.linalg.norm(e1) + 1e-30)
    nrm = np.cross(e1, e2)
    y = np.cross(nrm, x)
    y /= np.linalg.norm(y) + 1e-30
    A = np.array([[e1 @ x, e2 @ x], [e1 @ y, e2 @ y]])
    B = np.array([triuv[1] - triuv[0], triuv[2] - triuv[0]]).T
    if abs(np.linalg.det(A)) < 1e-14:
        return np.array([0.0, 0.0])
    J = B @ np.linalg.inv(A)
    return np.linalg.svd(J, compute_uv=False)


def island_uv_report(new3, newuv, ring3, ringuv, tol=1e-7):
    """new*/ring*: (n,3,3) and (n,3,2) for repair faces and the untouched faces
    touching the repair perimeter. Orientation reference = ring majority sign of
    (uv signed area) relative to 3D facing (all faces share winding)."""
    def sgn(uv):
        return np.sign([signed_area(t) for t in uv])
    s_ring = sgn(ringuv) if len(ringuv) else np.array([1.0])
    ref = 1.0 if (s_ring >= 0).sum() >= (s_ring < 0).sum() else -1.0
    s_new = sgn(newuv)
    area_uv = np.abs([signed_area(t) for t in newuv])
    zero = int((area_uv <= 1e-12).sum())
    flipped = int(((s_new != ref) & (area_uv > 1e-12)).sum())
    all_uv = np.concatenate([newuv, ringuv]) if len(ringuv) else newuv
    mask = np.zeros(len(all_uv), bool)
    mask[:len(newuv)] = True
    n_ov, pairs = overlap_pairs(all_uv, mask, tol)
    n_internal = sum(1 for i, j in pairs if i < len(newuv) and j < len(newuv))
    sv_new = np.array([jacobian_sv(a, b) for a, b in zip(new3, newuv)])
    sv_ring = np.array([jacobian_sv(a, b) for a, b in zip(ring3, ringuv)]) if len(ring3) else sv_new
    def stats(sv):
        sc = np.sqrt(np.maximum(sv[:, 0] * sv[:, 1], 0))
        an = sv[:, 0] / np.maximum(sv[:, 1], 1e-12)
        return sc, an
    sc_n, an_n = stats(sv_new)
    sc_r, an_r = stats(sv_ring)
    med_r = float(np.median(sc_r)) or 1.0
    return {
        "faces": len(newuv), "ring_faces": len(ringuv),
        "zero_area_uv": zero, "flipped_uv": flipped, "overlap_pairs": n_ov, "overlap_pairs_repair_internal": n_internal,
        "overlap_pairs_repair_vs_ring": n_ov - n_internal,
        "texel_scale_ratio_median": round(float(np.median(sc_n) / med_r), 4),
        "texel_scale_ratio_p5_p95": [round(float(np.percentile(sc_n, 5) / med_r), 4),
                                     round(float(np.percentile(sc_n, 95) / med_r), 4)],
        "anisotropy_median": round(float(np.median(an_n)), 4),
        "anisotropy_p95": round(float(np.percentile(an_n, 95)), 4),
        "ring_anisotropy_median": round(float(np.median(an_r)), 4),
        "ring_anisotropy_p95": round(float(np.percentile(an_r, 95)), 4),
    }
