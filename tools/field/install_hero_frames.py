#!/usr/bin/env python3
"""Hero (Aidan / Fiona) field-art intake: take delivered hand-painted / AI-generated frames at ANY canvas size and normalise them
to the runtime contract (one shared scale, feet on one anchor, one canvas), then regenerate the frame manifest.
usage: install_hero_frames.py <src_dir> --hero fiona|aidan [--height-world N] [--dot N] [--out-dir DIR] [--js-out FILE] [--dry-run]

Source names (1 frame = 1 transparent RGBA PNG, 4 directions down/left/right/up):
    <hero>_idle_<dir>.png        <hero>_walk_<dir>_01.png .. _06.png   (4-6 walk frames per direction, contiguous, same count for every direction)
Normalisation (so art of any size drops in and the character neither jumps nor drifts):
  * ONE scale for the whole hero: idle_down's body height (alpha>16 bbox) is mapped to --height-world (fiona 46 / aidan 44) world px.
  * Feet: each frame's lowest opaque row -> anchor row; per direction the horizontal feet centre of idle -> anchor column (walk frames share that shift: no sway jitter).
  * --dot N: snap to an N-world-px dot grid (1 dot = 2px recommended) with nearest-neighbour, for pixel-art deliveries.
  * Validates RGBA + real transparency (>=15 % transparent pixels - not a baked backdrop), contiguous frames, equal walk counts, stray background corners.
Output: <out-dir>/<hero>_*.png (default: the runtime folders) + the manifest js (default: js/field/<hero>-field-assets.js). Existing art is only overwritten without --dry-run."""
import os, sys, re, json
import numpy as np
from PIL import Image
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
HEROES = {
    'fiona': dict(canvas=(512, 640), anchor=(256, 600), scale=0.1, height=46, out='img/field/moss/real/fiona/', js='js/field/fiona-field-assets.js', walk=(4, 6)),
    'aidan': dict(canvas=(768, 768), anchor=(384, 700), scale=0.0625, height=44, out='img/field/characters/aidan/', js='js/field/aidan-field-assets.js', walk=(4, 6)),
}
DIRS = ['down', 'left', 'right', 'up']
def scan(src, hero):
    found = {'idle': {}, 'walk': {d: {} for d in DIRS}}
    for f in sorted(os.listdir(src)):
        m = re.fullmatch(r'%s_idle_(down|left|right|up)\.png' % hero, f)
        if m: found['idle'][m.group(1)] = f; continue
        m = re.fullmatch(r'%s_walk_(down|left|right|up)_(\d{2})\.png' % hero, f)
        if m: found['walk'][m.group(1)][int(m.group(2))] = f
    return found
def load(path):
    im = Image.open(path)
    return im.convert('RGBA') if im.mode != 'RGBA' else im, im.mode
def bbox(a, t=16):
    ys, xs = np.where(a[..., 3] > t)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else None
def main():
    args = sys.argv[1:]
    if len(args) < 3 or '--hero' not in args: print(__doc__); sys.exit(2)
    src = args[0]; hero = args[args.index('--hero') + 1]
    if hero not in HEROES: print('unknown hero', hero); sys.exit(2)
    cfg = HEROES[hero]; opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
    height = float(opt('--height-world', cfg['height'])); dot = int(opt('--dot', 0)); dry = '--dry-run' in args
    outdir = os.path.join(ROOT, opt('--out-dir', cfg['out'])) if not os.path.isabs(opt('--out-dir', cfg['out'])) else opt('--out-dir'); js_out = opt('--js-out', os.path.join(ROOT, cfg['js']))
    W, H = cfg['canvas']; ax, ay = cfg['anchor']; sc = cfg['scale']
    found = scan(src, hero); problems = []
    for d in DIRS:
        if d not in found['idle']: problems.append('missing %s_idle_%s.png' % (hero, d))
    counts = {d: sorted(found['walk'][d]) for d in DIRS}
    for d in DIRS:
        n = counts[d]
        if n != list(range(1, len(n) + 1)): problems.append('walk %s: frames must be 01..NN without gaps, got %s' % (d, n))
        if not cfg['walk'][0] <= len(n) <= cfg['walk'][1]: problems.append('walk %s: %d frames (need %d-%d)' % (d, len(n), *cfg['walk']))
    if len({len(counts[d]) for d in DIRS}) > 1: problems.append('every direction needs the same number of walk frames: %s' % {d: len(counts[d]) for d in DIRS})
    if problems: print('\n'.join('ERROR ' + p for p in problems)); sys.exit(1)
    imgs = {}
    for d in DIRS:
        imgs['idle_' + d] = os.path.join(src, found['idle'][d])
        for n, f in found['walk'][d].items(): imgs['walk_%s_%02d' % (d, n)] = os.path.join(src, f)
    arrs = {}
    for k, p in imgs.items():
        im, mode = load(p); a = np.array(im)
        if mode != 'RGBA': problems.append('%s: %s, must be transparent RGBA' % (k, mode)); continue
        if (a[..., 3] == 0).mean() < .15: problems.append('%s: only %.0f%% transparent - looks like a baked backdrop, not a cut-out' % (k, 100 * (a[..., 3] == 0).mean())); continue
        if bbox(a) is None: problems.append('%s: fully transparent' % k); continue
        corners = [a[0, 0, 3], a[0, -1, 3], a[-1, 0, 3], a[-1, -1, 3]]
        if max(corners) > 16: problems.append('%s: opaque canvas corner (background fragment?)' % k)
        arrs[k] = a
    if problems: print('\n'.join('ERROR ' + p for p in problems)); sys.exit(1)
    x0, y0, x1, y1 = bbox(arrs['idle_down']); k = (height / sc) / (y1 - y0)         # source px -> canvas px (one scale for the whole hero)
    # horizontal feet centre of each direction's idle: lowest 6 % rows of the body
    feet_x = {}
    for d in DIRS:
        a = arrs['idle_' + d]; bx0, by0, bx1, by1 = bbox(a); band = a[max(by0, int(by1 - (by1 - by0) * .06)):by1, :, 3] > 16
        xs = np.where(band.any(0))[0]; feet_x[d] = (xs.min() + xs.max() + 1) / 2
    results = {}; report = []
    for name, a in arrs.items():
        d = name.split('_')[1] if name.startswith('walk') else name.split('_')[1]; d = name.split('_')[1] if name.startswith('idle') else name.split('_')[1]
        bx0, by0, bx1, by1 = bbox(a); crop = Image.fromarray(a[by0:by1, bx0:bx1])
        nw, nh = max(1, round(crop.width * k)), max(1, round(crop.height * k)); crop = crop.resize((nw, nh), Image.LANCZOS if not dot else Image.BOX)
        if dot:
            cell = max(1, round(dot / sc)); sw, sh = max(1, nw // cell), max(1, nh // cell)
            crop = crop.resize((sw, sh), Image.BOX).resize((sw * cell, sh * cell), Image.NEAREST); nw, nh = crop.size
        canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        px = round(ax - (feet_x[d] - bx0) * k); py = ay - nh       # feet row (bottom of bbox) on the anchor row
        canvas.alpha_composite(crop, (max(px, 0), max(py, 0)))
        if px < 0 or py < 0 or px + nw > W: report.append('WARN %s: scaled art leaves the %dx%d canvas (%d,%d %dx%d) - some pixels cut' % (name, W, H, px, py, nw, nh))
        results[name] = canvas
    frames = {}
    for name, im in results.items():
        a = np.array(im); bx0, by0, bx1, by1 = bbox(a)
        frames['%s_%s' % (hero, name)] = {'path': (opt('--path-prefix') or cfg['out']) + '%s_%s.png' % (hero, name), 'width': W, 'height': H, 'bounds': [bx0, by0, bx1 - bx0, by1 - by0], 'anchor': [ax, ay], 'scale': sc}
    print('ok   %s: %d frames (walk %d per direction), scale %.4f world px/src px -> canvas %.3f, dot=%s' % (hero, len(frames), len(counts['down']), k * sc, k, dot or 'off'))
    for r in report: print(r)
    if dry: print('dry run: nothing written'); return
    os.makedirs(outdir, exist_ok=True)
    for name, im in results.items(): im.save(os.path.join(outdir, '%s_%s.png' % (hero, name)), optimize=True)
    body = json.dumps(frames, indent=1)
    if hero == 'fiona':
        js = '/* Fiona field frames (tools/field/install_hero_frames.py or make_fiona.py): 4 directions x (idle + walk). Same shape as AidanFieldAssets.frames. */\nwindow.FionaFieldAssets = Object.freeze({frames: Object.freeze(' + body + ')});\n'
    else:
        js = '/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */\n(function () {\n  "use strict";\n  if (!window.WINDBOUND_DEV) return;\n  const frames = ' + body + ';\n  Object.values(frames).forEach(Object.freeze);\n  window.AidanFieldAssets = Object.freeze({frames:Object.freeze(frames)});\n})();\n'
    open(js_out, 'w', encoding='utf-8').write(js); print('wrote', len(frames), 'PNGs ->', outdir, 'and', js_out)
main()
