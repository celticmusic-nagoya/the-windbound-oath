#!/usr/bin/env python3
"""Draw the Moss Forest / Windward Cliffs map props as warm retro pixel art (stand-in quality, replaceable by hand-drawn art any time).
Each prop is composed on a coarse grid (1 art pixel = 2 world px = 4 image px), outlined, lightly dithered, bottom-centre anchored.
Writes img/field/moss/props/<asset>.png and registers the rules at the TOP of the manifest 'node' list (idempotent: rules tagged "gen":"make_props").
usage: python3 tools/moss/make_props.py [--no-manifest]   then: python3 tools/moss/check_assets.py"""
import json, os, random, sys
from PIL import Image, ImageDraw
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'img/field/moss/props'); MAN = os.path.join(ROOT, 'img/field/moss/manifest.json')
S = 2   # world px per art pixel
K = 2   # image px per world px
INK = (43, 33, 28, 255)
WOOD = [(124, 88, 52, 255), (154, 112, 66, 255), (184, 140, 86, 255)]      # dark, mid, light
STONE = [(98, 104, 106, 255), (132, 138, 138, 255), (166, 170, 164, 255)]
MOSS = [(52, 94, 44, 255), (82, 130, 58, 255), (122, 166, 76, 255)]
ROPE = (206, 176, 112, 255)

class Art:
    def __init__(s, wpx, hpx, seed):
        s.w, s.h = wpx // S, hpx // S; s.sh = []; s.px = [[None] * s.w for _ in range(s.h)]; s.r = random.Random(seed)
    def put(s, x, y, c):
        if 0 <= x < s.w and 0 <= y < s.h: s.px[y][x] = c
    def rect(s, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): s.put(x, y, c)
    def poly_rows(s, rows, c):   # rows: {y: (x0, x1)}
        for y, (a, b) in rows.items():
            for x in range(a, b + 1): s.put(x, y, c)
    def outline(s):
        o = [[None] * s.w for _ in range(s.h)]
        for y in range(s.h):
            for x in range(s.w):
                if s.px[y][x] is None and any(0 <= x + dx < s.w and 0 <= y + dy < s.h and s.px[y + dy][x + dx] is not None for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): o[y][x] = INK
        for y in range(s.h):
            for x in range(s.w):
                if o[y][x]: s.px[y][x] = o[y][x]
    def shadow(s, cx, y, rw):   # soft ground shadow under the prop (drawn before the body)
        for dx in range(-rw, rw + 1):
            for dy in (-1, 0):
                if abs(dx) + abs(dy) * 2 <= rw + 1: s.sh.append((cx + dx, y + dy))   # drawn after the outline so it stays a soft blob
    def png(s, path):
        im = Image.new('RGBA', (s.w * S * K, s.h * S * K), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for (x, y) in s.sh:
            if 0 <= x < s.w and 0 <= y < s.h and s.px[y][x] is None: d.rectangle([x * S * K, y * S * K, (x + 1) * S * K - 1, (y + 1) * S * K - 1], fill=(30, 40, 24, 90))
        for y in range(s.h):
            for x in range(s.w):
                c = s.px[y][x]
                if c: d.rectangle([x * S * K, y * S * K, (x + 1) * S * K - 1, (y + 1) * S * K - 1], fill=c)
        im.save(path); return im.size

def wood_plank(a, x0, y0, x1, y1):
    a.rect(x0, y0, x1, y1, WOOD[1]); a.rect(x0, y0, x1, y0, WOOD[2]); a.rect(x0, y1, x1, y1, WOOD[0])
    for x in range(x0 + 2, x1, 5): a.put(x, (y0 + y1) // 2, WOOD[0])

def post(w=22, h=58):
    a = Art(w, h, 1); cx = a.w // 2; bot = a.h - 2
    a.shadow(cx, bot + 1, 5)
    a.rect(cx - 2, 5, cx + 2, bot, WOOD[1]); a.rect(cx - 2, 5, cx - 2, bot, WOOD[2]); a.rect(cx + 2, 5, cx + 2, bot, WOOD[0])
    a.rect(cx - 2, 3, cx + 2, 4, WOOD[2]); a.rect(cx - 1, 2, cx + 1, 2, WOOD[2])             # rounded top
    for y in range(9, bot, 4): a.put(cx, y, WOOD[0])
    a.rect(0, 11, a.w - 1, 12, WOOD[2]); a.rect(0, 13, a.w - 1, 13, WOOD[0])                 # rail stubs (joined with neighbours)
    a.rect(cx - 3, 18, cx + 3, 19, ROPE)
    a.rect(cx - 3, bot - 1, cx + 3, bot, MOSS[1]); a.put(cx - 2, bot, MOSS[2]); a.put(cx + 3, bot - 1, MOSS[2])
    a.outline(); return a

def bench(w=84, h=46):
    a = Art(w, h, 2); cx = a.w // 2; bot = a.h - 2
    a.shadow(cx, bot + 1, 17)
    for lx in (cx - 17, cx + 15):   # legs
        a.rect(lx, 14, lx + 2, bot, WOOD[0]); a.rect(lx, 14, lx, bot, WOOD[1])
    wood_plank(a, cx - 20, 11, cx + 20, 14)      # seat
    wood_plank(a, cx - 20, 4, cx + 20, 6)        # back rail
    wood_plank(a, cx - 20, 7, cx + 20, 9)
    a.rect(cx - 19, 5, cx - 17, 14, WOOD[0]); a.rect(cx + 17, 5, cx + 19, 14, WOOD[0])      # back uprights
    for x in (cx - 12, cx + 6, cx + 14): a.put(x, bot, MOSS[1]); a.put(x + 1, bot - 1, MOSS[2])
    a.outline(); return a

def signpost(w=34, h=80):
    a = Art(w, h, 3); cx = a.w // 2; bot = a.h - 2
    a.shadow(cx, bot + 1, 5)
    a.rect(cx - 1, 6, cx + 1, bot, WOOD[1]); a.rect(cx - 1, 6, cx - 1, bot, WOOD[2]); a.rect(cx + 1, 6, cx + 1, bot, WOOD[0])
    a.poly_rows({3: (cx - 1, cx + 1), 4: (cx - 2, cx + 2), 5: (cx - 2, cx + 2)}, WOOD[1])
    # two arrow boards
    for y0, x0, x1, left in ((9, cx - 7, cx + 6, True), (19, cx - 6, cx + 7, False)):
        wood_plank(a, x0, y0, x1, y0 + 5)
        tip = x0 - 2 if left else x1 + 2
        for i, yy in enumerate(range(y0, y0 + 6)):
            d = abs(yy - (y0 + 2.5)); n = int(2 - d * .8)
            for t in range(max(0, n)): a.put(tip + (t if left else -t), yy, WOOD[1])
        for x in range(x0 + 2, x1 - 1, 3): a.put(x, y0 + 2, INK)      # text scratches
    a.rect(cx - 1, bot - 1, cx + 1, bot, MOSS[1]); a.put(cx - 2, bot, MOSS[2]); a.put(cx + 2, bot - 1, MOSS[0])
    a.outline(); return a

def mossy_stone(w, h, seed, taper=.7, chip=True):
    a = Art(w, h, seed); r = a.r; cx = a.w // 2; bot = a.h - 2; top = 3
    a.shadow(cx, bot + 1, a.w // 3)
    rows = {}
    for y in range(top, bot + 1):
        t = (y - top) / max(1, bot - top)                              # 0 top .. 1 bottom
        half = (a.w / 2 - 2) * (taper + (1 - taper) * t) * (0.55 + 0.45 * min(1, (y - top) / 4.0)) 
        wob = r.randint(-1, 1) if y % 3 == 0 else 0
        rows[y] = (int(cx - half + wob), int(cx + half - wob))
    for y, (x0, x1) in rows.items():
        for x in range(x0, x1 + 1):
            u = (x - x0) / max(1, x1 - x0)
            c = STONE[2] if u < .25 else STONE[1] if u < .7 else STONE[0]
            if r.random() < .06: c = STONE[0 if c != STONE[0] else 1]
            a.put(x, y, c)
    for _ in range(max(2, a.w * a.h // 140)):   # cracks
        x = r.randint(rows[top + 4][0] + 2, rows[top + 4][1] - 2); y = r.randint(top + 4, bot - 6)
        for k in range(r.randint(3, 6)): a.put(x + (k % 2), y + k, STONE[0])
    for y in range(bot - 5, bot + 1):    # moss on the foot and a cap on top
        x0, x1 = rows[y]
        for x in range(x0, x1 + 1):
            if r.random() < .55: a.put(x, y, MOSS[r.randint(0, 2)])
    x0, x1 = rows[top + 1]
    for x in range(x0 + 1, x1):
        if r.random() < .6: a.put(x, top + 1, MOSS[1 + r.randint(0, 1)])
    for _ in range(a.w // 3): a.put(r.randint(rows[top + 8][0], rows[top + 8][1]), r.randint(top + 6, bot - 8), MOSS[r.randint(0, 2)])
    a.outline(); return a

def broken_fence(w=124, h=44):
    a = Art(w, h, 7); bot = a.h - 2
    a.shadow(a.w // 2, bot + 1, 28)
    xs = [6, 22, 40, 56]
    for i, x in enumerate(xs):
        top = 6 + (i * 5) % 9
        a.rect(x, top, x + 2, bot, WOOD[1]); a.rect(x, top, x, bot, WOOD[2]); a.rect(x + 2, top, x + 2, bot, WOOD[0])
    wood_plank(a, 5, 10, 30, 13)
    wood_plank(a, 38, 16, 58, 19)                 # a sagging rail
    for k in range(6): a.put(32 + k, 12 + k // 2, WOOD[0])    # broken end
    a.rect(30, bot - 2, 44, bot - 1, WOOD[0]); a.rect(46, bot - 3, 60, bot - 2, WOOD[1])    # fallen plank
    for x in (12, 26, 48, 54): a.put(x, bot, MOSS[1]); a.put(x + 1, bot - 1, MOSS[2])
    a.outline(); return a

def marker_fork(w=40, h=84):
    a = signpost(w, h); return a

ASSETS = {
    'prop_post_boundary_wood': (post, 22, 58),
    'prop_bench_view': (bench, 84, 46),
    'prop_marker_signpost': (signpost, 34, 80),
    'prop_marker_fork': (marker_fork, 40, 84),
    'prop_fence_broken': (broken_fence, 124, 44),
    'anc_standing_L': (lambda w, h: mossy_stone(w, h, 11, .62), 64, 150),
    'anc_boundary_stone': (lambda w, h: mossy_stone(w, h, 12, .8), 52, 84),
}
def main():
    os.makedirs(OUT, exist_ok=True); rules = []
    for name, (fn, w, h) in ASSETS.items():
        a = fn(w, h); size = a.png(os.path.join(OUT, name + '.png'))
        assert size == (w * K, h * K), (name, size)
        rules.append({'match': '^' + name, 'file': 'props/%s.png' % name, 'w': w, 'h': h, 'gen': 'make_props'})
        print('wrote %-26s %3dx%-3d world px (%dx%d image)' % (name, w, h, size[0], size[1]))
    if '--no-manifest' in sys.argv: return
    m = json.load(open(MAN, encoding='utf-8'))
    m['node'] = [r for r in m['node'] if r.get('gen') != 'make_props']
    m['node'][0:0] = rules
    open(MAN, 'w', encoding='utf-8').write(json.dumps(m, ensure_ascii=False, indent=1))
    print('manifest: %d rules registered at the top of node[]' % len(rules))
if __name__ == "__main__": main()
