#!/usr/bin/env python3
"""MORWEN-PIXEL-66: right-facing walk, 6 frames, structural rebuild of the lower body.

Pipeline (all edits at 96x128; 48x64 is derived and then checked):
  1. Source frame 00 of MORWEN-PIXEL-65B is the single upper-body reference.
     Alpha is normalised (>=128 -> 255, else 0, RGB of transparent = 0).
  2. Reference split into fixed layers by an explicit pixel mask:
       U_front : torso / arms / bag / potions / skirt (rows above the hem)  -> protected, drawn in front of legs
       U_back  : lower cape tail and cape lining                            -> drawn behind legs (shear sway allowed)
     All old leg/boot pixels are discarded (not patched).
  3. Both legs are redrawn every frame from a walk-cycle table with 2-bone IK
     (hip -> knee -> ankle) and a rigid boot whose pitch follows the gait phase.
     Shapes are rasterised at 8x supersampling into label maps, then reduced
     to 1x by majority vote, then shaded/outlined with a fixed palette sampled
     from the 65B boots/stockings.
  4. Z order (back -> front): U_back, far leg, near leg, U_front.
  5. Whole-character vertical bob is applied to U_front/U_back/hips only;
     the ground line (sole bottom row) never moves for planted feet.
Requires numpy + Pillow only.
"""
from pathlib import Path
import json, math, hashlib, argparse
import numpy as np
from PIL import Image, ImageDraw

W, H = 96, 128
SS = 8                      # supersampling factor for leg rasterising
GROUND = 124                # bottom row of a planted sole (65B frame 00 value)
HEM_CUT = 89                # last skirt row kept in U_front for x >= 46
NEAR_HIP_X, FAR_HIP_X, HIP_Y = 56.0, 54.0, 87.0
L_THIGH, L_SHIN = 15.0, 16.5
ANKLE_H = 6.0               # ankle centre above the sole bottom when the foot is flat

# gait table, phase p of ONE leg (near leg uses p=f, far leg p=(f+3)%6)
#   ankle_dx (relative to hip x), foot pitch deg (+ = toe up), lift (px above ground of lowest boot pixel)
GAIT = {
    0: dict(dx=+9.0, pitch=+16, lift=0, role='contact / heel strike'),
    1: dict(dx=+3.0, pitch=0,   lift=0, role='loading, foot flat'),
    2: dict(dx=-3.0, pitch=0,   lift=0, role='mid-stance, body passes over'),
    3: dict(dx=-9.0, pitch=-24, lift=0, role='toe-off (heel up, toe on ground)'),
    4: dict(dx=-6.5, pitch=-22, lift=5, role='swing back, knee forward'),
    5: dict(dx=+4.0, pitch=+2,  lift=4, role='swing forward / passing'),
}
BOB = [0, 1, 0, 0, 1, 0]          # +1 = 1px lower (down/loading frames 1 and 4)
CAPE_SWAY = [0, -1, -1, 0, -1, -1]  # cape tail trails back during loading/passing (shear, px at the tail tip)

# palettes (sampled from 65B boots / stockings, quantised)
P = {
    'near': dict(
        st_out=(34, 6, 30), st_d=(58, 12, 44), st_m=(84, 24, 62), st_l=(112, 40, 82),
        bt_out=(42, 8, 38), bt_d=(78, 18, 66), bt_m=(110, 32, 94), bt_l=(144, 52, 118), bt_h=(196, 112, 168),
        sole=(40, 10, 34), heel=(62, 16, 52),
        g_d=(168, 92, 12), g_m=(232, 156, 8), g_l=(250, 210, 40)),
    'far': dict(
        st_out=(26, 4, 22), st_d=(44, 8, 34), st_m=(64, 16, 50), st_l=(84, 26, 64),
        bt_out=(34, 6, 30), bt_d=(62, 14, 52), bt_m=(88, 24, 76), bt_l=(114, 40, 96), bt_h=(150, 80, 128),
        sole=(32, 8, 28), heel=(50, 12, 42),
        g_d=(140, 76, 10), g_m=(196, 128, 8), g_l=(222, 176, 34)),
}
# labels
BG, ST, BT, CUFF, FOOT, SOLE, HEEL, TOE = 0, 1, 2, 3, 4, 5, 6, 7


def load_reference(src: Path):
    a = np.array(Image.open(src).convert('RGBA'))
    if a.shape != (H, W, 4):
        raise ValueError('reference must be 96x128 RGBA')
    halo = int(((a[:, :, 3] > 0) & (a[:, :, 3] < 128)).sum())
    a = a.copy()
    a[a[:, :, 3] < 128] = 0
    a[a[:, :, 3] >= 128, 3] = 255
    return a, halo


def split_layers(a):
    yy, xx = np.mgrid[0:H, 0:W]
    front = (yy <= HEM_CUT) | ((yy == HEM_CUT + 1) & (xx < 46))
    bound = np.full(H, -1)
    bound[91:94] = 45
    bound[94:98] = 33
    bound[98:101] = 31
    bound[101:113] = 28
    back = (~front) & (xx <= bound[yy])
    op = a[:, :, 3] > 0
    uf = np.zeros_like(a); uf[front & op] = a[front & op]
    ub = np.zeros_like(a); ub[back & op] = a[back & op]
    # drop isolated cape crumbs (<8 px, 8-connected) left by the cut
    from collections import deque
    bm = ub[:, :, 3] > 0; seen = np.zeros_like(bm)
    for y0, x0 in zip(*np.where(bm)):
        if seen[y0, x0]: continue
        comp = []; q = deque([(y0, x0)]); seen[y0, x0] = True
        while q:
            y, x = q.popleft(); comp.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy2, xx2 = y + dy, x + dx
                    if 0 <= yy2 < H and 0 <= xx2 < W and bm[yy2, xx2] and not seen[yy2, xx2]:
                        seen[yy2, xx2] = True; q.append((yy2, xx2))
        if len(comp) < 8 and not any((uf[y - 1:y + 2, x - 1:x + 2, 3] > 0).any() for y, x in comp):
            for y, x in comp: ub[y, x] = 0
    dropped = int((op & ~front & ~back).sum())
    return uf, ub, dropped


def shift(img, dx, dy):
    out = np.zeros_like(img)
    ys0, ys1 = max(0, dy), min(H, H + dy)
    xs0, xs1 = max(0, dx), min(W, W + dx)
    out[ys0:ys1, xs0:xs1] = img[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return out


def shear_cape(ub, tip_dx):
    if tip_dx == 0:
        return ub
    out = np.zeros_like(ub)
    for y in range(H):
        t = max(0.0, (y - 92) / 20.0)
        dx = int(round(tip_dx * min(1.0, t)))
        row = ub[y]
        if dx == 0:
            out[y] = row
        elif dx < 0:
            out[y, :dx] = row[-dx:]
        else:
            out[y, dx:] = row[:-dx]
    return out


def ik(hip, ankle, l1, l2):
    hx, hy = hip; ax, ay = ankle
    dx, dy = ax - hx, ay - hy
    d = math.hypot(dx, dy)
    d = min(d, l1 + l2 - 1e-3)
    # knee bends forward (+x): choose the solution with larger x
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / math.hypot(dx, dy), dy / math.hypot(dx, dy)
    px, py = hx + a * ux, hy + a * uy
    k1 = (px - h * uy, py + h * ux)
    k2 = (px + h * uy, py - h * ux)
    return k1 if k1[0] > k2[0] else k2


def capsule(draw, p, q, r, label):
    (x1, y1), (x2, y2) = p, q
    vx, vy = x2 - x1, y2 - y1
    n = math.hypot(vx, vy) or 1
    nx, ny = -vy / n * r, vx / n * r
    pts = [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]
    draw.polygon([(x * SS, y * SS) for x, y in pts], fill=label)
    for (cx, cy) in (p, q):
        draw.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=label)


def quad(draw, p, q, r1, r2, label):
    (x1, y1), (x2, y2) = p, q
    vx, vy = x2 - x1, y2 - y1
    n = math.hypot(vx, vy) or 1
    nx, ny = -vy / n, vx / n
    pts = [(x1 + nx * r1, y1 + ny * r1), (x2 + nx * r2, y2 + ny * r2), (x2 - nx * r2, y2 - ny * r2), (x1 - nx * r1, y1 - ny * r1)]
    draw.polygon([(x * SS, y * SS) for x, y in pts], fill=label)


# boot foot in local coords (x forward, y down, origin = ankle centre, foot flat)
FOOT_POLY = [(-4.4, -3.4), (3.0, -3.4), (6.4, -1.6), (10.0, -0.2), (11.8, 1.8), (11.8, 4.4), (10.6, 5.6),
             (-4.8, 5.6), (-5.0, 0.6)]
SOLE_POLY = [(-0.8, 4.6), (11.8, 4.6), (10.6, 6.0), (-0.8, 6.0)]
HEEL_POLY = [(-5.0, 3.0), (-0.6, 3.0), (-0.6, 6.0), (-4.8, 6.0)]
TOE_POLY = [(7.6, -0.6), (10.4, 0.4), (11.6, 2.2), (8.8, 1.6)]


def foot_points(poly, ankle, pitch, k=1.0):
    c, sn = math.cos(math.radians(-pitch)), math.sin(math.radians(-pitch))
    ax, ay = ankle
    return [(ax + k * (x * c - y * sn), ay + k * (x * sn + y * c)) for x, y in poly]


def solve_leg(hip_x, hip_y, phase):
    g = GAIT[phase]
    # place the ankle so the lowest boot point rests on GROUND - lift
    ankle = (hip_x + g['dx'], 0.0)
    pts = foot_points(FOOT_POLY + SOLE_POLY + HEEL_POLY, ankle, g['pitch'])
    low = max(y for _, y in pts)          # relative to ankle y = 0
    ay = (GROUND + 0.5) - g['lift'] - low
    ankle = (ankle[0], ay)
    target = GROUND - g['lift']
    for _ in range(12):   # snap: the rasterised lowest boot row must sit exactly on the target row
        knee = ik((hip_x, hip_y), ankle, L_THIGH, L_SHIN)
        leg = dict(hip=(hip_x, hip_y), knee=knee, ankle=ankle, pitch=g['pitch'])
        lab, _ = rasterise_leg(leg)
        low = int(np.where(lab > 0)[0].max())
        if low == target:
            break
        ankle = (ankle[0], ankle[1] + (0.25 if low < target else -0.25))
    else:
        raise ValueError(f'ground snap failed phase {phase}')
    return leg


def scaled(leg, k):
    return {'hip': tuple(v * k for v in leg['hip']), 'knee': tuple(v * k for v in leg['knee']),
            'ankle': tuple(v * k for v in leg['ankle']), 'pitch': leg['pitch']}


def rasterise_leg(leg, k=1.0):
    """k=1.0 -> 96x128, k=0.5 -> native 48x64 redraw of the same pose."""
    w, h = int(W * k), int(H * k)
    leg = scaled(leg, k)
    big = Image.new('L', (w * SS, h * SS), BG)
    d = ImageDraw.Draw(big)
    hip, knee, ankle, pitch = leg['hip'], leg['knee'], leg['ankle'], leg['pitch']
    capsule(d, hip, knee, 4.1 * k, ST)
    kx, ky = knee; ax, ay = ankle
    vx, vy = ax - kx, ay - ky; n = math.hypot(vx, vy)
    top = (kx - vx / n * 1.5 * k, ky - vy / n * 1.5 * k)
    quad(d, top, ankle, 5.0 * k, 4.5 * k, BT)
    cuff_end = (top[0] + vx / n * 2.4 * k, top[1] + vy / n * 2.4 * k)
    quad(d, (top[0] - vx / n * 0.6 * k, top[1] - vy / n * 0.6 * k), cuff_end, 5.4 * k, 5.2 * k, CUFF)
    d.polygon([(x * SS, y * SS) for x, y in foot_points(FOOT_POLY, ankle, pitch, k)], fill=FOOT)
    if k >= 1.0:
        d.polygon([(x * SS, y * SS) for x, y in foot_points(TOE_POLY, ankle, pitch, k)], fill=TOE)
    d.polygon([(x * SS, y * SS) for x, y in foot_points(SOLE_POLY, ankle, pitch, k)], fill=SOLE)
    d.polygon([(x * SS, y * SS) for x, y in foot_points(HEEL_POLY, ankle, pitch, k)], fill=HEEL)
    arr = np.array(big).reshape(h, SS, w, SS).transpose(0, 2, 1, 3).reshape(h, w, SS * SS)
    lab = np.zeros((h, w), np.uint8)
    best = np.zeros((h, w), int)
    for L in range(1, 8):
        cnt = (arr == L).sum(2)
        lab = np.where(cnt > best, L, lab); best = np.maximum(best, cnt)
    cover = (arr != BG).sum(2)
    lab[cover < SS * SS // 2] = BG
    return lab, dict(top=top, cuff_end=cuff_end, axis=(vx / n, vy / n), leg=leg, k=k)


def shade_leg(lab, geo, pal):
    k = geo['k']; leg = geo['leg']
    h, w = lab.shape
    out = np.zeros((h, w, 4), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = xx + 0.5, yy + 0.5
    hip, knee, ankle = leg['hip'], leg['knee'], leg['ankle']

    def across(p, q):
        vx, vy = q[0] - p[0], q[1] - p[1]; n = math.hypot(vx, vy)
        nx, ny = vy / n, -vx / n
        if nx < 0: nx, ny = -nx, -ny          # + = front side (+x)
        return (cx - p[0]) * nx + (cy - p[1]) * ny

    u_th, u_sh = across(hip, knee), across(knee, ankle)
    m = lab == ST
    out[m & (u_th > 1.4 * k)] = (*pal['st_l'], 255)
    out[m & (u_th <= 1.4 * k) & (u_th > -1.6 * k)] = (*pal['st_m'], 255)
    out[m & (u_th <= -1.6 * k)] = (*pal['st_d'], 255)
    m = lab == BT
    out[m & (u_sh > 1.6 * k)] = (*pal['bt_l'], 255)
    out[m & (u_sh <= 1.6 * k) & (u_sh > -1.8 * k)] = (*pal['bt_m'], 255)
    out[m & (u_sh <= -1.8 * k)] = (*pal['bt_d'], 255)
    m = lab == CUFF
    out[m] = (*pal['bt_d'], 255)
    ys, xs = np.where(m)
    if len(xs):                                # gold buckle on the strap, visible side
        uu = u_sh[ys, xs]
        j = int(np.argmax(uu - 0.0))
        out[ys[j], xs[j]] = (*pal['g_l'], 255)
        if k >= 1.0:
            for i in np.argsort(np.abs(uu - 0.2))[:2]:
                out[ys[i], xs[i]] = (*pal['g_m'], 255)
    m = lab == FOOT
    out[m] = (*pal['bt_m'], 255)
    out[m & ~np.roll(m, 1, axis=0)] = (*pal['bt_l'], 255)
    out[lab == TOE] = (*pal['bt_h'], 255)
    out[lab == SOLE] = (*pal['sole'], 255)
    out[lab == HEEL] = (*pal['heel'], 255)
    vx, vy = geo['axis']; ce = geo['cuff_end']
    s_al = (cx - ce[0]) * vx + (cy - ce[1]) * vy
    s_len = math.hypot(ankle[0] - ce[0], ankle[1] - ce[1])
    if k >= 1.0:   # X-lacing: period 3 rows, 3px band on the front of the shaft
        band = (lab == BT) & (s_al > 0.3) & (s_al < s_len - 0.6) & (u_sh > 0.2) & (u_sh < 3.2)
        col_i = np.clip(np.floor(u_sh - 0.2), 0, 2).astype(int)
        row_i = np.floor(s_al).astype(int) % 3
        out[band & (row_i == 0) & (col_i != 1)] = (*pal['g_m'], 255)
        out[band & (row_i == 1) & (col_i == 1)] = (*pal['g_l'], 255)
    else:          # 48x64: single dotted lace column every other row
        band = (lab == BT) & (s_al > 0.2) & (s_al < s_len - 0.4) & (u_sh > 0.1) & (u_sh < 1.1)
        out[band & (np.floor(s_al).astype(int) % 2 == 0)] = (*pal['g_m'], 255)
    if k >= 1.0:
        x, y = int(ankle[0] + 1.5), int(ankle[1] - 1.0)
        if 0 <= x < w and 0 <= y < h and lab[y, x] in (BT, FOOT):
            out[y, x] = (*pal['g_m'], 255)
    leg_m = lab != BG
    edge = np.zeros_like(leg_m)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = np.zeros_like(leg_m)
        ys0, ys1 = max(0, dy), h + min(0, dy)
        xs0, xs1 = max(0, dx), w + min(0, dx)
        nb[ys0:ys1, xs0:xs1] = leg_m[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        edge |= leg_m & ~nb
    stock = lab == ST
    out[edge & stock] = (*pal['st_out'], 255)
    out[edge & ~stock] = (*pal['bt_out'], 255)
    if k >= 1.0:
        cuffm = lab == CUFF
        above = np.zeros_like(cuffm); above[:-1] = cuffm[1:]
        out[stock & above & ~edge] = (*pal['st_d'], 255)
    return out


def over(dst, src):
    m = src[:, :, 3] > 0
    dst[m] = src[m]
    return dst


def build(source: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    ref, halo = load_reference(source / 'morwen_right_walk_00_96x128.png')
    uf, ub, dropped = split_layers(ref)
    frames, smalls, legs_log = [], [], []
    for f in range(6):
        bob = BOB[f]
        hip_y = HIP_Y + bob
        near = solve_leg(NEAR_HIP_X, hip_y, f)
        far = solve_leg(FAR_HIP_X, hip_y, (f + 3) % 6)
        lab_f, geo_f = rasterise_leg(far)
        lab_n, geo_n = rasterise_leg(near)
        img = np.zeros((H, W, 4), np.uint8)
        back_l = shift(shear_cape(ub, CAPE_SWAY[f]), 0, bob)
        front_l = shift(uf, 0, bob)
        over(img, back_l)
        over(img, shade_leg(lab_f, geo_f, P['far']))
        over(img, shade_leg(lab_n, geo_n, P['near']))
        over(img, front_l)
        # 48x64: fixed layers = NEAREST (identical rule to 65B, keeps the approved 48px face/hat), legs redrawn natively
        sm = np.zeros((H // 2, W // 2, 4), np.uint8)
        over(sm, back_l[1::2, 1::2].copy())
        lf, gf = rasterise_leg(far, 0.5); ln, gn = rasterise_leg(near, 0.5)
        over(sm, shade_leg(lf, gf, P['far']))
        over(sm, shade_leg(ln, gn, P['near']))
        over(sm, front_l[1::2, 1::2].copy())
        sm[sm[:, :, 3] == 0, :3] = 0
        smalls.append(sm)
        img[img[:, :, 3] == 0, :3] = 0
        frames.append(img)
        legs_log.append({'frame': f, 'bob': bob,
                         'near': {k: [round(v, 2) for v in near[k]] for k in ('hip', 'knee', 'ankle')} | {'pitch': near['pitch'], 'phase': GAIT[f]['role']},
                         'far': {k: [round(v, 2) for v in far[k]] for k in ('hip', 'knee', 'ankle')} | {'pitch': far['pitch'], 'phase': GAIT[(f + 3) % 6]['role']}})
    for f, img in enumerate(frames):
        name = f'morwen_right_walk_{f:02d}'
        Image.fromarray(img, 'RGBA').save(out / f'{name}_96x128.png')
        Image.fromarray(smalls[f], 'RGBA').save(out / f'{name}_48x64.png')
    meta = {'halo_pixels_removed_from_reference': halo, 'old_lower_body_pixels_discarded': dropped,
            'gait': GAIT, 'bob': BOB, 'cape_sway': CAPE_SWAY, 'legs': legs_log}
    (out / 'build_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    return frames, smalls, uf, ub, meta


def downscale(img):
    """48x64: 2x2 blocks. Alpha by majority (>=2 of 4 opaque); colour = the block's
    most frequent opaque colour, ties -> the darkest (keeps 1px outlines)."""
    out = np.zeros((H // 2, W // 2, 4), np.uint8)
    for y in range(H // 2):
        for x in range(W // 2):
            blk = img[2 * y:2 * y + 2, 2 * x:2 * x + 2].reshape(4, 4)
            op = blk[blk[:, 3] > 0]
            if len(op) < 2:
                continue
            cols, cnt = np.unique(op[:, :3], axis=0, return_counts=True)
            best = max(range(len(cols)), key=lambda i: (cnt[i], -int(cols[i].astype(int).sum())))
            out[y, x] = (*cols[best], 255)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    build(a.source, a.out)
    print('ok')
