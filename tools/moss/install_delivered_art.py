#!/usr/bin/env python3
"""Moss Forest delivered-art intake (ChatGPT-generated transparent sheets/singles -> runtime sprites + manifest rules).

usage: install_delivered_art.py <src_dir> [--out img/field/moss/art] [--dry-run]
<src_dir> holds the delivered PNGs under these canonical names (see SPEC): seal_closed, seal_corrupted, seal_opening, arch_2,
stone_A..stone_F, sheet_fx, sheet_a1, sheet_a2, sheet_veg1, sheet_veg2, sheet_a3stones, sheet_decals, tiles.

What it does
  * splits sheets into single sprites (connected components of the real alpha, reading order), cleans the matte fringe of opaque
    sprites (hard alpha + edge-colour decontamination), keeps translucent FX untouched ('soft'),
  * scales every sprite to 2x its world size (bottom-centre anchored, see SPEC) and writes <out>/<name>.png,
  * (re)writes the manifest rules tagged "gen": "delivered_art" (node / layer / entity) + the ground tiles.
Re-running is idempotent. First matching rule wins in manifest.json, so these rules are inserted before the stand-ins."""
import os, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
S = 2  # output px per world px

# name: (source, selector, mode, ('h'|'w', world px), kinds)   kinds: n=node rule, l=layer rule, e=<entity key>
SPEC = {
 # --- A3 ancient grove ---
 'a3_seal_closed':    ('seal_closed', None, 'soft', ('w', 170), ['e:seal']),
 'a3_seal_corrupted': ('seal_corrupted', None, 'soft', ('w', 170), ['e:seal_corrupted']),
 'a3_seal_opening':   ('seal_opening', None, 'soft', ('w', 170), ['e:seal_opening']),
 'anc_arch_broken_01': ('arch_2', None, 'opaque', ('w', 175), ['n']),
 'anc_standing_L_01': ('stone_B', None, 'opaque', ('h', 140), ['n']),
 'anc_standing_L_02': ('stone_A', None, 'opaque', ('h', 140), ['n']),
 'anc_standing_L_03': ('stone_D', None, 'opaque', ('h', 140), ['n']),
 'anc_rune_broken_01': ('stone_F', None, 'opaque', ('h', 120), ['n']),
 'anc_rune_broken_02': ('stone_E', None, 'opaque', ('h', 120), ['n']),
 'anc_boundary_stone_01': ('sheet_a3stones', 0, 'opaque', ('h', 78), ['n']),
 'anc_boundary_stone_02': ('sheet_a3stones', 1, 'opaque', ('h', 70), ['n']),
 'anc_shrine_frag_01': ('sheet_a3stones', 2, 'opaque', ('w', 120), ['n']),
 'anc_shrine_frag_02': ('sheet_a3stones', 3, 'opaque', ('h', 92), ['n']),
 'anc_stone_marker_old_01': ('sheet_a3stones', 4, 'opaque', ('h', 108), ['n']),
 'anc_rune_decal_01': ('sheet_decals', 0, 'opaque', ('w', 150), ['n']),
 'anc_rune_decal_02': ('sheet_decals', 1, 'opaque', ('w', 150), ['n']),
 'anc_rune_decal_03': ('sheet_decals', 2, 'opaque', ('w', 150), ['n']),
 'anc_rune_decal_04': ('sheet_decals', 3, 'opaque', ('w', 150), ['n']),
 # --- A2 mossy ravine ---
 'prop_bridge_wood_01': ('sheet_a2', 0, 'opaque', ('w', 220), ['n']),
 'prop_bridge_post_01': ('sheet_a2', 1, 'opaque', ('h', 72), ['n']),
 'fx_waterfall_01': ('sheet_a2', 2, 'opaque', ('w', 170), ['n']),
 'prop_root_arch_01': ('sheet_a2', 3, 'opaque', ('w', 160), ['n']),
 'prop_root_steps_01': ('sheet_a2', 4, 'opaque', ('w', 120), ['n']),
 'prop_fence_broken_01': ('sheet_a2', 5, 'opaque', ('w', 135), ['n']),
 # --- A1 sunlit path ---
 'prop_marker_signpost_01': ('sheet_a1', 0, 'opaque', ('h', 84), ['n']),
 'prop_marker_fork_01': ('sheet_a1', 1, 'opaque', ('h', 84), ['n']),
 'prop_post_boundary_wood_01': ('sheet_a1', 2, 'opaque', ('h', 58), ['n']),
 'prop_post_boundary_wood_02': ('sheet_a1', 3, 'opaque', ('h', 58), ['n']),
 'prop_campfire_cold_01': ('sheet_a1', 4, 'opaque', ('w', 64), ['n']),
 'prop_lean_to_01': ('sheet_a1', 5, 'opaque', ('w', 170), ['n']),
 'prop_torn_banner_01': ('sheet_a1', 6, 'opaque', ('h', 100), ['n']),
 # --- vegetation / ground litter (node rule for props, layer rule for scatter) ---
 'veg_fairy_flower_01': ('sheet_veg1', 0, 'opaque', ('w', 34), ['n', 'l']),
 'veg_fairy_flower_02': ('sheet_veg1', 1, 'opaque', ('w', 34), ['n', 'l']),
 'veg_fairy_flower_03': ('sheet_veg1', 2, 'soft', ('w', 38), ['n', 'l']),
 'veg_moss_clump_01': ('sheet_veg1', 3, 'opaque', ('w', 56), ['n', 'l']),
 'veg_moss_clump_02': ('sheet_veg1', 4, 'opaque', ('w', 60), ['n', 'l']),
 'veg_moss_clump_03': ('sheet_veg1', 5, 'opaque', ('w', 58), ['n', 'l']),
 'veg_moss_patch_01': ('sheet_veg1', 6, 'opaque', ('w', 70), ['n', 'l']),
 'veg_moss_patch_02': ('sheet_veg1', 7, 'opaque', ('w', 70), ['n', 'l']),
 'veg_moss_patch_03': ('sheet_veg1', 8, 'opaque', ('w', 72), ['n', 'l']),
 'veg_moss_patch_04': ('sheet_veg1', 9, 'opaque', ('w', 64), ['n', 'l']),
 'veg_mushroom_brown_01': ('sheet_veg2', 0, 'opaque', ('w', 30), ['n', 'l']),
 'veg_mushroom_brown_02': ('sheet_veg2', 1, 'opaque', ('w', 28), ['n', 'l']),
 'veg_mushroom_red_01': ('sheet_veg2', 2, 'opaque', ('w', 30), ['n', 'l']),
 'veg_mushroom_red_02': ('sheet_veg2', 3, 'opaque', ('w', 28), ['n', 'l']),
 'veg_reeds_01': ('sheet_veg2', 4, 'opaque', ('h', 58), ['n', 'l']),
 'veg_reeds_02': ('sheet_veg2', 5, 'opaque', ('h', 58), ['n', 'l']),
 'veg_thorn_L_01': ('sheet_veg2', 6, 'opaque', ('w', 100), ['n', 'l']),
 'veg_thorn_L_02': ('sheet_veg2', 7, 'opaque', ('w', 96), ['n', 'l']),
 'gnd_leaflitter_01': ('sheet_veg2', 8, 'opaque', ('w', 84), ['n', 'l']),
 'gnd_leaflitter_02': ('sheet_veg2', 9, 'opaque', ('w', 84), ['n', 'l']),
 # --- gimmicks / FX (fx_* are stored for later hooks; chest/symbol are wired as runtime entities) ---
 'treasure_chest_closed': ('sheet_fx', 0, 'opaque', ('w', 56), ['e:chest_closed']),
 'treasure_chest_glint_01': ('sheet_fx', 1, 'opaque', ('w', 56), []),
 'treasure_chest_glint_02': ('sheet_fx', 2, 'opaque', ('w', 56), []),
 'treasure_chest_glint_03': ('sheet_fx', 3, 'opaque', ('w', 56), []),
 'treasure_chest_glint_04': ('sheet_fx', 4, 'opaque', ('w', 56), []),
 'treasure_chest_open': ('sheet_fx', 5, 'opaque', ('w', 56), ['e:chest_open']),
 'moss_corruption_symbol': ('sheet_fx', 6, 'opaque', ('w', 84), ['e:symbol']),
 'fx_treasure_glint_01': ('sheet_fx', 7, 'soft', ('w', 40), []),
 'fx_treasure_glint_02': ('sheet_fx', 8, 'soft', ('w', 40), []),
 'fx_treasure_glint_03': ('sheet_fx', 9, 'soft', ('w', 40), []),
 'fx_treasure_glint_04': ('sheet_fx', 10, 'soft', ('w', 40), []),
 'fx_seal_01': ('sheet_fx', 11, 'soft', ('w', 90), []),
 'fx_seal_02': ('sheet_fx', 12, 'soft', ('w', 90), []),
 'fx_seal_03': ('sheet_fx', 13, 'soft', ('w', 90), []),
 'fx_seal_04': ('sheet_fx', 14, 'soft', ('w', 90), []),
}
# per-sheet component detection: alpha threshold, dilation (joins loose petals / glows), row-gap in px
R1 = [0, 256, 512, 768, 1024, 1280, 1536]
FX_CELLS = [(R1[i], 60, R1[i + 1], 360) for i in range(6)] + [(0, 380, 560, 660)] + [(x0, 400, x1, 640) for x0, x1 in [(560, 770), (770, 1030), (1030, 1240), (1240, 1500)]] \
         + [(x0, 620, x1, 990) for x0, x1 in [(30, 405), (405, 760), (760, 1130), (1130, 1530)]]
SHEETS = {'sheet_fx': dict(cells=FX_CELLS), 'sheet_a1': dict(thr=24, dil=7, gap=150), 'sheet_a2': dict(thr=24, dil=9, gap=150),
          'sheet_veg1': dict(thr=24, dil=8, gap=150), 'sheet_veg2': dict(thr=24, dil=8, gap=140), 'sheet_a3stones': dict(thr=24, dil=7, gap=150),
          'sheet_decals': dict(thr=24, dil=12, gap=150)}

def load(src, key): return np.array(Image.open(os.path.join(src, key + '.png')).convert('RGBA'))

def largest(a, thr=24):
    m = a[..., 3] > thr; lab, n = ndi.label(ndi.binary_dilation(m, iterations=6))
    if n <= 1: return a
    sizes = [((lab == i) & m).sum() for i in range(1, n + 1)]; keep = lab == (1 + int(np.argmax(sizes)))
    out = a.copy(); out[..., 3] = np.where(keep, a[..., 3], 0); return out

def split(a, cfg, minarea=1500):
    if 'cells' in cfg:   # fixed grid (sheets whose glows / sparkles join neighbouring sprites)
        res = []
        for x0, y0, x1, y1 in cfg['cells']:
            c = np.zeros_like(a); c[y0:y1, x0:x1] = a[y0:y1, x0:x1]; res.append(largest(c))
        return res
    m = a[..., 3] > cfg['thr']; lab, n = ndi.label(ndi.binary_dilation(m, iterations=cfg['dil']))
    items = []
    for i in range(1, n + 1):
        mm = (lab == i) & m
        if mm.sum() < minarea: continue
        ys, xs = np.where(mm); items.append(dict(i=i, x0=xs.min(), x1=xs.max() + 1, y0=ys.min(), y1=ys.max() + 1))
    items.sort(key=lambda t: (t['y0'] + t['y1']) / 2); rows = []
    for t in items:
        if rows and (t['y0'] + t['y1']) / 2 - rows[-1][-1]['_cy'] < cfg['gap']: rows[-1].append(t)
        else: rows.append([t])
        t['_cy'] = (t['y0'] + t['y1']) / 2
    out = []
    for r in rows: out += sorted(r, key=lambda t: t['x0'])
    res = []
    for t in out:
        reg = ndi.binary_dilation(lab == t['i'], iterations=2); c = a.copy(); c[..., 3] = np.where(reg, a[..., 3], 0); res.append(c)
    return res

def clean(a, mode):
    """opaque: hard alpha + edge-colour decontamination (kills the red/green matte fringe); soft: translucent FX untouched."""
    a = a.astype(float)
    if mode == 'soft': return a.astype(np.uint8)
    m = a[..., 3] > 128; lab, k = ndi.label(m)
    if k > 1:  # drop dust, keep every real part (> 0.3 % of the biggest)
        sizes = ndi.sum(m, lab, range(1, k + 1)); keep = [i + 1 for i, s in enumerate(sizes) if s > max(60, sizes.max() * 0.003)]; m = np.isin(lab, keep)
    m = ndi.binary_erosion(m, iterations=1); soft = ndi.gaussian_filter(m.astype(float), 0.7)
    inner = ndi.binary_erosion(m, iterations=3)
    idx = ndi.distance_transform_edt(~inner, return_distances=False, return_indices=True)
    rgb = a[..., :3]; rgb = np.where((m & ~inner)[..., None], rgb[idx[0], idx[1]], rgb)
    return np.dstack([rgb, soft * 255]).astype(np.uint8)

def crop_scale(a, size):
    ys, xs = np.where(a[..., 3] > 12); im = Image.fromarray(a).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    kind, v = size; k = (v * S) / (im.height if kind == 'h' else im.width)
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)

def seamless(img, out_px=384):
    """square centre crop of a delivered tile panel -> seamless tile via half-shift cross-blend."""
    w, h = img.size; s = min(w, h); img = img.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((out_px, out_px), Image.LANCZOS)
    a = np.array(img).astype(float); b = np.roll(np.roll(a, out_px // 2, 0), out_px // 2, 1)
    yy, xx = np.mgrid[0:out_px, 0:out_px] / (out_px - 1); wx = np.sin(np.pi * xx) ** 2; wy = np.sin(np.pi * yy) ** 2; wgt = (wx * wy)[..., None]   # 1 in the middle, 0 on the border
    return Image.fromarray((a * wgt + b * (1 - wgt)).astype(np.uint8))

def panels(tiles):
    """the 2x2 tile sheet has white gutters: find the four panels."""
    rgb = tiles[..., :3].astype(int); white = (rgb.min(2) > 245)
    cols = np.where(white[:, :].mean(0) > 0.97)[0]; rows = np.where(white.mean(1) > 0.97)[0]
    h, w = white.shape; xc = [c for c in cols if w * 0.3 < c < w * 0.7]; yc = [r for r in rows if h * 0.3 < r < h * 0.7]
    mx = int(np.mean(xc)) if xc else w // 2; my = int(np.mean(yc)) if yc else h // 2
    g = 8
    return [(0, 0, mx - g, my - g), (mx + g, 0, w, my - g), (0, my + g, mx - g, h), (mx + g, my + g, w, h)]

def main():
    args = sys.argv[1:]
    if not args: print(__doc__); sys.exit(2)
    src = args[0]; dry = '--dry-run' in args; out = os.path.join(ROOT, args[args.index('--out') + 1] if '--out' in args else 'img/field/moss/art')
    os.makedirs(out, exist_ok=True); cache = {}; made = {}
    for name, (key, sel, mode, size, kinds) in SPEC.items():
        if sel is None: a = largest(load(src, key))
        else:
            if key not in cache: cache[key] = split(load(src, key), SHEETS[key])
            if sel >= len(cache[key]): print('MISSING', name, key, sel, 'of', len(cache[key])); continue
            a = cache[key][sel]
        im = crop_scale(clean(a, mode), size); made[name] = im
        if not dry: im.save(os.path.join(out, name + '.png'), optimize=True)
        print('%-30s %4dx%-4d  world %5.1fx%-5.1f  %s' % (name, im.width, im.height, im.width / S, im.height / S, mode))
    # ground tiles
    t = np.array(Image.open(os.path.join(src, 'tiles.png')).convert('RGB')); img = Image.fromarray(t); pn = panels(np.dstack([t, t[..., :1]]))
    gt = {'ground_moss.png': seamless(img.crop(pn[0])), 'ground_mossdirt.png': seamless(img.crop(pn[2]))}
    if not dry:
        for n, im in gt.items(): im.save(os.path.join(out, n), optimize=True)
    print('ground panels', pn)
    if dry: return
    mp = os.path.join(ROOT, 'img/field/moss/manifest.json'); m = json.load(open(mp))
    m['node'] = [r for r in m['node'] if r.get('gen') != 'delivered_art']; m['layer'] = [r for r in m['layer'] if r.get('gen') != 'delivered_art']
    node, layer, ent = [], [], {}
    for name, (key, sel, mode, size, kinds) in SPEC.items():
        if name not in made: continue
        im = made[name]; rule = dict(file='art/%s.png' % name, w=round(im.width / S, 1), h=round(im.height / S, 1))
        if 'n' in kinds: node.append(dict(match='^%s$' % name, **rule, gen='delivered_art'))
        if 'l' in kinds: layer.append(dict(match='^%s$' % name, **rule, gen='delivered_art'))
        for k in kinds:
            if k.startswith('e:'): ent[k[2:]] = rule
    first = next(i for i, r in enumerate(m['node']) if r['match'].startswith('^prop_post_boundary_wood'))   # before the generated stand-ins
    m['node'][first:first] = node; m['layer'][0:0] = layer; m['entity'] = {**m.get('entity', {}), **ent}
    m['ground'] = {**m['ground'], 'grass': 'art/ground_moss.png', 'dirt': 'art/ground_mossdirt.png'}
    json.dump(m, open(mp, 'w'), ensure_ascii=False, indent=1)
    print('manifest: +%d node, +%d layer, entity %s' % (len(node), len(layer), sorted(ent)))

if __name__ == '__main__': main()
