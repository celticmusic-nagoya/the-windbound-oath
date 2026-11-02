#!/usr/bin/env python3
"""Normalize raw ChatGPT deliveries into the exact house_01 game PNGs (local candidates only).

  python3 normalize_h01.py split  <sheet.png> <outdir>          # cut a multi-item sheet into numbered pieces (+ index preview)
  python3 normalize_h01.py fit    <raw.png> <asset_id> <outdir>  # one raw image -> furn_h01_<x>.png at the spec size
  python3 normalize_h01.py batch  <rawdir> <outdir>              # every <asset_id>*.png / furn_h01_*.png in rawdir
  python3 normalize_h01.py fire   <fireplace.png> <outdir> [--body body.png]   # body / fire layers aligned to the full fireplace

Pipeline per item (data: spec/h01_asset_spec.json + the FIT table below, measured from the current art so footprints stay on the
existing collision/event layout):
  1 background removal: keeps a real alpha channel; otherwise flood-fills from the border (flat colour or 2-colour checkerboard)
  2 trim to content, scale to fit the target content box (aspect kept, LANCZOS), centred on the target centre
  3 placement: stand -> lowest opaque row on the bottom row (anchor = bottom centre); floor/wall -> centred in the target box
  4 alpha: binary (>=128 -> 255), transparent RGB = 0, connected fragments < 12 px removed
Never writes into the repository."""
import json, pathlib, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

H01 = pathlib.Path(__file__).resolve().parents[1]
SPEC = {it['new_asset_id']: it for it in json.loads((H01 / 'spec/h01_asset_spec.json').read_text())['items']}
# max content box [x0, y0, x1, y1] (px, exclusive) = alpha bbox of the current art (measure_fit); its size bounds the new art
FIT = {"furn_h01_doormat": [4, 8, 164, 64], "furn_h01_window_wall": [0, 4, 128, 148], "furn_h01_tapestry": [0, 0, 144, 196], "furn_h01_fireplace": [4, 4, 300, 272], "furn_h01_bed": [4, 4, 244, 184], "furn_h01_bed_small": [8, 8, 216, 168], "furn_h01_rug_green": [4, 4, 400, 240], "furn_h01_table_small": [8, 12, 184, 144], "furn_h01_chair_back": [8, 12, 76, 112], "furn_h01_stool": [0, 0, 64, 72], "furn_h01_spinning_wheel": [8, 24, 120, 156], "furn_h01_barrel": [8, 4, 92, 124], "furn_h01_jar": [0, 8, 80, 104]}


def measure_fit(repo='/home/claude/the-windbound-oath'):
    """Recompute FIT from the current art (run once; result printed for pasting / kept in fit_measured.json)."""
    out = {}
    for k, it in SPEC.items():
        a = np.array(Image.open(pathlib.Path(repo) / it['current_png']).convert('RGBA'))[..., 3] > 0
        ys, xs = np.nonzero(a); out[k] = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    (H01 / 'spec/fit_measured.json').write_text(json.dumps(out, indent=1) + '\n'); return out


def remove_bg(im, tol=24):
    a = np.array(im.convert('RGBA')).astype(int)
    if (a[..., 3] < 250).mean() > .02: return a                       # already has transparency
    rgb = a[..., :3]; h, w = rgb.shape[:2]
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    cols, cnt = np.unique((border // 8) * 8, axis=0, return_counts=True); order = np.argsort(-cnt)
    near = np.zeros((h, w), bool)
    for i in order[:2]:                                                # flat background or the two checkerboard colours
        if cnt[i] >= len(border) * .1: near |= (np.abs(rgb - (cols[i] + 4)).max(2) <= tol)
    lab, _ = ndimage.label(near); edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])); edge = edge[edge > 0]
    bg = np.isin(lab, edge); a[..., 3] = np.where(bg, 0, 255); return a


def clean(a, min_frag=12):
    a = a.copy(); a[..., 3] = np.where(a[..., 3] >= 128, 255, 0); a[a[..., 3] == 0] = 0
    lab, n = ndimage.label(a[..., 3] > 0, structure=np.ones((3, 3)))
    if n:
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
        for i, s in enumerate(sizes, 1):
            if s < min_frag: a[lab == i] = 0
    return a.astype(np.uint8)


def fit(raw_path, asset_id, outdir):
    it = SPEC[asset_id]; W, H = it['px']; x0, y0, x1, y1 = FIT[asset_id]
    a = clean(remove_bg(Image.open(raw_path)))
    ys, xs = np.nonzero(a[..., 3]); src = Image.fromarray(a, 'RGBA').crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    bw, bh = x1 - x0, y1 - y0; s = min(bw / src.width, bh / src.height)
    src = src.resize((max(1, round(src.width * s)), max(1, round(src.height * s))), Image.LANCZOS)
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0)); px = (W - src.width) // 2   # horizontally centred on the anchor
    py = (H - src.height) if it['kind'] == 'stand' else y0 + (bh - src.height) // 2
    cv.alpha_composite(src, (px, py)); out = clean(np.array(cv))
    if it['kind'] == 'stand':                                         # make sure the lowest opaque row is the bottom row
        rows = np.nonzero(out[..., 3].any(1))[0]; d = H - 1 - rows.max()
        if d > 0: out = np.roll(out, d, axis=0); out[:d] = 0
    p = pathlib.Path(outdir) / it['file']; p.parent.mkdir(parents=True, exist_ok=True); Image.fromarray(out, 'RGBA').save(p, optimize=True)
    return dict(asset=asset_id, raw=str(raw_path), scale=round(s, 3), placed=[px, py, src.width, src.height], out=str(p))


def split(sheet, outdir, min_area=400):
    a = clean(remove_bg(Image.open(sheet)), 12); m = a[..., 3] > 0
    m2 = ndimage.binary_dilation(m, iterations=3); lab, n = ndimage.label(m2)
    boxes = sorted([s for s in ndimage.find_objects(lab) if (s[0].stop - s[0].start) * (s[1].stop - s[1].start) >= min_area], key=lambda s: (s[0].start // 64, s[1].start))
    out = pathlib.Path(outdir); out.mkdir(parents=True, exist_ok=True); prev = Image.fromarray(a, 'RGBA').convert('RGB'); d = ImageDraw.Draw(prev); res = []
    for i, s in enumerate(boxes, 1):
        piece = a[s]; f = out / f'piece_{i:02d}.png'; Image.fromarray(piece, 'RGBA').save(f); res.append(dict(piece=f.name, box=[s[1].start, s[0].start, s[1].stop, s[0].stop]))
        d.rectangle([s[1].start, s[0].start, s[1].stop, s[0].stop], outline=(255, 0, 90), width=3); d.text((s[1].start + 4, s[0].start + 4), str(i), fill=(255, 0, 90))
    prev.save(out / 'pieces_index.png'); (out / 'pieces.json').write_text(json.dumps(res, indent=1) + '\n'); return res


def fire_split(full_path, outdir, body_path=None):
    """Returns body / fire layers on the same 304x272 canvas so that body + fire == full.
    With a delivered body: fire = pixels where full differs from body. Without: fire = warm saturated bright pixels inside the
    fireplace opening; those pixels are replaced by the opening's dark interior colour in the body."""
    full = np.array(Image.open(full_path).convert('RGBA')).astype(int)
    if body_path:
        body = np.array(Image.open(body_path).convert('RGBA')).astype(int); fm = (np.abs(full - body).max(2) > 6) & (full[..., 3] > 0)
    else:
        r, g, b = full[..., 0], full[..., 1], full[..., 2]; mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
        warm = (r >= g) & (g >= b) & (mx > 170) & ((mx - mn) > .55 * mx)   # flame colours; wood (#b88c56) stays in the body & (full[..., 3] > 0)
        dark = (mx < 60) & (full[..., 3] > 0); lab, n = ndimage.label(dark)
        if n:
            big = 1 + int(np.argmax(ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)))); ys, xs = np.nonzero(lab == big)
            box = np.zeros_like(warm); box[ys.min() - 4:ys.max() + 5, xs.min() - 4:xs.max() + 5] = True; fm = warm & box
            inner = full[lab == big][:, :3].mean(0).astype(int)
        else: fm = warm; inner = np.array([24, 14, 10])
        fm = ndimage.binary_dilation(fm, iterations=1) & (full[..., 3] > 0)
        body = full.copy(); body[fm, :3] = inner
    fire = np.zeros_like(full); fire[fm] = full[fm]
    out = pathlib.Path(outdir); out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(body.astype(np.uint8), 'RGBA').save(out / 'furn_h01_fireplace_body.png'); Image.fromarray(fire.astype(np.uint8), 'RGBA').save(out / 'furn_h01_fireplace_fire.png')
    return dict(fire_px=int(fm.sum()), derived_body=body_path is None)


def main():
    cmd = sys.argv[1]
    if cmd == 'measure': print(json.dumps(measure_fit()))
    elif cmd == 'split': print(json.dumps(split(sys.argv[2], sys.argv[3]), ensure_ascii=False))
    elif cmd == 'fit': print(json.dumps(fit(sys.argv[2], sys.argv[3], sys.argv[4]), ensure_ascii=False))
    elif cmd == 'fire': print(json.dumps(fire_split(sys.argv[2], sys.argv[3], sys.argv[sys.argv.index('--body') + 1] if '--body' in sys.argv else None)))
    elif cmd == 'batch':
        raw, out = pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]); log = []
        for k in SPEC:
            cands = sorted(raw.glob(k + '*.png')) or sorted(raw.glob(k.replace('furn_h01_', '') + '*.png'))
            cands = [c for c in cands if not c.stem.endswith(('_body', '_fire'))]
            if cands: log.append(fit(cands[0], k, out))
            else: log.append(dict(asset=k, missing=True))
        full = out / 'furn_h01_fireplace.png'
        if full.exists():
            body = next(iter(sorted(raw.glob('*fireplace_body*.png'))), None)
            if body: body = fit(body, 'furn_h01_fireplace', out / '_body')['out']
            log.append(dict(fire=fire_split(full, out, body)))
        (out / 'normalize_log.json').write_text(json.dumps(log, ensure_ascii=False, indent=1) + '\n')
        for l in log: print(l)


if __name__ == '__main__':
    main()
