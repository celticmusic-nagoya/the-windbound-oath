#!/usr/bin/env python3
"""DIRECTIVE-ART-01B preview: offline mock-up of rilde_in_aidan with the interior candidate tiles.

Reads the real map (data/maps/rilde_in_aidan.json), the real manifest sprites (img/field/moss/manifest.json, bottom-centre
anchors, w/h in world px) and composes at @2x. It does NOT modify the game; it is a visual-review aid for the user only.
Output: <out>/preview_aidan_house_before.png / _after.png (world 960x720 rendered at 1920x1440, then saved at 50%%).
"""
import argparse, json, pathlib, re
from PIL import Image, ImageDraw

R = pathlib.Path(__file__).resolve().parents[2]
S = 2  # @2x


def load_manifest():
    m = json.loads((R / 'img/field/moss/manifest.json').read_text(encoding='utf-8'))
    return m, R / m['base']


def sprite(m, base, asset):
    for r in m['node']:
        if re.search(r['match'], asset) and r.get('file'):
            im = Image.open(base / r['file']).convert('RGBA')
            w = r.get('w'); h = r.get('h')
            if w is None and h is None: w, h = im.width / 2, im.height / 2
            elif w is None: w = h * im.width / im.height
            elif h is None: h = w * im.height / im.width
            return im.resize((round(w * S), round(h * S)), Image.NEAREST)
    return None


def tile(canvas, im, x, y, w, h):
    for ty in range(y * S, (y + h) * S, im.height):
        for tx in range(x * S, (x + w) * S, im.width):
            cw = min(im.width, (x + w) * S - tx); ch = min(im.height, (y + h) * S - ty)
            canvas.alpha_composite(im.crop((0, 0, cw, ch)), (tx, ty))


def render(after, cand):
    d = json.loads((R / 'data/maps/rilde_in_aidan.json').read_text(encoding='utf-8'))
    W, H = int(d['world']['width']), int(d['world']['height'])
    cv = Image.new('RGBA', (W * S, H * S), (0x17, 0x11, 0x0d, 255)); dr = ImageDraw.Draw(cv)
    m, base = load_manifest()
    if not after:  # approximate the current procedural fills (colour + plank lines) for side-by-side reference
        for f in d['terrain']['fills']:
            for r in f['rects']:
                c = f['color']; dr.rectangle([r[0] * S, r[1] * S, (r[0] + r[2]) * S - 1, (r[1] + r[3]) * S - 1], fill=c)
                if f.get('pattern') == 'planks':
                    for x in range(r[0] - r[0] % 28, r[0] + r[2], 28):
                        if x >= r[0]: dr.rectangle([x * S, r[1] * S, x * S + 3, (r[1] + r[3]) * S - 1], fill=(30, 22, 34))
    else:
        C = lambda n: Image.open(cand / n).convert('RGBA')
        tile(cv, C('art01_int_wall_planks_01.png'), 48, 48, 864, 150)
        tile(cv, C('art01_int_floor_planks_01.png'), 48, 198, 864, 474)
        tile(cv, C('art01_int_baseboard_01.png'), 48, 188, 864, 12)
        tile(cv, C('art01_int_wallcap_left_01.png'), 0, 0, 48, 720)
        tile(cv, C('art01_int_wallcap_right_01.png'), 912, 0, 48, 720)
        tile(cv, C('art01_int_wallcap_bottom_01.png'), 48, 672, 864, 48)
        cv.alpha_composite(C('art01_int_wallcap_corner_sw_01.png'), (0, 672 * S)); cv.alpha_composite(C('art01_int_wallcap_corner_se_01.png'), (912 * S, 672 * S))
        tr = d['transitions'][0]['rect']; cv.alpha_composite(C('art01_int_door_threshold_01.png'), (int(tr['x']) * S, 672 * S))
    props = sorted(d['props'], key=lambda p: (p.get('z', 5), p['y']))
    for p in props:
        asset = p['asset']
        if after and asset == 'furn_doormat':
            im = Image.open(cand / 'art01_furn_doormat_woven_01.png').convert('RGBA')
        else:
            im = sprite(m, base, asset)
        if im is None: continue
        cv.alpha_composite(im, (round(p['x'] * S - im.width / 2), round(p['y'] * S - im.height)))
    sp = d['spawns']['points']['default']
    ai = Image.open(R / 'img/field/characters/aidan/aidan_idle_down.png').convert('RGBA')
    ah = 84 * S; ai = ai.resize((round(ai.width * ah / ai.height), ah), Image.LANCZOS)
    cv.alpha_composite(ai, (round(sp['x'] * S - ai.width / 2), round(sp['y'] * S - ai.height)))
    return cv


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--cand', default='docs/art/candidates/art-01'); ap.add_argument('--out', default='docs/art/candidates/art-01')
    a = ap.parse_args(); cand = R / a.cand; out = R / a.out
    for tag, after in (('before', False), ('after', True)):
        im = render(after, cand)
        im.resize((im.width // 2, im.height // 2), Image.NEAREST).convert('RGB').save(out / f'preview_aidan_house_{tag}.png')
        print('wrote', out / f'preview_aidan_house_{tag}.png')


if __name__ == '__main__':
    main()
