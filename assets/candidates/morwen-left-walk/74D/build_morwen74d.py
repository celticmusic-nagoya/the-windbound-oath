#!/usr/bin/env python3
"""ART-74D: ART-74C 8-frame walk (motion unchanged) + official colours + short boots / knee socks.

FIX-01 colour : part-wise adjustment of the 74C left-side reference toward the official left profile (recolor74d.py);
                leg ramps (socks, boots, leg gold, pleats) and the 3 shared golds are designed from the official
                OKLab measurements (LEG_RAMPS / GOLD3_74D below).
FIX-02 boots  : boot shaft starts half way down the shin (official left: boot top at ~0.5 of knee->ankle) instead of
                just under the knee; the upper shin is knee sock. Lacing band / strap / cuff keep the 68 structure.
FIX-03 socks  : sock = thigh welt -> boot cuff, its own lighter warm-mauve ramp (official sock L .37-.52, h 354)
                against darker purple-black leather (official boot L .19-.44, h 322); skin band + garter unchanged.
FIX-04 motion : 74C timing / gait / pelvis / arm / lag tables are reused as they are (build_morwen74c), the region
                masks are taken from the 74C reference so layering is identical; only colours and the boot/sock
                split change. 12f = same cycle.
  python3 build_morwen74d.py --ref74c ../74C/REFERENCE_left_side_edit_right_coords.png --source ../74A/source_65B_F00 \
      --official <official left PNG> --out <dir>
"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_PIPE = _os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE, '..', '..', 'morwen-right-walk', '72'))
_B74 = _os.environ.get('MORWEN74B_DIR', _os.path.join(_HERE, '..', '74B'))
_C74 = _os.environ.get('MORWEN74C_DIR', _os.path.join(_HERE, '..', '74C'))
_sys.path[:0] = [_HERE, _C74, _B74, _PIPE]
import argparse, copy, json, math, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import build_morwen66 as B, build_morwen67 as C, build_morwen68 as D, build_morwen70 as E, build_morwen70art as A
import build_morwen71 as M
import build_morwen74c as X
from oklab import oklab2rgb
from parts74d import part_masks
from recolor74d import recolor, OFFICIAL, OFFICIAL_GOLD, GOLD_PIX, PIX_CHROMA

H, W = 128, 96
BOOT_T = 0.50     # boot top along knee->ankle (0 = knee, 1 = ankle); 74C: boot from just above the knee


def ok(L, C, h):
    return tuple(int(v) for v in oklab2rgb(np.array([L, C * math.cos(math.radians(h)), C * math.sin(math.radians(h))])))


def ramp(Ls, C, h): return [ok(L, C, h) for L in Ls]


LEG_RAMPS = {
    'stock':     ramp([0.20, 0.29, 0.37, 0.44, 0.52], 0.050, 354),
    'stock_far': ramp([0.16, 0.23, 0.30, 0.36, 0.42], 0.045, 354),
    'boot':      ramp([0.13, 0.20, 0.27, 0.35, 0.46, 0.64], 0.055, 322),
    'boot_far':  ramp([0.10, 0.16, 0.22, 0.28, 0.36, 0.50], 0.050, 322),
    'gold':      ramp(GOLD_PIX['L'], GOLD_PIX['C'], GOLD_PIX['h']),
    'gold_far':  ramp([v * 0.85 for v in GOLD_PIX['L']], GOLD_PIX['C'] * 0.9, GOLD_PIX['h']),
    'pleat':     ramp([0.17, 0.24, 0.31, 0.37, 0.43], OFFICIAL['skirt']['C'] * PIX_CHROMA, OFFICIAL['skirt']['h']),
}
GOLD3_74D = {'light': ok(0.90, 0.110, 74), 'mid': ok(0.76, 0.120, 70), 'dark': ok(0.58, 0.110, 64)}
RIM_74D = {'boot': LEG_RAMPS['boot'][3], 'stock': LEG_RAMPS['stock'][3], 'boot_far': LEG_RAMPS['boot_far'][3], 'stock_far': LEG_RAMPS['stock_far'][3]}


def rasterise74d(leg, k=1.0):
    """= build_morwen68.rasterise68 with the boot shaft starting at BOOT_T; knee -> boot top is sock (ST)."""
    ST, BT, CUFF, FOOT, SOLE, HEEL, TOE = D.ST, D.BT, D.CUFF, D.FOOT, D.SOLE, D.HEEL, D.TOE
    w, h = int(W * k), int(H * k)
    L = B.scaled(leg, k); SS = B.SS
    big = Image.new('L', (w * SS, h * SS), 0); d = ImageDraw.Draw(big)
    hip, knee, ankle, pitch = L['hip'], L['knee'], L['ankle'], L['pitch']
    d.ellipse([(hip[0] - D.R_HIP * k) * SS, (hip[1] - D.R_HIP * k) * SS, (hip[0] + D.R_HIP * k) * SS, (hip[1] + D.R_HIP * k) * SS], fill=ST)
    B.quad(d, hip, knee, D.R_HIP * k, D.R_KNEE * k, ST)
    d.ellipse([(knee[0] - D.R_KNEE * k) * SS, (knee[1] - D.R_KNEE * k) * SS, (knee[0] + D.R_KNEE * k) * SS, (knee[1] + D.R_KNEE * k) * SS], fill=ST)
    kx, ky = knee; ax, ay = ankle
    vx, vy = ax - kx, ay - ky; n = math.hypot(vx, vy); ux, uy = vx / n, vy / n
    nx, ny = uy, -ux
    if nx < 0: nx, ny = -nx, -ny
    top = (kx - ux * 1.5 * k, ky - uy * 1.5 * k)
    L2 = math.hypot(ax - top[0], ay - top[1])
    prof_back = [5.0, 5.4, 5.2, 4.7, 4.3]; prof_front = [4.9, 4.6, 4.4, 4.3, 4.2]
    ts = np.linspace(0, 1, 5)
    def outline(t0, t1, shrink):
        fr, bk = [], []
        for t in np.linspace(t0, t1, 5):
            pb = np.interp(t, ts, prof_back) - shrink; pf = np.interp(t, ts, prof_front) - shrink
            px, py = top[0] + ux * L2 * t, top[1] + uy * L2 * t
            fr.append((px + nx * pf * k, py + ny * pf * k)); bk.append((px - nx * pb * k, py - ny * pb * k))
        return fr + bk[::-1]
    # sock over the calf (slightly slimmer than the leather), then the short boot shaft
    d.polygon([(x * SS, y * SS) for x, y in outline(0.0, BOOT_T + 0.04, 0.45)], fill=ST)
    d.polygon([(x * SS, y * SS) for x, y in outline(BOOT_T, 1.0, 0.0)], fill=BT)
    btop = (top[0] + ux * L2 * BOOT_T, top[1] + uy * L2 * BOOT_T)
    cuff_end = (btop[0] + ux * 2.0 * k, btop[1] + uy * 2.0 * k)
    pb = float(np.interp(BOOT_T, ts, prof_back)); pf = float(np.interp(BOOT_T, ts, prof_front))
    B.quad(d, (btop[0] - ux * 0.5 * k, btop[1] - uy * 0.5 * k), cuff_end, (max(pb, pf) + 0.3) * k, (max(pb, pf) + 0.2) * k, CUFF)
    d.polygon([(x * SS, y * SS) for x, y in B.foot_points(B.FOOT_POLY, ankle, pitch, k)], fill=FOOT)
    if k >= 1:
        d.polygon([(x * SS, y * SS) for x, y in B.foot_points(B.TOE_POLY, ankle, pitch, k)], fill=TOE)
    d.polygon([(x * SS, y * SS) for x, y in B.foot_points(B.SOLE_POLY, ankle, pitch, k)], fill=SOLE)
    d.polygon([(x * SS, y * SS) for x, y in B.foot_points(B.HEEL_POLY, ankle, pitch, k)], fill=HEEL)
    arr = np.array(big).reshape(h, SS, w, SS).transpose(0, 2, 1, 3).reshape(h, w, SS * SS)
    lab = np.zeros((h, w), np.uint8); best = np.zeros((h, w), int)
    for Lb in range(1, 8):
        cnt = (arr == Lb).sum(2)
        lab = np.where(cnt > best, Lb, lab); best = np.maximum(best, cnt)
    lab[(arr != 0).sum(2) < SS * SS // 2] = 0
    yy, xx = np.mgrid[0:h, 0:w]
    tx, ty = knee[0] - hip[0], knee[1] - hip[1]; tn = math.hypot(tx, ty)
    s_dist = ((xx + 0.5 - hip[0]) * tx + (yy + 0.5 - hip[1]) * ty) / tn / k
    stock = lab == ST
    lab[stock & (s_dist < D.S_TOP)] = D.SKIN
    lab[stock & (s_dist >= D.S_TOP) & (s_dist < D.S_TOP + D.WELT_W)] = D.WELT
    geo = dict(top=top, cuff_end=cuff_end, axis=(ux, uy), leg=L, k=k, s_dist=s_dist)
    return lab, geo


def run(ref74d, ref74c, source, out, nframes):
    """X.run_pipeline (8f/12f branch) with: layers from the 74D reference, region masks from the 74C reference,
    74D leg ramps / golds / rims, short-boot rasteriser."""
    out.mkdir(parents=True, exist_ok=True)
    oref, _ = B.load_reference(source / 'morwen_right_walk_00_96x128.png'); ouf, _, _ = B.split_layers(oref)
    pal = copy.deepcopy(D.build_palette68(ouf)[0]); pal.update({k: list(v) for k, v in LEG_RAMPS.items()})
    uf, ub, _ = B.split_layers(ref74d)
    cuf, cub, _ = B.split_layers(ref74c)
    A.GOLD3.clear(); A.GOLD3.update(GOLD3_74D); A.ART['level'] = 'B'
    E.configure('B', ouf); E._RIM.clear(); E._RIM.update(RIM_74D)
    X.CUR['nf'] = nframes; T = X.tables(nframes)
    D.SECONDARY_MOTION = copy.deepcopy(T['motion'])
    M.STATE['proposal'] = 'GLASSES'
    D.shade68 = M.shade71; D.compose68 = M.compose71
    o_r = D.rasterise68; D.rasterise68 = rasterise74d
    saved = X.setup_motion(T)
    try:
        masks = D.region_masks(cuf, cub)            # structure of 74C (colour-independent layering)
        for f in range(nframes):
            X.CUR['f'] = f; bob = T['bob'][f]
            U, foot = D.upper_layers(f, uf, ub, masks)
            U96 = {k: B.shift(v, 0, bob) for k, v in U.items()}
            img, layers, legs = D.compose68(f, U96, pal, 1.0)
            U48 = {k: v[1::2, 1::2].copy() for k, v in U96.items()}
            sm, _, _ = D.compose68(f, U48, pal, 0.5)
            Image.fromarray(img, 'RGBA').save(out / f'morwen_right_walk_{f:02d}_96x128.png')
            Image.fromarray(sm, 'RGBA').save(out / f'morwen_right_walk_{f:02d}_48x64.png')
    finally:
        X.restore(saved); D.rasterise68 = o_r
        D.shade68 = E._shade68; D.compose68 = A._compose68; M.STATE['proposal'] = None


def build(ref74c_path: Path, source: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    w = out / '_work'
    if w.exists(): shutil.rmtree(w)
    ref74c, _ = B.load_reference(ref74c_path)
    full74c = np.array(Image.open(ref74c_path).convert('RGBA'))
    uf, ub, _ = B.split_layers(ref74c)
    parts, keep = part_masks(X.region_masks8(uf, ub), uf[:, :, 3] > 0, ub[:, :, 3] > 0)
    full74d, clog = recolor(full74c, parts, keep)
    refdir = w / 'ref74d'; refdir.mkdir(parents=True)
    Image.fromarray(full74d, 'RGBA').save(refdir / 'morwen_right_walk_00_96x128.png')
    Image.fromarray(full74d, 'RGBA').save(out / 'REFERENCE_left_side_74D_colour_right_coords.png')
    lab = np.zeros((H, W, 4), np.uint8)
    PC = {'hat': (60, 60, 230), 'hair': (220, 50, 50), 'bow': (40, 200, 60), 'jacket': (240, 160, 30), 'skirt': (230, 40, 230), 'mantle': (40, 220, 220), 'potion': (150, 90, 255)}
    for n, m in parts.items(): lab[m] = (*PC[n], 255)
    lab[keep & (full74c[:, :, 3] > 0)] = (255, 255, 255, 255)
    Image.fromarray(lab, 'RGBA').save(out / 'PART_MASKS_74D_right_coords.png')
    ref74d, _ = B.load_reference(refdir / 'morwen_right_walk_00_96x128.png')
    for nf in (8, 12):
        run(ref74d, ref74c, source, w / f'r{nf}', nf)
        for f in range(nf):
            for s in ('96x128', '48x64'):
                Image.open(w / f'r{nf}' / f'morwen_right_walk_{f:02d}_{s}.png').transpose(Image.FLIP_LEFT_RIGHT).save(out / f'morwen_left_walk_{nf}f_{f:02d}_{s}.png')
    meta = {'base': 'ART-74C (8f motion, 12f same cycle)', 'boot_top_t': BOOT_T,
            'leg_ramps': {k: [list(c) for c in v] for k, v in LEG_RAMPS.items()},
            'gold3': {k: list(v) for k, v in GOLD3_74D.items()}, 'rim': {k: list(v) for k, v in RIM_74D.items()},
            'official_targets': OFFICIAL, 'official_gold_measured': OFFICIAL_GOLD, 'gold_pixel_target': GOLD_PIX,
            'pixel_chroma_factor': PIX_CHROMA, 'recolor_log': clog}
    (out / 'build_meta_74d.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    shutil.rmtree(w)
    return clog


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref74c', type=Path, required=True); ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); build(a.ref74c, a.source, a.out); print('ok')
