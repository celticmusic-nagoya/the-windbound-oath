#!/usr/bin/env python3
"""Prepare the Lind village art for the Moss-runtime Rilde Village maps (img/field/moss/rilde/).
 - lind/<id>.png   : every Lind object cropped to its visible pixels and downscaled to 2 image px per world px (the originals are 1536x1024, far too heavy to load ~50 of)
 - ruin/<id>.png   : the same buildings after the attack (burnt colours, collapsed roof, charred rafters, rubble) - generated from the peaceful art, so a house
                     is still recognisably THE house
 - npc/<id>_*.png  : villager idle / walk frames, same canvas rules (walkers anchor at the visible feet)
 - landmark/ , animals/
 Writes tools/moss/rilde_assets.json (sizes/anchors) which tools/moss/build_rilde_village.py turns into manifest rules.
 usage: python3 tools/moss/prepare_rilde_lind.py      (idempotent; needs node for the layout export)"""
import json, os, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'img/field/moss/rilde')
LIND = os.path.join(ROOT, 'img/field/lind')
K = 2   # image px per world px (1 world px = half an art dot, like every other moss asset)

def layout():
    return json.loads(subprocess.check_output(['node', os.path.join(ROOT, 'tools/moss/export_lind_layout.js')]))

def crop_alpha(im):
    bb = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(bb) if bb else im

def save_scaled(im, path, wworld, hworld):
    im = im.resize((max(1, round(wworld * K)), max(1, round(hworld * K))), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True); im.save(path); return im

# ------------------------------------------------------------------ ruins
def noise1d(n, rnd, octaves=((40, .5), (14, .3), (5, .2))):
    out = np.zeros(n)
    for step, amp in octaves:
        pts = [rnd.random() for _ in range(n // step + 3)]
        for x in range(n):
            i = x // step; t = (x % step) / step; t = t * t * (3 - 2 * t)
            out[x] += amp * (pts[i] * (1 - t) + pts[i + 1] * t)
    return out

def ruinify(im, seed, kind='house'):
    """Burnt colours + collapsed top + charred rafters + rubble. Same canvas size as the input."""
    rnd = random.Random(seed); W, H = im.size
    a = np.asarray(im.convert('RGBA'), dtype=np.float32).copy()
    # 1) collapse: a jagged cut line, deeper on one side (the roof fell in)
    n = noise1d(W, rnd)
    side = rnd.choice([-1, 1]); xs = np.linspace(0, 1, W)
    depth = {'house': .78, 'barn': .62, 'shed': .50, 'tree': .0, 'low': .22}.get(kind, .5)
    ramp = (0.30 + 0.70 * (1 - xs if side < 0 else xs) ** 1.3)
    cut = (depth * ramp * (0.7 + 0.6 * n)) * H
    for x in range(W):
        c = int(cut[x]); a[:c, x, 3] = 0
        if 0 < c < H: a[c:c + 3, x, 3] *= .5   # slightly feathered edge
    # 2) colours: desaturate, darken, soot toward the cut edge, burn blotches
    lum = (a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114)[..., None]
    rgb = a[..., :3] * .38 + lum * .62
    rgb *= np.array([.58, .50, .47], dtype=np.float32)
    yy = np.linspace(0, 1, H)[:, None, None]
    rgb *= (0.62 + 0.38 * yy)                                  # blacker toward the (burnt) top
    blot = np.zeros((H, W), dtype=np.float32)
    for _ in range(60 if kind != 'low' else 25):
        cx, cy, r = rnd.randrange(W), rnd.randrange(H), rnd.randrange(max(6, W // 40), max(14, W // 9))
        y0, y1, x0, x1 = max(0, cy - r), min(H, cy + r), max(0, cx - r), min(W, cx + r)
        gy, gx = np.ogrid[y0:y1, x0:x1]; d = ((gx - cx) ** 2 + (gy - cy) ** 2) / float(r * r)
        blot[y0:y1, x0:x1] = np.maximum(blot[y0:y1, x0:x1], np.clip(1 - d, 0, 1) * rnd.uniform(.35, .75))
    rgb *= (1 - blot[..., None] * .7)
    # ember glow just under the collapsed edge
    glow = np.zeros((H, W), dtype=np.float32)
    for x in range(W):
        c = int(cut[x])
        if 0 < c < H - 4: glow[c:min(H, c + 7), x] = np.linspace(.5, 0, min(H, c + 7) - c)
    flick = np.asarray([rnd.random() for _ in range(W)], dtype=np.float32)[None, :, None]
    rgb += glow[..., None] * np.array([150, 62, 14], dtype=np.float32) * (.4 + .6 * flick)
    a[..., :3] = np.clip(rgb, 0, 255)
    out = Image.fromarray(a.astype(np.uint8), 'RGBA'); d = ImageDraw.Draw(out)
    # 3) charred rafters sticking up from the cut
    al = np.asarray(out.getchannel('A'))
    for _ in range(max(3, W // 55)):
        x = rnd.randrange(8, W - 8); col = np.nonzero(al[:, x] > 128)[0]
        if not len(col): continue
        c = int(col[0]); L = rnd.randrange(int(H * .07), int(H * .2)); ang = rnd.uniform(-.7, .7); wd = max(3, W // 90)
        x2, y2 = x + L * np.sin(ang), c - L * np.cos(ang)
        d.line([(x, c + 5), (x2, y2)], fill=(34, 24, 20, 255), width=wd)
        d.line([(x + 1, c + 5), (x2 + 1, y2)], fill=(58, 38, 28, 255), width=max(1, wd // 3))
    # 4) rubble along the foot (stones, broken planks), kept inside the original width so anchors stay put
    base = H - 2
    for _ in range(max(10, W // 14)):
        cx = rnd.randrange(6, W - 6); r = rnd.randrange(max(4, W // 60), max(9, W // 22)); cy = base - rnd.randrange(0, max(3, H // 14))
        col = rnd.choice([(88, 82, 76), (70, 64, 60), (104, 94, 84), (54, 46, 42)]) + (255,)
        pts = [(cx - r, cy), (cx - r * .6, cy - r * .8), (cx + r * .3, cy - r * .9), (cx + r, cy - r * .2), (cx + r * .8, cy)]
        d.polygon(pts, fill=col, outline=(30, 24, 22, 255))
    for _ in range(max(4, W // 40)):
        x = rnd.randrange(10, W - 30); y = base - rnd.randrange(2, max(4, H // 10)); L = rnd.randrange(14, max(18, W // 7)); ang = rnd.uniform(-.5, .5)
        d.line([(x, y), (x + L * np.cos(ang), y - L * np.sin(ang))], fill=(40, 28, 22, 255), width=max(3, W // 100))
    return out

def burnt_tree(im, seed):
    """Charred trunk-and-branches silhouette: keep the trunk column, drop most of the foliage."""
    rnd = random.Random(seed); W, H = im.size
    a = np.asarray(im, dtype=np.float32).copy()
    lum = (a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114)
    brown = (a[..., 0] > a[..., 1] * .86) & (lum < 175)         # trunk pixels (brown), foliage is green-dominant
    a[..., 3] = np.where(brown, a[..., 3], 0)
    a[..., :3] = np.array([38, 28, 24], dtype=np.float32) + lum[..., None] * .18
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    return crop_alpha(out)

# ------------------------------------------------------------------ main
BUILDINGS = {'lind_elder_house': 'house', 'lind_inn': 'house', 'lind_aidan_house': 'house', 'lind_item_shop': 'house', 'lind_house_01': 'house', 'lind_house_02': 'house',
             'lind_house_03': 'house', 'lind_house_04': 'house', 'lind_barn': 'barn', 'lind_storage': 'shed', 'lind_cowshed': 'shed', 'lind_pigsty': 'shed', 'lind_chicken_coop': 'shed',
             'train_shed': 'shed', 'lind_haystack': 'low', 'lind_cart': 'low', 'lind_fence': 'low', 'pig_fence': 'low', 'chicken_fence': 'low', 'train_fence_west': 'low', 'train_fence_east': 'low',
             'train_gate': 'low', 'lind_laundry': 'low', 'lind_sign': 'low', 'train_weapon_rack': 'low', 'lind_farm_tools': 'low', 'lind_orchard_apple': 'tree', 'lind_tree_01': 'tree', 'train_target': 'low'}

def main():
    L = layout(); meta = {'objects': {}, 'ruin': {}, 'npc': {}, 'landmark': {}, 'animals': {}}
    seen = {}
    for i, o in enumerate(L['objects']):
        src = os.path.join(ROOT, o['path'])
        if not os.path.exists(src): print('missing', src); continue
        base = o.get('boundsId') or o['id']   # fence variants share the source file
        key = os.path.basename(o['path'])
        if key not in seen: seen[key] = crop_alpha(Image.open(src).convert('RGBA'))
        im = seen[key]
        wworld, hworld = o['width'], o['height']
        out = save_scaled(im, os.path.join(OUT, 'lind', o['id'] + '.png'), wworld, hworld)
        meta['objects'][o['id']] = {'file': 'rilde/lind/%s.png' % o['id'], 'w': wworld, 'h': hworld}
        kind = BUILDINGS.get(o['id'])
        if kind:
            if kind == 'tree': r = burnt_tree(out, 1000 + i)
            else: r = ruinify(out, 1000 + i, kind)
            os.makedirs(os.path.join(OUT, 'ruin'), exist_ok=True); r.save(os.path.join(OUT, 'ruin', o['id'] + '.png'))
            meta['ruin'][o['id']] = {'file': 'rilde/ruin/%s.png' % o['id'], 'w': wworld, 'h': hworld if kind != 'tree' else hworld * r.size[1] / out.size[1], 'wReal': wworld * (r.size[0] / out.size[0]) if kind == 'tree' else wworld}
    # wind stone (normal = wind blowing; off = the night the wind stopped)
    ws = L['windStone']
    for st, fn in (('normal', 'lind_wind_stone.png'), ('off', 'lind_wind_stone_off.png')):
        im = crop_alpha(Image.open(os.path.join(LIND, 'landmarks', fn)).convert('RGBA'))
        save_scaled(im, os.path.join(OUT, 'landmark', 'wind_stone_%s.png' % st), ws['width'], ws['height'])
        meta['landmark']['wind_stone_' + st] = {'file': 'rilde/landmark/wind_stone_%s.png' % st, 'w': ws['width'], 'h': ws['height']}
    # animals (static idle in the pens)
    for name, wd in (('cow', 72), ('pig', 43), ('chicken', 24)):
        im = crop_alpha(Image.open(os.path.join(LIND, 'animals', name + '_idle.png')).convert('RGBA'))
        h = wd * im.size[1] / im.size[0]; save_scaled(im, os.path.join(OUT, 'animals', name + '.png'), wd, h)
        meta['animals'][name] = {'file': 'rilde/animals/%s.png' % name, 'w': wd, 'h': round(h, 1)}
    # villagers: keep each frame's full canvas (shared by idle/walk) scaled so the idle's visible height = registry height
    for n in L['npcs']:
        d = os.path.join(LIND, 'npc', n['sprite'])
        idle = os.path.join(d, n['id'] + '_idle.png')
        if not os.path.exists(idle): continue
        im0 = Image.open(idle).convert('RGBA'); bb = im0.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
        W, H = im0.size; l, t, r, b = bb; s = n['height'] / (b - t)          # world px per source px
        ww, hh = W * s, H * s
        frames = []
        if n['id'] == 'boy_swordsman': pat = n['id'] + '_attack_%02d.png'
        else: pat = n['id'] + '_walk_%02d.png'
        for k in range(1, 9):
            f = os.path.join(d, pat % k)
            if os.path.exists(f): frames.append(f)
        os.makedirs(os.path.join(OUT, 'npc'), exist_ok=True)
        im0.resize((round(ww * K), round(hh * K)), Image.LANCZOS).save(os.path.join(OUT, 'npc', n['id'] + '_idle.png'))
        cnt = 0
        for k, f in enumerate(frames, 1):
            im = Image.open(f).convert('RGBA')
            if im.size != (W, H): continue                                  # only canvases that match the idle (no legacy sheets)
            im.resize((round(ww * K), round(hh * K)), Image.LANCZOS).save(os.path.join(OUT, 'npc', '%s_f%02d.png' % (n['id'], k))); cnt += 1
        meta['npc'][n['id']] = {'idle': 'rilde/npc/%s_idle.png' % n['id'], 'frames': cnt, 'frame': 'rilde/npc/%s_f{n}.png' % n['id'], 'w': round(ww, 2), 'h': round(hh, 2),
                                'dx': round(((l + r) / 2 - W / 2) * s, 2), 'dy': round((H - b) * s, 2), 'talk': n['talk'], 'label': n['label'], 'foot': n['footY'], 'x': n['x'], 'height': n['height']}
    json.dump(meta, open(os.path.join(ROOT, 'tools/moss/rilde_assets.json'), 'w'), ensure_ascii=False, indent=1)
    print('objects %d  ruins %d  npcs %d  -> %s' % (len(meta['objects']), len(meta['ruin']), len(meta['npc']), OUT))

if __name__ == '__main__': main()
