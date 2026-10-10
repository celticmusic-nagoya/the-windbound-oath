#!/usr/bin/env python3
"""Rilde Village interior furniture + post-attack debris, drawn as warm earth-tone Celtic-fantasy pixel art (stand-in quality, replaceable any time).
Spec (same as every moss asset): 1 art dot = 2 world px = 4 image px, transparent RGBA, feet at the bottom-centre of the image (props), 'decal' items lie flat on the floor.
Writes img/field/moss/rilde/furn/<name>.png and tools/moss/rilde_furn.json {name:{file,w,h,kind}} (consumed by build_rilde_village.py -> manifest rules).
usage: python3 tools/moss/make_rilde_art.py [--sheet out.png]"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from make_props import Art, WOOD, STONE, MOSS, ROPE, INK, wood_plank, S, K
from PIL import Image
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'img/field/moss/rilde/furn')
G = lambda *a: tuple(a) + (255,)
GREEN = [G(44, 82, 54), G(70, 116, 72), G(104, 152, 92)]
RED = [G(104, 44, 38), G(148, 68, 50), G(188, 100, 66)]
LINEN = [G(186, 172, 146), G(222, 210, 184), G(246, 238, 216)]
IRON = [G(58, 58, 66), G(96, 98, 106), G(142, 144, 150)]
GOLD = [G(160, 120, 44), G(214, 172, 70), G(248, 216, 118)]
FIRE = [G(196, 56, 20), G(240, 128, 30), G(255, 214, 84)]
CLAY = [G(120, 74, 50), G(158, 100, 66), G(196, 130, 86)]
BLUE = [G(52, 78, 120), G(80, 112, 160), G(124, 156, 200)]
ASH = [G(30, 28, 30), G(52, 48, 48), G(82, 76, 72)]
ITEMS = {}   # name -> (fn, w, h, kind)
def item(w, h, kind='prop'):
    def deco(fn): ITEMS[fn.__name__] = (fn, w, h, kind); return fn
    return deco
def ell(a, cx, cy, rx, ry, c):
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if ((x - cx) / max(rx, .5)) ** 2 + ((y - cy) / max(ry, .5)) ** 2 <= 1.0: a.put(x, y, c)
def panel(a, x0, y0, x1, y1, c=WOOD, step=5):   # vertical planks, lit top edge, shaded foot
    a.rect(x0, y0, x1, y1, c[1]); a.rect(x0, y0, x1, y0, c[2]); a.rect(x0, y1, x1, y1, c[0])
    for x in range(x0 + step, x1, step): a.rect(x, y0 + 1, x, y1 - 1, c[0])
def box(a, x0, y0, x1, y1, top, c=WOOD, step=6):   # front face + top surface of height `top`
    panel(a, x0, y0 + top, x1, y1, c, step); a.rect(x0, y0, x1, y0 + top - 1, c[2]); a.rect(x0, y0 + top - 1, x1, y0 + top - 1, c[0]); a.rect(x0, y0, x0, y1, c[2]); a.rect(x1, y0 + top, x1, y1, c[0])
def new(w, h, seed): return Art(w, h, seed)
def done(a): a.outline(); return a
def base_shadow(a, rw): a.shadow(a.w // 2, a.h - 1, rw)

# ---------------------------------------------------------------- sleeping / sitting
@item(124, 92)
def bed(w, h):
    a = new(w, h, 1); cx = a.w // 2; base_shadow(a, 26)
    panel(a, 3, 2, a.w - 4, 12, WOOD, 4); a.rect(3, 2, a.w - 4, 3, WOOD[2])                  # headboard
    a.rect(2, 10, 5, a.h - 2, WOOD[0]); a.rect(a.w - 6, 10, a.w - 3, a.h - 2, WOOD[0])      # posts
    a.rect(6, 13, a.w - 7, a.h - 6, LINEN[1])                                                # sheet
    a.rect(8, 15, a.w - 9, 22, LINEN[2]); a.rect(8, 22, a.w - 9, 22, LINEN[0]); a.rect(9, 16, 14, 18, LINEN[1])   # pillow
    a.rect(6, 25, a.w - 7, a.h - 6, GREEN[1]); a.rect(6, 25, a.w - 7, 26, GREEN[2]); a.rect(6, a.h - 8, a.w - 7, a.h - 6, GREEN[0])   # blanket
    for x in range(8, a.w - 8, 4): a.put(x, 30, GOLD[1]); a.put(x + 1, 31, GOLD[0])            # knot trim
    panel(a, 3, a.h - 7, a.w - 4, a.h - 3, WOOD, 4)                                         # footboard
    return done(a)
@item(112, 84)
def bed_small(w, h):
    a = new(w, h, 2); base_shadow(a, 22)
    panel(a, 3, 3, a.w - 4, 11, WOOD, 4); a.rect(5, 12, a.w - 6, a.h - 5, LINEN[1]); a.rect(7, 14, 20, 20, LINEN[2]); a.rect(5, 23, a.w - 6, a.h - 5, RED[1]); a.rect(5, 23, a.w - 6, 24, RED[2]); a.rect(5, a.h - 7, a.w - 6, a.h - 5, RED[0])
    for x in range(7, a.w - 7, 4): a.put(x, 28, GOLD[1])
    panel(a, 3, a.h - 6, a.w - 4, a.h - 2, WOOD, 4); return done(a)
@item(40, 56)
def chair(w, h):   # seen from the front, facing the camera
    a = new(w, h, 3); base_shadow(a, 7); cx = a.w // 2
    a.rect(cx - 6, 2, cx + 6, 14, WOOD[1]); a.rect(cx - 6, 2, cx + 6, 3, WOOD[2]); a.rect(cx - 6, 14, cx + 6, 14, WOOD[0])
    for x in (cx - 4, cx, cx + 4): a.rect(x, 5, x, 12, WOOD[0])
    a.rect(cx - 7, 16, cx + 7, 20, WOOD[2]); a.rect(cx - 7, 20, cx + 7, 20, WOOD[0])
    for lx in (cx - 7, cx + 5): a.rect(lx, 21, lx + 2, a.h - 2, WOOD[0]); a.rect(lx, 21, lx, a.h - 2, WOOD[1])
    return done(a)
@item(40, 56)
def chair_back(w, h):   # back to the camera (sits on the far side of a table)
    a = new(w, h, 4); base_shadow(a, 7); cx = a.w // 2
    a.rect(cx - 6, 4, cx + 6, 22, WOOD[1]); a.rect(cx - 6, 4, cx + 6, 5, WOOD[2]); a.rect(cx - 6, 22, cx + 6, 22, WOOD[0])
    for x in (cx - 3, cx + 1, cx + 5): a.rect(x, 7, x, 20, WOOD[0])
    a.rect(cx - 7, 23, cx + 7, 25, WOOD[0])
    for lx in (cx - 7, cx + 5): a.rect(lx, 26, lx + 2, a.h - 2, WOOD[0])
    return done(a)
@item(32, 36)
def stool(w, h):
    a = new(w, h, 5); base_shadow(a, 6); cx = a.w // 2
    ell(a, cx, 4, 7, 3, WOOD[2]); a.rect(cx - 7, 4, cx + 7, 6, WOOD[1]); a.rect(cx - 6, 7, cx + 6, 7, WOOD[0])
    for lx in (cx - 5, cx + 3): a.rect(lx, 8, lx + 1, a.h - 2, WOOD[0])
    return done(a)
@item(116, 48)
def bench(w, h):
    a = new(w, h, 6); base_shadow(a, 22)
    for lx in (6, a.w - 9): a.rect(lx, 8, lx + 2, a.h - 2, WOOD[0])
    box(a, 3, 4, a.w - 4, 14, 6, WOOD, 5); return done(a)

# ---------------------------------------------------------------- tables / counters
@item(120, 84)
def table_round(w, h):
    a = new(w, h, 7); cx = a.w // 2; base_shadow(a, 22)
    a.rect(cx - 3, 16, cx + 3, a.h - 3, WOOD[0]); a.rect(cx - 9, a.h - 4, cx + 9, a.h - 2, WOOD[0])
    ell(a, cx, 12, 25, 10, WOOD[0]); ell(a, cx, 10, 25, 10, WOOD[2]); ell(a, cx, 10, 22, 8, WOOD[1])
    for dx in (-12, -3, 7, 14): a.put(cx + dx, 9 + (dx % 3), WOOD[0])
    ell(a, cx - 8, 9, 4, 2, LINEN[2]); a.rect(cx + 4, 7, cx + 8, 9, CLAY[1]); a.rect(cx + 4, 6, cx + 8, 6, CLAY[2])      # plate, mug
    ell(a, cx + 12, 11, 3, 2, G(206, 150, 70)); a.put(cx + 12, 10, G(240, 200, 120))                                   # loaf
    return done(a)
@item(184, 80)
def table_long(w, h):
    a = new(w, h, 8); base_shadow(a, 40)
    for lx in (8, a.w - 11): a.rect(lx, 14, lx + 2, a.h - 2, WOOD[0])
    box(a, 4, 6, a.w - 5, 28, 9, WOOD, 7)
    for x in range(14, a.w - 14, 22): ell(a, x, 12, 3, 1, LINEN[2]); a.rect(x + 6, 9, x + 8, 11, CLAY[1])
    return done(a)
@item(96, 72)
def table_small(w, h):
    a = new(w, h, 9); base_shadow(a, 18)
    for lx in (6, a.w - 9): a.rect(lx, 12, lx + 2, a.h - 2, WOOD[0])
    box(a, 3, 4, a.w - 4, 22, 8, WOOD, 6); ell(a, 14, 9, 3, 1, LINEN[2]); a.rect(a.w - 14, 6, a.w - 11, 8, CLAY[1]); return done(a)
@item(224, 92)
def counter(w, h):
    a = new(w, h, 10); base_shadow(a, 46)
    box(a, 3, 4, a.w - 4, a.h - 3, 12, WOOD, 7)
    a.rect(3, 4, a.w - 4, 5, WOOD[2]); a.rect(3, 16, a.w - 4, 16, WOOD[0])
    for x in range(10, a.w - 10, 20): a.rect(x, 22, x + 12, a.h - 8, WOOD[0]); a.rect(x + 1, 23, x + 11, a.h - 9, WOOD[1])   # front panels
    return done(a)
def _counter_goods(w, h):
    a = new(w, h, 11); base_shadow(a, 46)
    box(a, 3, 8, a.w - 4, a.h - 3, 12, WOOD, 7)
    for x in range(10, a.w - 10, 20): a.rect(x, 26, x + 12, a.h - 8, WOOD[0]); a.rect(x + 1, 27, x + 11, a.h - 9, WOOD[1])
    for i, x in enumerate(range(16, 60, 11)): a.rect(x, 1, x + 4, 7, [BLUE, GREEN, RED, CLAY][i % 4][1]); a.rect(x + 1, 0, x + 3, 0, WOOD[2])       # bottles
    a.rect(a.w - 40, 5, a.w - 26, 7, LINEN[1]); a.rect(a.w - 38, 3, a.w - 28, 4, LINEN[2])                                                           # ledger
    a.rect(a.w - 20, 6, a.w - 14, 7, IRON[1]); a.rect(a.w - 17, 3, a.w - 17, 6, IRON[0]); a.rect(a.w - 22, 3, a.w - 12, 3, IRON[2])             # scale
    return done(a)
def _counter_inn(w, h):
    a = new(w, h, 12); base_shadow(a, 46)
    box(a, 3, 8, a.w - 4, a.h - 3, 12, WOOD, 7)
    for x in range(10, a.w - 10, 20): a.rect(x, 26, x + 12, a.h - 8, WOOD[0]); a.rect(x + 1, 27, x + 11, a.h - 9, WOOD[1])
    for x in (18, 36, 78, 100): a.rect(x, 3, x + 4, 7, CLAY[1]); a.rect(x, 3, x + 4, 3, LINEN[2]); a.rect(x + 5, 4, x + 6, 6, CLAY[0])     # tankards
    a.rect(60, 2, 66, 7, WOOD[1]); a.rect(60, 2, 66, 2, WOOD[2]); a.rect(63, 0, 63, 2, IRON[1])                                              # tap keg
    return done(a)
ITEMS['counter_inn'] = (_counter_inn, 224, 96, 'prop')
ITEMS['counter_shop'] = (_counter_goods, 224, 96, 'prop')

# ---------------------------------------------------------------- storage
def _shelf(w, h, seed, rows):
    a = new(w, h, seed); base_shadow(a, 18); W, H = a.w, a.h
    a.rect(2, 2, W - 3, H - 2, WOOD[0]); a.rect(3, 3, W - 4, H - 3, WOOD[1]); a.rect(2, 2, W - 3, 3, WOOD[2])
    levels = [4 + i * (H - 8) // rows for i in range(rows + 1)]
    for i in range(rows):
        y0, y1 = levels[i] + 1, levels[i + 1] - 1; a.rect(4, y1, W - 5, y1 + 1, WOOD[2]); a.rect(4, y1 + 2, W - 5, y1 + 2, WOOD[0]); a.rect(4, y0, W - 5, y1 - 1, G(54, 38, 28))
        yield a, i, y0, y1
def _fill_books(a, y0, y1, r):
    x = 5
    while x < a.w - 7:
        wd = r.choice([2, 3, 3, 4]); c = r.choice([RED, GREEN, BLUE, CLAY, WOOD])[1]; hh = r.randrange(max(3, (y1 - y0) - 4), y1 - y0)
        a.rect(x, y1 - hh, x + wd - 1, y1 - 1, c); a.rect(x, y1 - hh, x, y1 - 1, c); a.put(x + 1, y1 - hh + 1, GOLD[1]); x += wd + (1 if r.random() < .15 else 0)
def _fill_pots(a, y0, y1, r):
    x = 6
    while x < a.w - 10:
        k = r.choice(['jar', 'pot', 'bottle']); c = r.choice([CLAY, WOOD, GREEN])
        if k == 'jar': a.rect(x, y1 - 7, x + 5, y1 - 1, c[1]); a.rect(x + 1, y1 - 9, x + 4, y1 - 8, c[2]); a.rect(x, y1 - 1, x + 5, y1 - 1, c[0]); x += 8
        elif k == 'pot': ell(a, x + 4, y1 - 5, 5, 4, c[1]); a.rect(x, y1 - 9, x + 8, y1 - 8, IRON[1]); a.put(x + 2, y1 - 6, c[2]); x += 11
        else: a.rect(x, y1 - 8, x + 2, y1 - 1, c[1]); a.rect(x + 1, y1 - 10, x + 1, y1 - 9, WOOD[2]); x += 5
def _fill_goods(a, y0, y1, r):
    x = 6
    while x < a.w - 9:
        k = r.choice(['potion', 'herb', 'sack', 'coil']);
        if k == 'potion': c = r.choice([RED, BLUE, GREEN]); a.rect(x, y1 - 7, x + 3, y1 - 1, c[1]); a.rect(x + 1, y1 - 9, x + 2, y1 - 8, LINEN[1]); a.put(x + 1, y1 - 6, c[2]); x += 6
        elif k == 'herb': a.rect(x, y1 - 6, x + 5, y1 - 1, LINEN[0]); [a.put(x + i, y1 - 7 - (i % 2), GREEN[2]) for i in range(1, 5)]; a.rect(x, y1 - 3, x + 5, y1 - 3, ROPE); x += 8
        elif k == 'sack': ell(a, x + 4, y1 - 4, 4, 4, LINEN[1]); a.rect(x + 3, y1 - 9, x + 5, y1 - 8, ROPE); x += 10
        else: ell(a, x + 4, y1 - 3, 4, 3, ROPE); x += 10
def make_shelf(name, w, h, seed, filler, rows=3):
    def fn(w, h):
        r = random.Random(seed); a = None
        for a, i, y0, y1 in _shelf(w, h, seed, rows): filler(a, y0, y1, r)
        return done(a)
    fn.__name__ = name; ITEMS[name] = (fn, w, h, 'prop')
make_shelf('shelf_books', 100, 140, 21, _fill_books)
make_shelf('shelf_pots', 100, 140, 22, _fill_pots)
make_shelf('shelf_goods', 116, 140, 23, _fill_goods)
@item(92, 116)
def cupboard(w, h):   # タンス
    a = new(w, h, 24); base_shadow(a, 18)
    box(a, 3, 3, a.w - 4, a.h - 3, 6, WOOD, 6); a.rect(a.w // 2, 10, a.w // 2, a.h - 5, WOOD[0])
    for sx in (a.w // 2 - 6, a.w // 2 + 4): a.rect(sx, a.h // 2 - 2, sx + 1, a.h // 2 + 3, GOLD[1])
    a.rect(6, a.h - 18, a.w - 7, a.h - 18, WOOD[0]); a.rect(5, 2, a.w - 6, 2, WOOD[2]); return done(a)
@item(40, 52)
def jar(w, h):
    a = new(w, h, 25); base_shadow(a, 8); cx = a.w // 2
    ell(a, cx, 16, 9, 9, CLAY[1]); a.rect(cx - 5, 5, cx + 5, 9, CLAY[1]); a.rect(cx - 6, 3, cx + 6, 4, CLAY[2]); a.rect(cx - 8, 22, cx + 8, 24, CLAY[0])
    for dx in range(-7, 8, 3): a.put(cx + dx, 14, CLAY[2] if dx % 2 else CLAY[0])
    a.put(cx - 4, 12, CLAY[2]); a.put(cx - 4, 13, CLAY[2]); return done(a)
@item(48, 62)
def barrel(w, h):
    a = new(w, h, 26); base_shadow(a, 10); cx = a.w // 2
    a.rect(cx - 9, 4, cx + 9, a.h - 3, WOOD[1]); a.rect(cx - 9, 4, cx - 9, a.h - 3, WOOD[2]); a.rect(cx + 9, 4, cx + 9, a.h - 3, WOOD[0]); ell(a, cx, 5, 9, 3, WOOD[2]); ell(a, cx, 5, 7, 2, WOOD[1])
    for y in (10, a.h - 9): a.rect(cx - 9, y, cx + 9, y + 1, IRON[1])
    for x in (cx - 4, cx, cx + 4): a.rect(x, 8, x, a.h - 4, WOOD[0])
    return done(a)
@item(56, 48)
def crate(w, h):
    a = new(w, h, 27); base_shadow(a, 11); box(a, 3, 5, a.w - 4, a.h - 3, 6, WOOD, 6)
    a.rect(3, 12, a.w - 4, 13, WOOD[0]); a.rect(3, a.h - 8, a.w - 4, a.h - 8, WOOD[0]); return done(a)
@item(42, 46)
def sack(w, h):
    a = new(w, h, 28); base_shadow(a, 8); cx = a.w // 2
    ell(a, cx, 14, 8, 8, LINEN[1]); a.rect(cx - 4, 4, cx + 4, 8, LINEN[1]); a.rect(cx - 4, 8, cx + 4, 8, ROPE); a.rect(cx - 5, 3, cx + 5, 4, LINEN[2]); a.rect(cx - 7, 20, cx + 7, 21, LINEN[0])
    a.put(cx - 3, 12, LINEN[2]); a.put(cx - 3, 13, LINEN[2]); return done(a)
@item(44, 36)
def basket(w, h):
    a = new(w, h, 29); base_shadow(a, 8); cx = a.w // 2
    a.rect(cx - 8, 6, cx + 8, a.h - 3, WOOD[2]); a.rect(cx - 8, 6, cx + 8, 7, WOOD[1])
    for y in range(8, a.h - 3, 3): a.rect(cx - 8, y, cx + 8, y, WOOD[0])
    for x in range(cx - 6, cx + 8, 4): a.rect(x, 7, x, a.h - 4, WOOD[0])
    for dx in (-4, 0, 4): ell(a, cx + dx, 5, 2, 2, [RED, GREEN, GOLD][dx // 4 + 1][1]) if True else None
    return done(a)
@item(36, 40)
def bucket(w, h):
    a = new(w, h, 30); base_shadow(a, 7); cx = a.w // 2
    a.rect(cx - 6, 8, cx + 6, a.h - 3, WOOD[1]); a.rect(cx - 6, 8, cx - 6, a.h - 3, WOOD[2]); ell(a, cx, 8, 6, 2, BLUE[1]); a.rect(cx - 6, 11, cx + 6, 11, IRON[1]); a.rect(cx - 6, a.h - 8, cx + 6, a.h - 8, IRON[1])
    a.put(cx - 7, 5, IRON[1]); a.put(cx - 6, 3, IRON[1]); a.rect(cx - 5, 2, cx + 5, 2, IRON[1]); a.put(cx + 6, 3, IRON[1]); a.put(cx + 7, 5, IRON[1]); return done(a)
@item(72, 52)
def hay_bale(w, h):
    a = new(w, h, 31); base_shadow(a, 14)
    a.rect(4, 6, a.w - 5, a.h - 3, G(206, 170, 84)); a.rect(4, 6, a.w - 5, 8, G(238, 206, 120)); a.rect(4, a.h - 5, a.w - 5, a.h - 3, G(150, 112, 52))
    for x in range(8, a.w - 6, 5): a.rect(x, 9, x + 1, a.h - 5, G(176, 138, 64))
    a.rect(a.w // 3, 6, a.w // 3, a.h - 3, ROPE); a.rect(2 * a.w // 3, 6, 2 * a.w // 3, a.h - 3, ROPE); return done(a)
@item(76, 76)
def crates_stack(w, h):
    a = new(w, h, 32); base_shadow(a, 14)
    box(a, 2, 24, 22, a.h - 3, 5, WOOD, 5); box(a, 20, 28, 36, a.h - 3, 5, WOOD, 5); box(a, 8, 5, 28, 25, 5, WOOD, 5); return done(a)
@item(64, 68)
def sacks_pile(w, h):
    a = new(w, h, 33); base_shadow(a, 14)
    for (cx, cy, r) in ((10, 22, 8), (24, 24, 8), (17, 12, 8)): ell(a, cx + 4, cy + 6, r, r, LINEN[1]); a.rect(cx + 1, cy - 2, cx + 7, cy, LINEN[0]); a.rect(cx + 2, cy - 3, cx + 6, cy - 3, ROPE)
    return done(a)
@item(80, 100)
def tool_rack(w, h):
    a = new(w, h, 34); base_shadow(a, 14)
    a.rect(4, 6, a.w - 5, 8, WOOD[1]); a.rect(4, 6, a.w - 5, 6, WOOD[2]); a.rect(5, 8, 6, a.h - 3, WOOD[0]); a.rect(a.w - 7, 8, a.w - 6, a.h - 3, WOOD[0])
    for x, k in ((12, 'hoe'), (20, 'fork'), (28, 'rake'), (36, 'axe')):
        a.rect(x, 8, x, a.h - 8, WOOD[1])
        if k == 'axe': a.rect(x + 1, 10, x + 5, 15, IRON[1]); a.rect(x + 1, 10, x + 5, 10, IRON[2])
        else: a.rect(x - 2, a.h - 9, x + 2, a.h - 8, IRON[1])
    return done(a)
@item(60, 78)
def spinning_wheel(w, h):
    a = new(w, h, 35); base_shadow(a, 11)
    ell(a, 14, 18, 11, 11, WOOD[0]); ell(a, 14, 18, 9, 9, None); a.rect(14, 8, 14, 28, WOOD[1]); a.rect(4, 18, 24, 18, WOOD[1]); a.rect(13, 17, 15, 19, WOOD[2])
    a.rect(24, 26, 42, 28, WOOD[1]); a.rect(36, 18, 38, 36, WOOD[0]); a.rect(10, 28, 12, a.h - 2, WOOD[0]); a.rect(26, 28, 28, a.h - 2, WOOD[0]); a.rect(38, 36, 40, a.h - 2, WOOD[0])
    ell(a, 40, 16, 3, 2, LINEN[2]); return done(a)
@item(80, 104)
def weapon_rack(w, h):   # wooden practice blades and a spear (never a dagger)
    a = new(w, h, 36); base_shadow(a, 14)
    a.rect(4, a.h - 12, a.w - 5, a.h - 8, WOOD[1]); a.rect(4, a.h - 12, a.w - 5, a.h - 12, WOOD[2]); a.rect(6, a.h - 8, 8, a.h - 2, WOOD[0]); a.rect(a.w - 9, a.h - 8, a.w - 7, a.h - 2, WOOD[0])
    for x in (12, 20, 28): a.rect(x, 8, x + 1, a.h - 12, WOOD[2]); a.rect(x - 1, 22, x + 2, 23, WOOD[0])       # wooden swords: hilt guard
    a.rect(36, 4, 36, a.h - 12, WOOD[1]); a.rect(35, 1, 37, 4, IRON[2]); a.put(36, 0, IRON[2])
    a.rect(6, 30, a.w - 7, 31, WOOD[0]); return done(a)

# ---------------------------------------------------------------- hearth / wall pieces
@item(152, 136)
def fireplace(w, h):
    a = new(w, h, 40); W = a.w; base_shadow(a, 30)
    a.rect(2, 4, W - 3, a.h - 2, STONE[1]); a.rect(2, 4, W - 3, 6, STONE[2]); a.rect(2, a.h - 3, W - 3, a.h - 2, STONE[0])
    for y in range(8, a.h - 2, 6):
        for x in range(3 + (y // 6 % 2) * 4, W - 3, 8): a.rect(x, y, x, y + 5, STONE[0]); a.rect(x, y, x + 7, y, STONE[0]) if x + 7 < W - 3 else None
    a.rect(2, 2, W - 3, 5, STONE[2]); a.rect(2, 5, W - 3, 5, STONE[0])                                  # mantle
    a.rect(14, 18, W - 15, a.h - 4, G(24, 18, 18))                                                    # opening
    for y in range(18, 24): a.rect(14 + (y - 18), y, W - 15 - (y - 18), y, G(24, 18, 18))
    cx = W // 2
    for i, (fx, fh, c) in enumerate(((-9, 18, FIRE[0]), (0, 26, FIRE[1]), (9, 17, FIRE[0]), (-3, 15, FIRE[2]), (4, 12, FIRE[2]))):
        for y in range(fh): a.rect(cx + fx - max(0, 5 - y // 4) // 1, a.h - 7 - y, cx + fx + max(0, 5 - y // 4), a.h - 7 - y, c) if y < fh else None
    a.rect(cx - 16, a.h - 7, cx + 16, a.h - 5, WOOD[0]); a.rect(cx - 12, a.h - 8, cx + 12, a.h - 7, WOOD[1])      # logs
    a.rect(cx - 1, 6, cx - 1, 17, IRON[1]); ell(a, cx, 21, 7, 4, IRON[1]); a.rect(cx - 7, 18, cx + 7, 18, IRON[2])   # hanging cauldron
    return done(a)
@item(72, 100)
def tapestry(w, h):
    a = new(w, h, 41); W = a.w
    a.rect(1, 1, W - 2, 3, WOOD[1]); a.rect(1, 1, W - 2, 1, WOOD[2]); a.rect(3, 4, W - 4, a.h - 5, GREEN[1]); a.rect(3, 4, 3, a.h - 5, GOLD[1]); a.rect(W - 4, 4, W - 4, a.h - 5, GOLD[1])
    for y in range(8, a.h - 8, 6): a.rect(5, y, W - 6, y, GREEN[0])
    cx = W // 2; cy = a.h // 2
    for r, c in ((10, GOLD[1]), (8, GREEN[0]), (6, GOLD[2]), (4, GREEN[1])): ell(a, cx, cy, r, r, c)
    for dx, dy in ((-9, 0), (9, 0), (0, -9), (0, 9)): ell(a, cx + dx, cy + dy, 2, 2, GOLD[1])
    for x in range(4, W - 4, 3): a.put(x, a.h - 4, GOLD[1]); a.put(x, a.h - 3, GOLD[0])
    return done(a)
@item(64, 76)
def window_wall(w, h):
    a = new(w, h, 42); W = a.w
    a.rect(2, 2, W - 3, a.h - 3, WOOD[0]); a.rect(4, 4, W - 5, a.h - 5, G(150, 196, 220)); a.rect(4, 4, W - 5, 12, G(190, 222, 238))
    a.rect(W // 2, 4, W // 2, a.h - 5, WOOD[0]); a.rect(4, a.h // 2, W - 5, a.h // 2, WOOD[0]); a.rect(1, a.h - 4, W - 2, a.h - 3, WOOD[2])
    for y in range(6, 14): a.put(6 + (y - 6), y, G(240, 250, 255))
    return done(a)
@item(60, 100)
def door_wall(w, h):   # room / back doors drawn on the wall
    a = new(w, h, 43); W = a.w
    a.rect(2, 2, W - 3, a.h - 2, WOOD[0]); panel(a, 4, 4, W - 5, a.h - 3, WOOD, 6); a.rect(4, 4, W - 5, 5, WOOD[2])
    a.rect(4, a.h // 2, W - 5, a.h // 2, WOOD[0]); a.rect(W - 9, a.h // 2 + 3, W - 7, a.h // 2 + 5, GOLD[1]); return done(a)
@item(36, 60)
def candle_stand(w, h):
    a = new(w, h, 44); base_shadow(a, 6); cx = a.w // 2
    a.rect(cx - 1, 14, cx + 1, a.h - 4, IRON[1]); a.rect(cx - 5, a.h - 4, cx + 5, a.h - 2, IRON[0]); a.rect(cx - 3, 12, cx + 3, 13, IRON[2])
    a.rect(cx - 1, 6, cx + 1, 11, LINEN[1]); a.rect(cx, 3, cx, 5, FIRE[2]); a.put(cx, 2, FIRE[1]); return done(a)
@item(44, 66)
def herb_bundle(w, h):   # hung on the wall
    a = new(w, h, 45); cx = a.w // 2
    a.rect(cx - 5, 2, cx + 5, 3, WOOD[1])
    for dx in (-4, 0, 4): a.rect(cx + dx, 4, cx + dx, 9, ROPE); [a.put(cx + dx + (i % 3) - 1, 10 + i, [GREEN[1], GREEN[2], GREEN[0]][i % 3]) for i in range(0, 18)]
    return done(a)
@item(56, 80)
def rune_pillar(w, h):   # elder's house: small carved rune stone
    a = new(w, h, 46); base_shadow(a, 10); cx = a.w // 2
    a.rect(cx - 8, 6, cx + 8, a.h - 3, STONE[1]); a.rect(cx - 8, 6, cx - 8, a.h - 3, STONE[2]); a.rect(cx + 8, 6, cx + 8, a.h - 3, STONE[0]); a.rect(cx - 6, 3, cx + 6, 5, STONE[1]); a.rect(cx - 3, 1, cx + 3, 2, STONE[1])
    for y, (x0, x1) in ((14, (-3, 3)), (20, (0, 0)), (26, (-3, 3)), (30, (-3, 0))): a.rect(cx + x0, y, cx + x1, y, MOSS[2] if False else G(110, 170, 160))
    a.rect(cx, 14, cx, 28, G(110, 170, 160)); a.put(cx - 2, 18, G(110, 170, 160)); a.put(cx + 2, 24, G(110, 170, 160)); return done(a)
@item(120, 84)
def map_table(w, h):   # elder's table with the old village map
    a = new(w, h, 47); base_shadow(a, 22)
    for lx in (7, a.w - 10): a.rect(lx, 18, lx + 2, a.h - 2, WOOD[0])
    box(a, 3, 6, a.w - 4, 30, 9, WOOD, 6)
    a.rect(10, 8, a.w - 11, 13, LINEN[1]); a.rect(10, 8, a.w - 11, 8, LINEN[2]); a.rect(14, 10, 22, 11, MOSS[1]); a.rect(30, 9, 34, 12, G(110, 150, 190)); a.rect(40, 10, 46, 10, CLAY[1]); a.put(26, 11, RED[1])
    a.rect(a.w - 20, 7, a.w - 14, 9, CLAY[1]); return done(a)
@item(88, 78)
def stairs_up(w, h):
    a = new(w, h, 48); base_shadow(a, 16); W = a.w
    for i in range(6): a.rect(4 + i * 2, 4 + i * 5, W - 5, 8 + i * 5, WOOD[1] if i % 2 else WOOD[2]); a.rect(4 + i * 2, 8 + i * 5, W - 5, 8 + i * 5, WOOD[0])
    a.rect(2, 2, 4, a.h - 3, WOOD[0]); a.rect(W - 5, 2, W - 3, a.h - 3, WOOD[0]); a.rect(2, 2, W - 3, 3, WOOD[2]); return done(a)
@item(88, 78)
def stairs_down(w, h):
    a = new(w, h, 49); base_shadow(a, 16); W = a.w
    a.rect(4, 8, W - 5, a.h - 4, G(34, 24, 20))
    for i in range(5): a.rect(4, 8 + i * 6, W - 5, 11 + i * 6, WOOD[1] if i % 2 else WOOD[0]); a.rect(4, 8 + i * 6, W - 5, 8 + i * 6, WOOD[2])
    a.rect(2, 4, 4, 14, WOOD[0]); a.rect(W - 5, 4, W - 3, 14, WOOD[0]); a.rect(2, 4, W - 3, 5, WOOD[2]); return done(a)
@item(52, 56)
def plant_pot(w, h):
    a = new(w, h, 50); base_shadow(a, 8); cx = a.w // 2
    a.rect(cx - 6, 16, cx + 6, a.h - 3, CLAY[1]); a.rect(cx - 7, 14, cx + 7, 16, CLAY[2]); a.rect(cx - 6, a.h - 5, cx + 6, a.h - 3, CLAY[0])
    for dx, dy, c in ((-5, 6, GREEN[1]), (0, 2, GREEN[2]), (5, 7, GREEN[1]), (-2, 8, GREEN[0]), (3, 4, GREEN[2])): ell(a, cx + dx, dy, 4, 4, c)
    a.put(cx, 6, G(244, 220, 90)); a.put(cx - 6, 8, G(240, 240, 232)); return done(a)
@item(48, 40)
def spill_bowl(w, h):
    a = new(w, h, 51); base_shadow(a, 7); cx = a.w // 2
    ell(a, cx, 12, 9, 5, CLAY[0]); ell(a, cx, 11, 9, 4, CLAY[1]); ell(a, cx, 10, 7, 3, G(206, 150, 70)); return done(a)

# ---------------------------------------------------------------- floor decals (lie flat; drawn under actors)
def _rug(w, h, seed, base, rim):
    a = new(w, h, seed); W, H = a.w, a.h; cx, cy = W // 2, H // 2
    ell(a, cx, cy, W // 2 - 1, H // 2 - 1, rim[0]); ell(a, cx, cy, W // 2 - 3, H // 2 - 3, rim[1]); ell(a, cx, cy, W // 2 - 6, H // 2 - 6, base[1]); ell(a, cx, cy, W // 2 - 8, H // 2 - 8, base[0] if False else base[1])
    for i in range(0, 360, 20):
        import math; x = int(cx + (W // 2 - 4) * math.cos(math.radians(i))); y = int(cy + (H // 2 - 4) * math.sin(math.radians(i))); a.put(x, y, GOLD[1]); a.put(x + 1, y, GOLD[2])
    for r, c in ((H // 5, GOLD[1]), (H // 7, base[0]), (H // 10, GOLD[2])): ell(a, cx, cy, int(r * 1.6), r, c)
    a.px = [[(c if c is None else c) for c in row] for row in a.px]
    return a
ITEMS['rug_green'] = (lambda w, h: _rug(w, h, 52, GREEN, RED), 200, 120, 'decal')
ITEMS['rug_red'] = (lambda w, h: _rug(w, h, 53, RED, GREEN), 144, 88, 'decal')
@item(84, 36, 'decal')
def doormat(w, h):
    a = new(w, h, 54); a.rect(1, 2, a.w - 2, a.h - 3, ROPE); a.rect(1, 2, a.w - 2, 2, LINEN[2]); a.rect(1, a.h - 3, a.w - 2, a.h - 3, WOOD[0])
    for x in range(3, a.w - 3, 4): a.rect(x, 4, x, a.h - 5, G(176, 144, 84)); return a
@item(60, 36, 'decal')
def window_light(w, h):   # soft pool of daylight on the floor
    a = new(w, h, 55)
    for y in range(a.h):
        for x in range(a.w):
            if abs(x - a.w // 2) / (a.w / 2) + abs(y - a.h // 2) / (a.h / 2) < 1: a.put(x, y, (255, 240, 190, 46))
    return a   # no outline on purpose

# ---------------------------------------------------------------- post-attack debris (outdoors)
def _rubble(w, h, seed, n):
    a = new(w, h, seed); r = random.Random(seed); base_shadow(a, a.w // 3)
    for _ in range(n):
        cx = r.randrange(6, a.w - 6); cy = a.h - 4 - r.randrange(0, max(2, a.h // 3)); rr = r.randrange(3, max(5, a.w // 6)); c = r.choice([STONE, ASH, [G(88, 66, 50), G(116, 88, 66), G(146, 112, 84)]])
        ell(a, cx, cy, rr, max(2, rr * 2 // 3), c[1]); a.rect(cx - rr + 1, cy - max(2, rr * 2 // 3), cx + rr - 1, cy - max(2, rr * 2 // 3), c[2])
    for _ in range(max(2, n // 4)):
        x = r.randrange(4, a.w - 12); y = a.h - 4 - r.randrange(0, max(3, a.h // 2)); L = r.randrange(8, 18)
        for i in range(L): a.put(x + i, y - i // 6, ASH[1]); a.put(x + i, y - i // 6 + 1, ASH[0])
    return done(a)
ITEMS['rubble_s'] = (lambda w, h: _rubble(w, h, 61, 7), 72, 44, 'prop')
ITEMS['rubble_m'] = (lambda w, h: _rubble(w, h, 62, 13), 120, 66, 'prop')
ITEMS['rubble_l'] = (lambda w, h: _rubble(w, h, 63, 22), 180, 90, 'prop')
@item(150, 40)
def burnt_beam(w, h):
    a = new(w, h, 64); base_shadow(a, 20)
    for i in range(a.w - 14): a.rect(6 + i, 12 - i // 14, 6 + i, 18 - i // 14, ASH[1]); a.put(6 + i, 12 - i // 14, ASH[2]); a.put(6 + i, 18 - i // 14, ASH[0])
    for x in range(8, a.w - 12, 7): a.put(x, 15 - x // 14, FIRE[0]) if x % 3 == 0 else None
    return done(a)
@item(96, 120, 'decal')
def ash_patch(w, h):
    a = new(w, h, 65); r = random.Random(65); cx, cy = a.w // 2, a.h // 2
    for _ in range(110):
        x = int(r.gauss(cx, a.w / 5)); y = int(r.gauss(cy, a.h / 5)); rr = r.randrange(1, 4)
        if abs(x - cx) < a.w // 2 - 2 and abs(y - cy) < a.h // 2 - 2: ell(a, x, y, rr, max(1, rr - 1), (30, 26, 28, r.choice([70, 90, 120])))
    for _ in range(14): a.put(cx + r.randrange(-12, 12), cy + r.randrange(-14, 14), (222, 110, 30, 150))
    return a
@item(120, 90, 'decal')
def scorch(w, h):
    a = new(w, h, 66); r = random.Random(66); cx, cy = a.w // 2, a.h // 2
    for ring, al in ((26, 40), (20, 70), (14, 100), (9, 130)):
        ell(a, cx, cy, ring + r.randrange(-1, 2), (ring * 2) // 3, (22, 18, 20, al))
    return a
@item(70, 100)
def post_burnt(w, h):
    a = new(w, h, 67); base_shadow(a, 8); cx = a.w // 2
    for y in range(6, a.h - 2): a.rect(cx - 3 + (y % 5 == 0), y, cx + 3 - (y % 7 == 0), y, ASH[1]); a.put(cx - 3, y, ASH[2]); a.put(cx + 3, y, ASH[0])
    for y in range(2, 8): a.rect(cx - 2 + (y % 2), y, cx + 1, y, ASH[0])
    a.put(cx, 8, FIRE[0]); a.put(cx + 1, 14, FIRE[0]); return done(a)
@item(110, 76)
def cart_wreck(w, h):
    a = new(w, h, 68); base_shadow(a, 20)
    a.rect(6, 22, a.w - 12, 30, ASH[1]); a.rect(6, 22, a.w - 12, 22, ASH[2]); a.rect(10, 12, 12, 22, ASH[0]); a.rect(a.w - 18, 16, a.w - 16, 24, ASH[0])
    ell(a, 18, a.h - 12, 12, 12, ASH[0]); ell(a, 18, a.h - 12, 9, 9, None); a.rect(18, a.h - 22, 18, a.h - 2, ASH[2]); a.rect(8, a.h - 12, 28, a.h - 12, ASH[2])
    return done(a)
@item(60, 50)
def banner_torn(w, h):
    a = new(w, h, 69); cx = a.w // 2
    a.rect(cx - 1, 2, cx + 1, a.h - 2, WOOD[0]); a.rect(cx + 2, 4, cx + 12, 8, GREEN[0]); a.rect(cx + 2, 4, cx + 12, 4, GREEN[1]); a.rect(cx + 4, 9, cx + 9, 12, GREEN[0]); a.rect(cx + 6, 13, cx + 8, 15, GREEN[0])
    return done(a)

@item(36, 32)
def cat_white(w, h):
    a = new(w, h, 70); base_shadow(a, 6); cx = a.w // 2; W = LINEN
    ell(a, cx, 10, 5, 5, W[2]); ell(a, cx, 5, 4, 3, W[2]); a.put(cx - 3, 1, W[2]); a.put(cx - 3, 2, W[1]); a.put(cx + 3, 1, W[2]); a.put(cx + 3, 2, W[1])
    a.put(cx - 2, 5, ASH[1]); a.put(cx + 2, 5, ASH[1]); a.put(cx, 6, (210, 130, 120, 255))
    a.rect(cx + 4, 12, cx + 8, 13, W[1]); a.put(cx + 8, 11, W[1]); a.put(cx + 9, 10, W[1]); return done(a)

def main():
    os.makedirs(OUT, exist_ok=True); meta = {}; tiles = []
    for name, (fn, w, h, kind) in ITEMS.items():
        a = fn(w, h); size = a.png(os.path.join(OUT, name + '.png'))
        assert size == (w * K, h * K), (name, size, (w * K, h * K))
        meta[name] = {'file': 'rilde/furn/%s.png' % name, 'w': w, 'h': h, 'kind': kind}; tiles.append(name)
    json.dump(meta, open(os.path.join(ROOT, 'tools/moss/rilde_furn.json'), 'w'), indent=1)
    print('furniture/debris: %d sprites -> %s' % (len(meta), OUT))
    if '--sheet' in sys.argv:
        path = sys.argv[sys.argv.index('--sheet') + 1]; sheet = Image.new('RGBA', (1800, 1100), (150, 120, 84, 255)); x = y = 10; rowh = 0
        for name in tiles:
            im = Image.open(os.path.join(OUT, name + '.png')).convert('RGBA')
            if x + im.size[0] > 1790: x = 10; y += rowh + 10; rowh = 0
            sheet.alpha_composite(im, (x, y)); x += im.size[0] + 10; rowh = max(rowh, im.size[1])
        sheet.save(path)
if __name__ == '__main__': main()
