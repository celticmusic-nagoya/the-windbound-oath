#!/usr/bin/env python3
"""Dunvall Fort + Royal Capital props as warm retro pixel art (stand-in quality, replaceable any time). Same spec as every moss prop:
1 art dot = 2 world px = 4 image px, transparent RGBA, feet at the bottom-centre. Writes img/field/moss/town/<name>.png and registers 'town_<name>'
rules at the top of the manifest node list (gen:"make_town_art", idempotent).
usage: python3 tools/moss/make_town_art.py [--sheet out.png]"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from make_props import Art, WOOD, STONE, MOSS, ROPE, INK, S, K
from PIL import Image
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'img/field/moss/town'); MAN = os.path.join(ROOT, 'img/field/moss/manifest.json')
G = lambda *a: tuple(a) + (255,)
GRY = [G(84, 80, 92), G(122, 118, 128), G(164, 160, 164)]          # castle stone dark/mid/light
SAND = [G(150, 130, 100), G(188, 166, 128), G(220, 200, 160)]       # town plaster
ROOFR = [G(120, 52, 40), G(164, 76, 52), G(204, 104, 66)]
ROOFB = [G(48, 64, 104), G(72, 96, 144), G(108, 136, 184)]
ROOFG = [G(52, 88, 70), G(78, 124, 94), G(116, 164, 126)]
LEAF = [G(38, 84, 46), G(62, 118, 58), G(104, 156, 74)]
PINE = [G(28, 66, 52), G(44, 96, 66), G(76, 132, 84)]
RED = [G(112, 34, 40), G(160, 52, 52), G(204, 84, 72)]
NAVY = [G(34, 48, 96), G(54, 78, 144), G(96, 128, 196)]
GOLD = [G(160, 120, 44), G(214, 172, 70), G(248, 216, 118)]
WATER = [G(52, 116, 152), G(88, 160, 190), G(168, 216, 228)]
IRON = [G(52, 52, 60), G(92, 94, 102), G(140, 142, 150)]
CLOTH = {'red': RED, 'blue': NAVY, 'green': [G(44, 96, 60), G(70, 140, 84), G(112, 186, 116)], 'ochre': GOLD}
ITEMS = {}
def item(w, h):
    def deco(fn): ITEMS[fn.__name__] = (fn, w, h); return fn
    return deco
def ell(a, cx, cy, rx, ry, c):
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if ((x - cx) / max(rx, .5)) ** 2 + ((y - cy) / max(ry, .5)) ** 2 <= 1.0: a.put(x, y, c)
def bricks(a, x0, y0, x1, y1, c=GRY, rowh=4, bw=7):
    a.rect(x0, y0, x1, y1, c[1])
    for i, y in enumerate(range(y0, y1 + 1, rowh)):
        a.rect(x0, y, x1, y, c[0])
        for x in range(x0 + (bw // 2 if i % 2 else 0), x1 + 1, bw):
            for yy in range(y + 1, min(y + rowh, y1 + 1)): a.put(x, yy, c[0])
    a.rect(x0, y0, x1, y0, c[2])
    for _ in range((x1 - x0) * (y1 - y0) // 60):
        a.put(a.r.randint(x0, x1), a.r.randint(y0, y1), c[2])
def shade_right(a, x0, y0, x1, y1, c, wdt=3):
    for y in range(y0, y1 + 1):
        for x in range(x1 - wdt + 1, x1 + 1):
            if a.px[y][x] is not None: a.put(x, y, c)
def new(w, h, seed): return Art(w, h, seed)
def done(a): a.outline(); return a
def shadow(a, rw=None): a.shadow(a.w // 2, a.h - 1, rw or a.w // 2 - 2)

# ---------------------------------------------------------------- nature
@item(120, 160)
def tree_oak():
    a = new(120, 160, 1); shadow(a, 22)
    a.rect(26, 56, 33, 78, WOOD[1]); a.rect(26, 56, 28, 78, WOOD[2]); a.rect(32, 56, 33, 78, WOOD[0]); a.rect(22, 74, 37, 78, WOOD[0])
    for cx, cy, rx, ry in ((30, 34, 28, 22), (14, 42, 14, 14), (46, 42, 14, 14), (30, 18, 18, 14), (20, 28, 12, 12), (42, 26, 12, 12)): ell(a, cx, cy, rx, ry, LEAF[1])
    for cx, cy, rx, ry in ((24, 22, 12, 8), (40, 36, 10, 7), (16, 36, 8, 6)): ell(a, cx, cy, rx, ry, LEAF[2])
    for _ in range(40):
        x, y = a.r.randint(6, 56), a.r.randint(30, 56)
        if a.px[y][x] == LEAF[1]: a.put(x, y, LEAF[0])
    return done(a)
@item(90, 160)
def tree_pine():
    a = new(90, 160, 2); shadow(a, 14)
    a.rect(21, 62, 24, 78, WOOD[0]); a.rect(21, 62, 22, 78, WOOD[1])
    for i, (cy, hw) in enumerate(((58, 19), (46, 16), (34, 13), (22, 10), (11, 6))):
        for dy in range(-9, 4):
            w = max(0, hw - max(0, -dy) * hw // 10 - (3 if dy > 0 else 0)) if dy <= 0 else hw - 2 - dy
            for x in range(22 - w, 23 + w):
                a.put(x, cy + dy, PINE[1] if (x + dy) % 5 else PINE[0])
        for x in range(22 - hw, 23 - hw // 2): a.put(x, cy, PINE[2]) if x % 2 else None
    return done(a)
@item(110, 60)
def flowerbed():
    a = new(110, 60, 3); shadow(a, 26)
    a.rect(2, 12, 52, 26, STONE[1]); a.rect(2, 12, 52, 13, STONE[2]); a.rect(2, 26, 52, 26, STONE[0]); a.rect(4, 14, 50, 21, G(96, 64, 44))
    for _ in range(22):
        x, y = a.r.randint(5, 49), a.r.randint(9, 19); a.put(x, y - 1, MOSS[1]); a.put(x, y, a.r.choice([RED[2], GOLD[2], G(220, 120, 170), G(210, 210, 240)]))
    return done(a)
@item(70, 90)
def bush_round():
    a = new(70, 90, 4); shadow(a, 14)
    for cx, cy, rx, ry in ((17, 30, 14, 12), (10, 34, 8, 8), (25, 34, 8, 8)): ell(a, cx, cy, rx, ry, LEAF[1])
    ell(a, 14, 26, 7, 5, LEAF[2])
    for _ in range(14): a.put(a.r.randint(6, 28), a.r.randint(30, 40), LEAF[0])
    return done(a)

# ---------------------------------------------------------------- street furniture
@item(36, 100)
def lamp_post():
    a = new(36, 100, 5); shadow(a, 5)
    a.rect(8, 22, 9, 48, IRON[1]); a.rect(8, 22, 8, 48, IRON[2]); a.rect(5, 46, 12, 48, IRON[0])
    a.rect(4, 12, 13, 22, G(60, 50, 40)); a.rect(5, 13, 12, 21, G(255, 226, 140)); a.rect(7, 14, 10, 19, G(255, 248, 200)); a.rect(3, 10, 14, 11, IRON[1]); a.rect(7, 8, 10, 9, IRON[2])
    return done(a)
@item(40, 84)
def torch_post():
    a = new(40, 84, 6); shadow(a, 5)
    a.rect(9, 24, 10, 40, WOOD[1]); a.rect(8, 40, 11, 41, IRON[1]); a.rect(6, 20, 13, 24, IRON[1])
    ell(a, 10, 14, 3, 5, G(240, 128, 30)); ell(a, 10, 15, 2, 3, G(255, 214, 84)); a.put(10, 9, G(255, 214, 84))
    return done(a)
@item(52, 120)
def banner_pole():   # kingdom banner on a pole (navy + gold); `banner_pole_red` for the fort
    a = new(52, 120, 7); shadow(a, 5)
    a.rect(12, 6, 13, 54, WOOD[1]); a.rect(12, 6, 12, 54, WOOD[2]); ell(a, 12, 5, 2, 2, GOLD[1])
    a.rect(14, 8, 24, 36, NAVY[1]); a.rect(14, 8, 14, 36, NAVY[2]); a.rect(24, 8, 24, 36, NAVY[0])
    for y in range(36, 41): a.rect(14 + (y - 36), y, 24 - (y - 36), y, NAVY[1])
    a.rect(17, 14, 21, 14, GOLD[2]); a.rect(19, 12, 19, 20, GOLD[2]); a.rect(17, 24, 21, 24, GOLD[1]); a.rect(14, 8, 24, 8, GOLD[1])
    return done(a)
@item(52, 120)
def banner_pole_red():
    a = new(52, 120, 8); shadow(a, 5)
    a.rect(12, 6, 13, 54, WOOD[1]); a.rect(12, 6, 12, 54, WOOD[2]); ell(a, 12, 5, 2, 2, GOLD[1])
    a.rect(14, 8, 24, 36, RED[1]); a.rect(14, 8, 14, 36, RED[2]); a.rect(24, 8, 24, 36, RED[0])
    for y in range(36, 41): a.rect(14 + (y - 36), y, 24 - (y - 36), y, RED[1])
    a.rect(17, 16, 21, 16, GOLD[2]); a.rect(19, 14, 19, 24, GOLD[2]); a.rect(14, 8, 24, 8, GOLD[1])
    return done(a)
@item(96, 100)
def well():
    a = new(96, 100, 9); shadow(a, 18)
    bricks(a, 12, 30, 36, 44, GRY, 4, 6); ell(a, 24, 30, 12, 4, GRY[2]); ell(a, 24, 30, 9, 3, G(24, 40, 60))
    a.rect(10, 8, 11, 32, WOOD[0]); a.rect(36, 8, 37, 32, WOOD[0]); a.rect(8, 6, 39, 9, WOOD[1]); a.rect(8, 6, 39, 6, WOOD[2]); a.rect(10, 4, 37, 5, ROOFR[1])
    a.rect(24, 10, 24, 22, ROPE); a.rect(22, 22, 26, 25, WOOD[0])
    return done(a)
@item(280, 200)
def fountain():
    a = new(280, 200, 10); shadow(a, 56)
    ell(a, 70, 74, 62, 24, GRY[0]); ell(a, 70, 72, 62, 22, GRY[2]); ell(a, 70, 74, 56, 19, GRY[1]); ell(a, 70, 74, 52, 16, WATER[1])
    for i in range(30): a.put(a.r.randint(30, 110), a.r.randint(64, 82), WATER[2])
    a.rect(64, 34, 76, 74, GRY[1]); a.rect(64, 34, 66, 74, GRY[2]); a.rect(75, 34, 76, 74, GRY[0])
    ell(a, 70, 44, 18, 7, GRY[1]); ell(a, 70, 43, 16, 5, WATER[1]); ell(a, 70, 20, 8, 12, WATER[2]); a.rect(69, 8, 71, 30, WATER[2])
    for dx, dy in ((-3, 26), (3, 26), (-8, 22), (8, 22)): a.rect(70 + dx, dy, 70 + dx, 42, WATER[2])
    return done(a)
@item(190, 150)
def stall_red():
    return stall('red', 11)
@item(190, 150)
def stall_blue():
    return stall('blue', 12)
@item(190, 150)
def stall_green():
    return stall('green', 13)
def stall(col, seed):
    a = new(190, 150, seed); shadow(a, 40); c = CLOTH[col]
    a.rect(6, 30, 8, 72, WOOD[0]); a.rect(86, 30, 88, 72, WOOD[0])
    a.rect(4, 8, 90, 30, c[1])
    for x in range(4, 91, 8): a.rect(x, 8, x + 3, 30, G(236, 226, 200)); a.rect(x, 30, x + 3, 33, G(236, 226, 200)); a.rect(x + 4, 30, x + 7, 33, c[1])
    a.rect(4, 8, 90, 9, c[2]); a.rect(4, 29, 90, 29, c[0])
    a.rect(6, 52, 88, 72, WOOD[1]); a.rect(6, 52, 88, 54, WOOD[2]); a.rect(6, 72, 88, 72, WOOD[0])
    for x in range(12, 88, 10): a.rect(x, 58, x, 70, WOOD[0])
    for i, x in enumerate(range(12, 82, 12)):
        col2 = [RED[2], GOLD[1], MOSS[2], G(220, 150, 80), G(150, 90, 150)][i % 5]; ell(a, x + 3, 49, 4, 3, col2); a.put(x + 2, 47, G(255, 255, 255))
    return done(a)
@item(150, 100)
def cart():
    a = new(150, 100, 14); shadow(a, 30)
    a.rect(8, 22, 64, 40, WOOD[1]); a.rect(8, 22, 64, 24, WOOD[2]); a.rect(8, 40, 64, 40, WOOD[0])
    for x in range(14, 64, 8): a.rect(x, 25, x, 39, WOOD[0])
    for x in range(14, 60, 9): ell(a, x + 3, 21, 4, 3, G(210, 170, 70))
    for cx in (22, 52): ell(a, cx, 42, 8, 8, WOOD[0]); ell(a, cx, 42, 6, 6, WOOD[2]); ell(a, cx, 42, 2, 2, IRON[1])
    a.rect(64, 34, 78, 35, WOOD[0])
    return done(a)
@item(70, 90)
def bench_stone():
    a = new(70, 90, 15); shadow(a, 14)
    a.rect(4, 22, 31, 31, GRY[1]); a.rect(4, 22, 31, 23, GRY[2]); a.rect(4, 31, 31, 31, GRY[0]); a.rect(5, 32, 8, 38, GRY[0]); a.rect(27, 32, 30, 38, GRY[0])
    return done(a)

# ---------------------------------------------------------------- fort pieces
@item(210, 150)
def battlement():   # row of merlons that sits on top of a wall segment (drawn at the wall's top edge)
    a = new(210, 150, 16)
    for i in range(0, 52, 10):
        a.rect(i, 6, i + 6, 20, GRY[1]); a.rect(i, 6, i + 6, 7, GRY[2]); a.rect(i + 5, 8, i + 6, 20, GRY[0]); a.rect(i, 20, i + 6, 20, GRY[0])
    return done(a)
@item(240, 300)
def tower_round():   # watch tower, art covers a 200x200 world footprint
    a = new(240, 300, 17); shadow(a, 46)
    bricks(a, 18, 48, 102, 142, GRY, 5, 9)
    for x in range(18, 103):
        for y in range(48, 143):
            if a.px[y][x] and x < 30: a.put(x, y, GRY[2] if (y // 5 + x) % 3 else GRY[1])
            if a.px[y][x] and x > 90: a.put(x, y, GRY[0] if (x + y) % 3 else GRY[1])
    for y0 in (70, 100):
        a.rect(56, y0, 64, y0 + 14, G(30, 26, 36)); a.rect(55, y0 - 1, 65, y0 - 1, GRY[2])
    for i in range(14, 108, 12): a.rect(i, 36, i + 7, 47, GRY[1]); a.rect(i, 36, i + 7, 37, GRY[2]); a.rect(i + 6, 38, i + 7, 47, GRY[0])
    for y in range(8, 36):   # conical roof
        hw = 4 + (y - 8) * 2
        for x in range(60 - hw, 61 + hw): a.put(x, y, ROOFB[1] if (x + y) % 6 else ROOFB[0])
        a.put(60 - hw, y, ROOFB[2]); a.put(61 + hw, y, ROOFB[0])
    a.rect(60, 0, 60, 8, IRON[1]); a.rect(61, 1, 66, 5, RED[1])
    return done(a)
@item(420, 220)
def gate_arch():   # fort gate: two stone piers with an arch + portcullis seen open (art 420 wide, opening 220)
    a = new(420, 220, 18)
    bricks(a, 0, 20, 36, 104, GRY, 5, 9); bricks(a, 174, 20, 209, 104, GRY, 5, 9)
    bricks(a, 36, 20, 174, 44, GRY, 5, 9)
    for i in range(36, 174, 12): a.rect(i, 14, i + 6, 19, GRY[1]); a.rect(i, 14, i + 6, 14, GRY[2])
    for i in (0, 174):
        for j in range(0, 36, 12): a.rect(i + j, 10, i + j + 6, 19, GRY[1]); a.rect(i + j, 10, i + j + 6, 10, GRY[2])
    for x in range(40, 170, 8): a.rect(x, 45, x, 62, IRON[1])
    a.rect(38, 45, 172, 46, IRON[0])
    a.rect(14, 58, 19, 66, RED[1]); a.rect(190, 58, 195, 66, RED[1])
    return done(a)
@item(120, 100)
def weapon_stand_out():
    a = new(120, 100, 19); shadow(a, 24)
    a.rect(6, 26, 52, 28, WOOD[1]); a.rect(6, 26, 52, 26, WOOD[2]); a.rect(8, 28, 9, 46, WOOD[0]); a.rect(49, 28, 50, 46, WOOD[0]); a.rect(6, 38, 52, 39, WOOD[1])
    for x in range(12, 50, 6):
        a.rect(x, 12, x, 36, IRON[2]); a.rect(x - 1, 34, x + 1, 35, GOLD[1]) if (x // 6) % 2 else a.rect(x, 8, x, 12, IRON[2])
    return done(a)
@item(110, 130)
def training_dummy():
    a = new(110, 130, 20); shadow(a, 13)
    a.rect(26, 14, 28, 58, WOOD[1]); a.rect(26, 14, 26, 58, WOOD[2]); a.rect(14, 26, 40, 30, WOOD[1]); a.rect(14, 26, 40, 26, WOOD[2])
    ell(a, 27, 14, 6, 6, G(210, 180, 120)); a.rect(21, 28, 33, 44, G(196, 160, 100)); a.rect(21, 28, 22, 44, G(226, 196, 140)); a.rect(32, 28, 33, 44, G(150, 116, 70))
    a.rect(20, 40, 34, 40, RED[1]); a.rect(22, 54, 32, 58, WOOD[0])
    return done(a)
@item(130, 80)
def hay_stack():
    a = new(130, 80, 21); shadow(a, 24)
    ell(a, 30, 26, 26, 12, G(214, 180, 84)); ell(a, 28, 22, 18, 8, G(238, 208, 116))
    for _ in range(40): a.put(a.r.randint(6, 54), a.r.randint(14, 36), G(176, 140, 56))
    return done(a)
@item(190, 80)
def hedge_long():
    a = new(190, 80, 22); shadow(a, 40)
    a.rect(3, 12, 90, 36, LEAF[1]); a.rect(3, 12, 90, 14, LEAF[2]); a.rect(3, 34, 90, 36, LEAF[0])
    for _ in range(70): a.put(a.r.randint(4, 89), a.r.randint(15, 33), a.r.choice([LEAF[0], LEAF[2], LEAF[1]]))
    return done(a)

# ---------------------------------------------------------------- houses / buildings (art footprint = collision rect; feet at the rect's bottom)
def townhouse(w, h, roof, wall, seed, chimney=True, door_c=WOOD):
    a = new(w, h, seed); shadow(a, w // 2 - 6); W, H = a.w, a.h; ry = int(H * .5)
    a.rect(2, ry, W - 3, H - 2, wall[1]); a.rect(2, ry, 4, H - 2, wall[2]); a.rect(W - 6, ry, W - 3, H - 2, wall[0])
    for y in range(ry + 5, H - 2, 6):
        for x in range(4, W - 6): a.put(x, y, wall[0]) if (x + y) % 3 == 0 else None
    for x in range(6, W - 6, 14): a.rect(x, ry, x, H - 3, WOOD[0])   # timber frame
    a.rect(2, H - 5, W - 3, H - 2, STONE[1])
    for y in range(0, ry + 6):   # steep roof (trapezoid)
        t = y / (ry + 5); x0 = int(8 * (1 - t)) ; x1 = W - 1 - x0
        x0 = max(0, int((1 - t) * W * .22)) - 1
        for x in range(max(x0, 0), W - max(x0, 0)): a.put(x, y, roof[1] if (x // 3 + y // 2) % 4 else roof[0])
        a.put(max(x0, 0), y, roof[2]); a.put(W - max(x0, 0) - 1, y, roof[0])
    for y in range(3, ry + 5, 4): a.rect(max(int((1 - y / (ry + 5)) * W * .22), 0), y, W - 1 - max(int((1 - y / (ry + 5)) * W * .22), 0), y, roof[0])
    a.rect(0, ry + 4, W - 1, ry + 6, roof[2]); a.rect(0, ry + 6, W - 1, ry + 6, roof[0])
    if chimney: a.rect(int(W * .7), 2, int(W * .7) + 6, int(ry * .55), GRY[1]); a.rect(int(W * .7) - 1, 1, int(W * .7) + 7, 2, GRY[2])
    dx = W // 2 - 5; a.rect(dx, H - 26, dx + 10, H - 6, door_c[0]); a.rect(dx + 1, H - 25, dx + 9, H - 6, door_c[1]); a.put(dx + 8, H - 15, GOLD[2]); a.rect(dx - 1, H - 27, dx + 11, H - 27, STONE[2])
    for wx in (int(W * .2), int(W * .68)):
        a.rect(wx, ry + 12, wx + 8, ry + 22, G(62, 48, 40)); a.rect(wx + 1, ry + 13, wx + 7, ry + 21, G(150, 200, 226)); a.rect(wx + 4, ry + 13, wx + 4, ry + 21, G(62, 48, 40)); a.rect(wx - 1, ry + 23, wx + 9, ry + 23, WOOD[1])
    return done(a)
@item(420, 400)
def house_town_a(): return townhouse(420, 400, ROOFR, SAND, 30)
@item(420, 400)
def house_town_b(): return townhouse(420, 400, ROOFB, SAND, 31)
@item(420, 400)
def house_town_c(): return townhouse(420, 400, ROOFG, [G(166, 150, 130), G(206, 190, 164), G(236, 224, 196)], 32, door_c=WOOD)
@item(2000, 900)
def castle_front():   # royal castle facade: curtain wall, two round corner towers, central gatehouse tower with spire (art covers the 2000x900 footprint)
    a = new(2000, 900, 34); W, H = a.w, a.h; cx = W // 2
    shadow(a, 380)
    def cone(x, ytop, ybase, hw, col):
        for y in range(ytop, ybase):
            h = 3 + (y - ytop) * (hw - 3) // max(1, ybase - ytop)
            for x2 in range(x - h, x + h + 1): a.put(x2, y, col[1] if (x2 + y) % 6 else col[0])
            a.put(x - h, y, col[2]); a.put(x + h, y, col[0])
        a.rect(x - hw - 2, ybase, x + hw + 2, ybase + 2, col[2])
    def merlons(x0, x1, y):
        for i in range(x0, x1, 12): a.rect(i, y, i + 6, y + 10, GRY[1]); a.rect(i, y, i + 6, y + 1, GRY[2]); a.rect(i + 5, y + 2, i + 6, y + 10, GRY[0])
    def windows(x0, x1, y, step, skip=None):
        for x in range(x0, x1, step):
            if skip and skip(x): continue
            a.rect(x, y, x + 8, y + 26, G(24, 20, 30)); a.rect(x - 1, y - 1, x + 9, y - 1, GRY[2]); a.rect(x + 3, y + 8, x + 5, y + 10, GOLD[1]); a.rect(x - 1, y + 27, x + 9, y + 28, GRY[0])
    # curtain wall
    bricks(a, 90, 150, W - 91, H - 6, GRY, 6, 11); merlons(90, W - 100, 138)
    a.rect(90, H - 24, W - 91, H - 6, GRY[0]); a.rect(90, H - 24, W - 91, H - 24, GRY[2])
    windows(180, W - 180, 215, 100, skip=lambda x: abs(x - cx) < 190)
    windows(180, W - 180, 330, 100, skip=lambda x: abs(x - cx) < 190)
    # corner towers
    for tx in (30, W - 130):
        bricks(a, tx, 60, tx + 100, H - 4, GRY, 6, 11)
        for y in range(60, H - 4):
            a.put(tx + 1, y, GRY[2]); a.put(tx + 2, y, GRY[2]); a.put(tx + 99, y, GRY[0]); a.put(tx + 98, y, GRY[0]); a.put(tx + 97, y, GRY[0])
        merlons(tx, tx + 100, 48); cone(tx + 50, 4, 48, 56, ROOFB); a.rect(tx + 50, 0, tx + 50, 5, IRON[1]); a.rect(tx + 51, 0, tx + 58, 4, NAVY[1])
        windows(tx + 20, tx + 90, 130, 46); windows(tx + 20, tx + 90, 260, 46)
    # gatehouse
    bricks(a, cx - 130, 96, cx + 130, H - 6, GRY, 6, 11); merlons(cx - 130, cx + 130, 84)
    bricks(a, cx - 90, 30, cx + 90, 84, GRY, 6, 11); merlons(cx - 90, cx + 90, 20); cone(cx, 0, 20, 98, ROOFB)
    windows(cx - 50, cx + 60, 40, 60); windows(cx - 70, cx + 90, 150, 70)
    # royal banners
    for bx in (cx - 200, cx + 180):
        a.rect(bx, 150, bx + 20, 240, NAVY[1]); a.rect(bx, 150, bx, 240, NAVY[2]); a.rect(bx + 20, 150, bx + 20, 240, NAVY[0]); a.rect(bx + 9, 170, bx + 11, 210, GOLD[2]); a.rect(bx + 4, 184, bx + 16, 186, GOLD[2])
        for y in range(240, 252): a.rect(bx + (y - 240), y, bx + 20 - (y - 240), y, NAVY[1])
    # great gate
    gw = 44
    a.rect(cx - gw - 8, H - 190, cx + gw + 8, H - 6, GRY[2])
    for y in range(H - 216, H - 190):
        k = (H - 190 - y) // 2; a.rect(cx - gw - 8 + k, y, cx + gw + 8 - k, y, GRY[2])
    a.rect(cx - gw, H - 180, cx + gw, H - 6, G(30, 22, 18))
    for y in range(H - 206, H - 180):
        k = (H - 180 - y) // 2; a.rect(cx - gw + k, y, cx + gw - k, y, G(30, 22, 18))
    a.rect(cx - gw + 4, H - 170, cx + gw - 4, H - 6, WOOD[0])
    for y in range(H - 196, H - 170):
        k = (H - 170 - y) // 2; a.rect(cx - gw + 4 + k, y, cx + gw - 4 - k, y, WOOD[0])
    for x in range(cx - gw + 8, cx + gw - 4, 8): a.rect(x, H - 188, x, H - 6, WOOD[1])
    for y in (H - 130, H - 70): a.rect(cx - gw + 4, y, cx + gw - 4, y + 2, IRON[1])
    a.rect(cx - 1, H - 190, cx + 1, H - 6, IRON[0]); a.rect(cx - 8, H - 90, cx - 5, H - 86, GOLD[2]); a.rect(cx + 5, H - 90, cx + 8, H - 86, GOLD[2])
    for st in range(3): a.rect(cx - gw - 14 - st * 3, H - 6 + 0, cx + gw + 14 + st * 3, H - 6, GRY[1 + (st % 2)])
    return done(a)

@item(420, 290)
def barracks(): return townhouse(420, 290, [G(86, 66, 52), G(122, 92, 66), G(158, 120, 84)], [G(110, 82, 52), G(150, 114, 70), G(184, 144, 92)], 40, door_c=[G(70,50,40),G(100,72,50),G(130,96,64)])
@item(420, 290)
def stable(): return townhouse(420, 290, ROOFG, [G(120, 90, 56), G(160, 122, 76), G(194, 154, 100)], 41, chimney=False)
@item(840, 620)
def keep_front():   # fort keep: tall brick block, crenellated top, two corner turrets, arched door (art covers the 800x520 footprint + roof overhang)
    a = new(840, 620, 42); W, H = a.w, a.h; cx = W // 2; shadow(a, 150)
    def cone(x, ytop, ybase, hw, col):
        for y in range(ytop, ybase):
            h = 3 + (y - ytop) * (hw - 3) // max(1, ybase - ytop)
            for x2 in range(x - h, x + h + 1): a.put(x2, y, col[1] if (x2 + y) % 6 else col[0])
            a.put(x - h, y, col[2]); a.put(x + h, y, col[0])
    bricks(a, 14, 90, W - 15, H - 4, GRY, 6, 11)
    for i in range(14, W - 15, 12): a.rect(i, 78, i + 6, 89, GRY[1]); a.rect(i, 78, i + 6, 79, GRY[2]); a.rect(i + 5, 80, i + 6, 89, GRY[0])
    for tx in (0, W - 56):
        bricks(a, tx, 36, tx + 56, H - 2, GRY, 6, 11); cone(tx + 28, 0, 36, 34, ROOFR)
    for y in (130, 220, 310): 
        for x in (60, 130, 200, 270, W - 270, W - 200, W - 130, W - 60):
            if y > 220 and abs(x - cx) < 100: continue
            a.rect(x, y, x + 8, y + 24, G(24, 20, 30)); a.rect(x - 1, y - 1, x + 9, y - 1, GRY[2]); a.rect(x + 3, y + 6, x + 5, y + 8, GOLD[1])
    gw = 50; a.rect(cx - gw - 6, H - 150, cx + gw + 6, H - 4, GRY[2])
    for y in range(H - 180, H - 150):
        k = (H - 150 - y) // 2; a.rect(cx - gw - 6 + k, y, cx + gw + 6 - k, y, GRY[2])
    a.rect(cx - gw, H - 140, cx + gw, H - 4, WOOD[0])
    for y in range(H - 166, H - 140):
        k = (H - 140 - y) // 2; a.rect(cx - gw + k, y, cx + gw - k, y, WOOD[0])
    for x in range(cx - gw + 6, cx + gw - 2, 8): a.rect(x, H - 160, x, H - 4, WOOD[1])
    a.rect(cx - 1, H - 164, cx + 1, H - 4, IRON[0]); a.rect(cx - gw, H - 90, cx + gw, H - 88, IRON[1])
    for bx in (cx - 140, cx + 120):
        a.rect(bx, 120, bx + 18, 190, RED[1]); a.rect(bx, 120, bx, 190, RED[2]); a.rect(bx + 18, 120, bx + 18, 190, RED[0]); a.rect(bx + 8, 140, bx + 10, 175, GOLD[2]); a.rect(bx + 3, 152, bx + 15, 154, GOLD[2])
    return done(a)

def main():
    os.makedirs(OUT, exist_ok=True); rules = []; sheet = []
    for name, (fn, w, h) in ITEMS.items():
        a = fn(); size = a.png(os.path.join(OUT, name + '.png')); sheet.append((name, Image.open(os.path.join(OUT, name + '.png'))))
        assert size == (w * K, h * K), (name, size, (w * K, h * K))
        rules.append({'match': '^town_%s$' % name, 'file': 'town/%s.png' % name, 'w': w, 'h': h, 'gen': 'make_town_art'})
    m = json.load(open(MAN, encoding='utf-8')); m['node'] = [r for r in m['node'] if r.get('gen') != 'make_town_art']; m['node'][0:0] = rules
    open(MAN, 'w', encoding='utf-8').write(json.dumps(m, ensure_ascii=False, indent=1)); print('manifest: %d town rules; %d PNGs' % (len(rules), len(sheet)))
    if '--sheet' in sys.argv:
        out = sys.argv[sys.argv.index('--sheet') + 1]; Wd = 2400; x = y = 0; rh = 0; im = Image.new('RGBA', (Wd, 2400), (120, 150, 100, 255))
        for n, i in sheet:
            if x + i.width > Wd: x = 0; y += rh + 10; rh = 0
            im.alpha_composite(i, (x, y)); x += i.width + 10; rh = max(rh, i.height)
        im.crop((0, 0, Wd, y + rh)).save(out)
if __name__ == '__main__': main()
