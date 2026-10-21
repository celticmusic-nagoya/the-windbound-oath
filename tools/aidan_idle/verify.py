#!/usr/bin/env python3
"""Aidan idle v1 -- automated verification (numbers only; artwork quality is judged separately by eye).
usage: verify.py MASTER.png OVERLAY_DIR [OUT.json]
"""
import sys, os, json, math, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from idle_motion import Idle, warp, P
from render_preview import composite_eyes, BLINK_SEQ

def main():
    mp, ov = sys.argv[1], sys.argv[2]
    M = np.array(Image.open(mp).convert('RGBA')); boxes = json.load(open(f'{ov}/boxes.json')); R = {}
    # 1. blink: pixel diff vs MASTER outside the two eye boxes must be exactly 0; overlay alpha only inside the box; stage0 == MASTER
    outside = np.ones(M.shape[:2], bool)
    for e, b in boxes.items(): outside[b[1]:b[3], b[0]:b[2]] = False
    worst = 0; closed_ok = True
    for st in (1, 2, 3, 4):
        f = composite_eyes(M, ov, boxes, st)
        worst = max(worst, int(np.abs(f.astype(int) - M.astype(int))[outside].max()))
        assert (f[..., 3] == M[..., 3]).all(), 'alpha channel of the sprite changed by a blink overlay'
    R['blink_nonEye_maxdiff'] = worst; R['blink_alpha_unchanged'] = True
    R['blink_stage0_is_master'] = bool((composite_eyes(M, ov, boxes, 0) == M).all())
    R['blink_diff_pixels_stage4'] = int((np.abs(composite_eyes(M, ov, boxes, 4).astype(int) - M.astype(int)).max(-1) > 0).sum())
    R['blink_total_ms'] = sum(d for _, d in BLINK_SEQ)
    # 2. motion field
    idle = Idle(M[..., 3]); ts = np.arange(0, P, 0.04)
    fields = [idle.field(t) for t in ts]
    maxd = max(float(np.hypot(dx, dy).max()) for dx, dy in fields)
    yy = np.mgrid[0:M.shape[0], 0:M.shape[1]][0]; sole = (yy > 1080) & (M[..., 3] > 200)
    foot = max(float(np.hypot(dx, dy)[sole].max()) for dx, dy in fields)
    R['max_displacement_px_master'] = round(maxd, 2); R['max_boot_region_displacement_px_y>1080'] = round(foot, 3)
    def at(p, k):  # displacement at a point over the cycle
        x, y = p; return np.array([[dx[y, x], dy[y, x]] for dx, dy in [fields[k]]])[0]
    pts = {'guard': (640, 512), 'hand_near': (700, 600), 'hand_far': (790, 560), 'blade_mid': (400, 260), 'tip': (150, 24), 'head': (860, 190), 'boot_L': (270, 1130), 'boot_R': (1150, 1130)}
    tr = {k: np.array([[f[0][p[1], p[0]], f[1][p[1], p[0]]] for f in fields]) for k, p in pts.items()}
    R['point_displacement_range_px'] = {k: [round(float(np.abs(v).max()), 2)] for k, v in tr.items()}
    rel = np.abs(tr['hand_near'] - tr['guard']).max(); R['hand_vs_guard_relative_px'] = round(float(rel), 2)
    R['hand_vs_far_hand_relative_px'] = round(float(np.abs(tr['hand_near'] - tr['hand_far']).max()), 2)
    # blade as a rigid line: relative displacement between guard and tip should equal rotation*length only (no independent tip motion)
    tip_extra = np.abs((tr['tip'] - tr['guard'])).max(); R['tip_minus_guard_px'] = round(float(tip_extra), 2)
    # eye boxes: displacement uniformity (the eye must move rigidly with the head)
    for e, b in boxes.items():
        sub = [(dx[b[1]:b[3], b[0]:b[2]], dy[b[1]:b[3], b[0]:b[2]]) for dx, dy in fields]
        R[f'eye_{e}_warp_nonuniformity_px'] = round(max(float(max(np.ptp(a), np.ptp(b_))) for a, b_ in sub), 4)
    # 3. loop: exact periodicity, long run
    a0 = idle.field(0.0); a1 = idle.field(P); a2 = idle.field(P * 1000 + 0.0)
    R['loop_seam_max_field_diff'] = float(max(np.abs(a0[0] - a1[0]).max(), np.abs(a0[1] - a1[1]).max(), np.abs(a0[0] - a2[0]).max(), np.abs(a0[1] - a2[1]).max()))
    step = [float(np.abs(fields[i][1] - fields[(i + 1) % len(fields)][1]).max()) for i in range(len(fields))]
    R['max_frame_to_frame_dy_px_at_25fps'] = round(max(step), 3); R['seam_step_dy_px'] = round(step[-1], 3)
    # 4. RGBA / alpha integrity over cycle
    lo0 = (M[..., 3] > 0) & (M[..., 3] < 40); halo0 = int((M[..., :3][lo0].astype(int).sum(-1) > 700).sum()); R['bright_lowalpha_pixels_in_master'] = halo0
    bad = 0; halo = 0; grow = 0
    dil = np.array(Image.fromarray((M[..., 3] > 0).astype(np.uint8) * 255).filter(__import__('PIL.ImageFilter', fromlist=['x']).MaxFilter(21))) > 0
    for k in range(0, len(ts), 10):
        f = warp(M, *fields[k]); bad += int(np.isnan(f.astype(float)).sum())
        grow += int(((f[..., 3] > 8) & ~dil).sum())
        lo = (f[..., 3] > 0) & (f[..., 3] < 40); halo += int((f[..., :3][lo].astype(int).sum(-1) > 700).sum())
    R['nan_pixels'] = bad; R['alpha_outside_master_dilated10px'] = grow; R['bright_lowalpha_pixels_warped_avg_frame'] = round(halo / len(range(0, len(ts), 10)))
    R['master_alpha_range'] = [int(M[..., 3].min()), int(M[..., 3].max())]
    out = sys.argv[3] if len(sys.argv) > 3 else None
    print(json.dumps(R, indent=1))
    if out: json.dump(R, open(out, 'w'), indent=1)

if __name__ == '__main__':
    main()
