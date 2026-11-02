#!/usr/bin/env python3
"""Numeric acceptance for the house_01 furniture deliveries (local only).
Usage: python3 accept_h01.py <inbox dir>   (files named exactly as in spec/h01_asset_spec.json)
Checks per PNG: exists, exact @2x size, RGBA, alpha policy (0/255; soft contact shadow allowed only as dark pixels in the bottom 12%
of the canvas), RGB of fully transparent pixels = 0, no detached fragments (components < 12 px), ground contact (floor/stand items
touch the bottom 2 px rows; floor decals and wall items are reported but exempt), fireplace parts registration (body+fire composite == furn_h01_fireplace.png).
Writes report/accept_<timestamp>.json and prints PASS/FAIL per file."""
import json, pathlib, sys, time
import numpy as np
from PIL import Image
from scipy import ndimage

H01 = pathlib.Path(__file__).resolve().parents[1]; SPEC = json.loads((H01 / 'spec/h01_asset_spec.json').read_text())


def check(path, w, h, kind):
    r = dict(file=path.name, exists=path.exists())
    if not path.exists(): r['result'] = 'MISSING'; return r
    im = Image.open(path); r['size'] = list(im.size); r['mode'] = im.mode; a = np.array(im.convert('RGBA')).astype(int); al = a[..., 3]
    fails = []
    if im.size != (w, h): fails.append(f'size {im.size} != {(w, h)}')
    if im.mode != 'RGBA': fails.append(f'mode {im.mode}')
    semi = (al > 0) & (al < 255); band = np.zeros_like(semi); band[int(h * .88):] = True
    dark = a[..., :3].max(2) < 90
    bad_semi = semi & ~(band & dark); r['semi_px'] = int(semi.sum()); r['semi_outside_shadow_rule'] = int(bad_semi.sum())
    if bad_semi.sum(): fails.append(f'{int(bad_semi.sum())} semi-transparent px outside the contact-shadow rule')
    res = int((a[al == 0][:, :3] != 0).any(1).sum()); r['transparent_rgb_residual'] = res
    if res: fails.append(f'{res} transparent px with RGB residue')
    lab, n = ndimage.label(al > 0, structure=np.ones((3, 3)))
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)) if n else []
    frag = int(sum(1 for s in sizes if s < 12)); r['components'] = int(n); r['fragments_lt12'] = frag
    if frag: fails.append(f'{frag} detached fragments')
    rows = np.where((al == 255).any(1))[0]; r['bottom_gap_px'] = int(h - 1 - rows.max()) if len(rows) else None
    if kind == 'stand' and (r['bottom_gap_px'] is None or r['bottom_gap_px'] > 1): fails.append(f"bottom gap {r['bottom_gap_px']} px (must be 0-1)")
    cols = np.where((al == 255).any(0))[0]
    if len(cols): r['content_centre_offset_px'] = round((cols.min() + cols.max()) / 2 - (w - 1) / 2, 1)
    r['fails'] = fails; r['result'] = 'PASS' if not fails else 'FAIL'; return r


def main():
    inbox = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else H01 / 'inbox'); out = []
    for it in SPEC['items']: out.append(dict(prop=it['prop_id'], asset=it['new_asset_id'], **check(inbox / it['file'], *it['px'], it['kind'])))
    for f in ('furn_h01_fireplace_body.png', 'furn_h01_fireplace_fire.png'):
        out.append(dict(prop='p_03', asset=f[:-4], **check(inbox / f, 304, 272, 'part')))
    body, fire, full = (inbox / 'furn_h01_fireplace_body.png', inbox / 'furn_h01_fireplace_fire.png', inbox / 'furn_h01_fireplace.png')
    if body.exists() and fire.exists() and full.exists():
        comp = Image.open(body).convert('RGBA'); comp.alpha_composite(Image.open(fire).convert('RGBA'))
        diff = np.abs(np.array(comp).astype(int) - np.array(Image.open(full).convert('RGBA')).astype(int)).max(2)
        out.append(dict(asset='fireplace_registration', result='PASS' if (diff <= 2).mean() > .999 else 'FAIL', mismatched_px=int((diff > 2).sum())))
    stamp = time.strftime('%Y%m%d_%H%M%S'); (H01 / 'report').mkdir(exist_ok=True)
    (H01 / f'report/accept_{stamp}.json').write_text(json.dumps(dict(inbox=str(inbox), results=out), ensure_ascii=False, indent=1) + '\n')
    for r in out: print(r.get('result'), r.get('asset'), '; '.join(r.get('fails', [])))


if __name__ == '__main__':
    main()
