#!/usr/bin/env python3
"""Fiona (フィオナ) field sprite set: supersampled vector chibi (3x -> LANCZOS), 4 directions x (idle + 6-frame walk), transparent RGBA,
one frame = one PNG on a shared 512x640 canvas, feet anchor (256,600), drawn at scale 0.1 (~46 world px tall, same class as Aidan's field art).
Canon: ~16, HUMAN ears (no elf ears), NO wings, light chestnut long wavy hair, green eyes, floral/leaf ornaments, ivory + pale/deep green + antique gold,
linen/leather textures, wooden vine staff with a green gem. Writes img/field/moss/real/fiona/*.png and js/field/fiona-field-assets.js.
usage: python3 tools/field/make_fiona.py [--sheet out.png]"""
import math, os, sys, json
from PIL import Image, ImageDraw, ImageFilter
ROOT = os.path.join(os.path.dirname(__file__), '..', '..'); OUT = os.path.join(ROOT, 'img/field/moss/real/fiona')
W, H, SS = 512, 640, 3; CX, FY = 256, 600
INK = (50, 36, 30, 255)
def c(r, g, b, a=255): return (r, g, b, a)
HAIR, HAIR_D, HAIR_L = c(198, 152, 100), c(150, 106, 66), c(236, 202, 146)
SKIN, SKIN_D = c(250, 226, 200), c(234, 190, 160)
IVORY, IVORY_D = c(246, 240, 224), c(212, 204, 184)
GRN, GRN_D, GRN_L = c(74, 118, 80), c(46, 80, 58), c(154, 190, 134)
GOLD, GOLD_D = c(220, 176, 76), c(150, 108, 40)
BRN, BRN_D, BRN_L = c(124, 84, 50), c(80, 52, 32), c(168, 120, 74)
GEM = c(120, 230, 130)

def catmull(pts, closed=True, n=14):
    out = []; m = len(pts)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0, p1, p2, p3 = (pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]) if closed else (pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, m - 1)])
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out
class Cv:
    def __init__(s): s.im = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im)
    def sc(s, pts): return [(x * SS, y * SS) for x, y in pts]
    def poly(s, pts, fill, ol=INK, w=5, smooth=True, closed=True):
        q = s.sc(catmull(pts) if smooth else pts)
        if fill: s.d.polygon(q, fill=fill)
        if ol: s.d.line(q + [q[0]] if closed else q, fill=ol, width=int(w * SS), joint='curve')
    def ell(s, cx, cy, rx, ry, fill, ol=INK, w=5):
        b = [(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS]
        s.d.ellipse(b, fill=fill, outline=ol, width=int(w * SS) if ol else 0)
    def line(s, pts, col, w, smooth=False):
        q = s.sc(catmull(pts, closed=False) if smooth else pts); s.d.line(q, fill=col, width=int(w * SS), joint='curve')
    def out(s): return s.im.resize((W, H), Image.LANCZOS)
def shadow(cv, cx=CX, w=110):
    sh = Image.new('RGBA', cv.im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.ellipse([(cx - w) * SS, (FY - 10) * SS, (cx + w) * SS, (FY + 18) * SS], fill=(24, 36, 20, 96)); sh = sh.filter(ImageFilter.GaussianBlur(5 * SS))
    cv.im.alpha_composite(sh)
def linen(cv, box, col, step=9):   # fine woven-linen hatching clipped to a shape later by the caller drawing it onto the shape layer
    pass
def flower(cv, x, y, r=17, rot=0):
    for k in range(5):
        a = rot + k * 1.2566; cv.ell(x + math.cos(a) * r * .8, y + math.sin(a) * r * .8, r * .62, r * .42, c(255, 252, 244), INK, 2.5)
    cv.ell(x, y, r * .38, r * .38, GOLD, GOLD_D, 2)
def leaf(cv, x, y, L, ang, col=GRN):
    ex, ey = x + math.cos(ang) * L, y + math.sin(ang) * L; nx, ny = -math.sin(ang) * L * .3, math.cos(ang) * L * .3
    cv.poly([(x, y), ((x + ex) / 2 + nx, (y + ey) / 2 + ny), (ex, ey), ((x + ex) / 2 - nx, (y + ey) / 2 - ny)], col, GRN_D, 3)
def staff(cv, x, top, bot, tilt=0):
    x2 = x + tilt
    cv.line([(x, bot), (x2, top)], INK, 17); cv.line([(x, bot), (x2, top)], BRN, 11); cv.line([(x - 3, bot), (x2 - 3, top)], BRN_L, 3)
    for k in range(7):   # gold vine wrap
        t = k / 7; yy = bot - (bot - top) * (.18 + t * .6); xx = x + tilt * (1 - (yy - top) / (bot - top))
        cv.line([(xx - 8, yy + 5), (xx + 8, yy - 5)], GOLD_D, 3.5); cv.line([(xx - 8, yy + 3), (xx + 8, yy - 7)], GOLD, 2)
    # crown: twisted branch ring + gem + leaves
    cx, cy = x2, top - 6
    cv.poly([(cx - 22, cy + 24), (cx - 30, cy - 6), (cx - 12, cy - 32), (cx + 12, cy - 32), (cx + 30, cy - 6), (cx + 22, cy + 24), (cx + 12, cy + 6), (cx - 12, cy + 6)], None, INK, 9)
    cv.poly([(cx - 22, cy + 24), (cx - 30, cy - 6), (cx - 12, cy - 32), (cx + 12, cy - 32), (cx + 30, cy - 6), (cx + 22, cy + 24), (cx + 12, cy + 6), (cx - 12, cy + 6)], None, BRN, 5)
    cv.poly([(cx, cy - 20), (cx + 13, cy - 2), (cx, cy + 16), (cx - 13, cy - 2)], GEM, INK, 3, smooth=False)
    cv.poly([(cx, cy - 15), (cx + 6, cy - 3), (cx, cy + 2), (cx - 5, cy - 4)], c(200, 255, 200), None, 0, smooth=False)
    leaf(cv, cx - 18, cy - 24, 30, -2.5); leaf(cv, cx + 18, cy - 24, 30, -.6); flower(cv, cx - 26, cy + 6, 12, .4)
def boot(cv, x, y, lift, side=0, face='front'):
    y -= lift
    if face == 'front':
        cv.poly([(x - 21, y - 60), (x + 21, y - 60), (x + 24, y - 24), (x + 36, y - 6), (x + 32, y + 12), (x - 32, y + 12), (x - 36, y - 6), (x - 24, y - 24)], BRN, INK, 5)
        cv.poly([(x - 22, y - 58), (x + 22, y - 58), (x + 22, y - 48), (x - 22, y - 48)], GOLD, GOLD_D, 3, smooth=False)
        cv.line([(x - 14, y - 40), (x + 14, y - 22)], GOLD_D, 3); cv.line([(x + 14, y - 40), (x - 14, y - 22)], GOLD_D, 3)
        cv.poly([(x - 30, y + 2), (x + 30, y + 2), (x + 32, y + 12), (x - 32, y + 12)], BRN_D, None, 0, smooth=False)
    else:   # side: pointing right
        cv.poly([(x - 18, y - 60), (x + 14, y - 60), (x + 16, y - 26), (x + 44, y - 8), (x + 44, y + 12), (x - 22, y + 12), (x - 24, y - 10)], BRN, INK, 5)
        cv.poly([(x - 18, y - 58), (x + 14, y - 58), (x + 14, y - 47), (x - 18, y - 47)], GOLD, GOLD_D, 3, smooth=False)
        cv.line([(x - 12, y - 38), (x + 10, y - 26)], GOLD_D, 3); cv.poly([(x - 22, y + 4), (x + 44, y + 4), (x + 44, y + 12), (x - 22, y + 12)], BRN_D, None, 0, smooth=False)
def face_front(cv, cx, cy):
    for sx in (-1, 1):
        ex = cx + sx * 34; cv.ell(ex, cy + 6, 18, 23, c(255, 255, 255), INK, 3)
        cv.ell(ex, cy + 9, 14, 19, c(86, 156, 92), None, 0); cv.ell(ex, cy + 12, 9, 12, c(38, 86, 52), None, 0)
        cv.ell(ex - 4, cy + 2, 5.5, 6.5, c(255, 255, 255), None, 0); cv.ell(ex + 5, cy + 16, 2.5, 3, c(220, 255, 220), None, 0)
        cv.line([(ex - 20, cy - 12), (ex - 4, cy - 19), (ex + 14, cy - 15), (ex + 21, cy - 6)], INK, 5, True)      # upper lash
        cv.line([(ex - 20 * -sx * .0 - 14, cy - 28 - 2 * sx), (ex + 14, cy - 30 + 2 * sx)], HAIR_D, 4, True)       # brow
        cv.ell(ex + sx * 8, cy + 36, 14, 8, c(246, 160, 150, 140), None, 0)                                         # blush
    cv.line([(cx - 11, cy + 40), (cx, cy + 46), (cx + 11, cy + 40)], c(170, 90, 80), 4, True)                         # smile
    cv.line([(cx - 2, cy + 22), (cx + 2, cy + 26)], SKIN_D, 3)
def draw(direction, t, idle=False):
    cv = Cv(); s = 0 if idle else math.sin(2 * math.pi * t); co = 0 if idle else math.cos(2 * math.pi * t)
    bob = 0 if idle else -abs(s) * 9; breathe = (math.sin(t * 6.283) * 2 if idle else 0)
    sway = 0 if idle else co * 10
    shadow(cv)
    if direction in ('down', 'up'): return front_back(cv, direction == 'up', s, co, bob, sway, idle, t)
    img = side(cv, s, co, bob, sway, idle, t)
    return img.transpose(Image.FLIP_LEFT_RIGHT) if direction == 'left' else img
def hair_back(cv, cx, top, bottom, spread, sway, back=False):
    pts = [(cx - spread * .62, top + 30), (cx - spread * .9, top + 120), (cx - spread * 1.0 + sway * .4, top + 210), (cx - spread * .92 + sway * .9, bottom - 30), (cx - spread * .65 + sway * 1.2, bottom),
           (cx - spread * .3 + sway, bottom - 26), (cx + spread * .05 + sway, bottom + 4), (cx + spread * .4 + sway, bottom - 24), (cx + spread * .7 + sway * 1.2, bottom), (cx + spread * .95 + sway * .9, bottom - 34),
           (cx + spread * 1.0 + sway * .4, top + 210), (cx + spread * .9, top + 120), (cx + spread * .62, top + 30), (cx, top - 8)]
    cv.poly(pts, HAIR, INK, 5)
    for k in range(7):    # strand highlights following the wave
        x0 = cx - spread * .75 + k * spread * .25
        cv.line([(x0, top + 60), (x0 - 6 + sway * .3, top + 150), (x0 + 8 + sway * .7, top + 240), (x0 - 4 + sway, bottom - 20)], HAIR_D if k % 2 else HAIR_L, 4, True)
def front_back(cv, back, s, co, bob, sway, idle, t):
    cx = CX; legL, legR = max(0, s) * 22, max(0, -s) * 22; by = bob
    hair_top = 150 + by
    # staff arm (viewer-left) swings against the leg
    arm = -s * 14
    cloak_c = GRN_D
    # cloak behind
    if not back:
        hair_back(cv, cx, hair_top, 440 + by, 100, sway)
        cv.poly([(cx - 88, 330 + by), (cx + 88, 330 + by), (cx + 132 + sway * .6, 520), (cx + 40, 540), (cx - 40, 540), (cx - 132 + sway * .6, 520)], GRN, INK, 5)
        cv.poly([(cx - 120 + sway * .6, 505), (cx - 132 + sway * .6, 520), (cx - 40, 540), (cx - 52, 520)], GOLD, GOLD_D, 2.5, smooth=False)
    else: hair_back(cv, cx, hair_top, 470 + by, 110, sway * .8, True)
    # legs / boots
    for sx, lf in ((-1, legL), (1, legR)): boot(cv, cx + sx * 34, FY - 8 + 0, lf, 0)
    # skirt (ivory, scalloped hem) with green overskirt
    hem = 520 + by * .5
    sk = [(cx - 52, 396 + by), (cx + 52, 396 + by), (cx + 96, hem - 30), (cx + 118, hem)]
    for k in range(6): sk.append((cx + 118 - (k + .5) * 39.3, hem + 20 + (k % 2) * -2)); sk.append((cx + 118 - (k + 1) * 39.3, hem - 4))
    sk.append((cx - 118, hem)); sk.append((cx - 96, hem - 30))
    cv.poly(sk, IVORY, INK, 5, smooth=False)
    cv.poly([(cx - 40, 400 + by), (cx + 40, 400 + by), (cx + 60, hem - 6), (cx, hem + 12), (cx - 60, hem - 6)], GRN, INK, 4)
    for k in range(5): cv.line([(cx - 52 + k * 26, 430 + by + k % 2 * 8), (cx - 48 + k * 26, hem - 14)], GOLD, 2.5)
    cv.line([(cx - 58, hem - 8), (cx, hem + 8), (cx + 58, hem - 8)], GOLD, 4, True)
    for k in range(-2, 3): cv.ell(cx + k * 22, hem + 2, 6, 6, c(255, 255, 255, 220), None, 0)
    # arms (wide white sleeves)
    for sx in (-1, 1):
        ax = cx + sx * 100; dy = arm * (-sx if sx < 0 else sx) * .0 + (arm if sx < 0 else -arm)
        cv.poly([(cx + sx * 62, 332 + by), (cx + sx * 96, 336 + by), (ax + sx * 24, 430 + dy + by), (ax + sx * 6, 458 + dy + by), (ax - sx * 22, 440 + dy + by), (cx + sx * 56, 380 + by)], IVORY, INK, 5)
        cv.line([(ax + sx * 24, 430 + dy + by), (ax + sx * 6, 458 + dy + by), (ax - sx * 22, 440 + dy + by)], GOLD, 3)
        cv.ell(ax + sx * 2, 452 + dy + by, 15, 15, SKIN, INK, 3.5)
    if not back:
        # bodice: linen blouse + leather corset with gold lacing + green mantle collar
        cv.poly([(cx - 58, 320 + by), (cx + 58, 320 + by), (cx + 66, 372 + by), (cx + 50, 412 + by), (cx - 50, 412 + by), (cx - 66, 372 + by)], IVORY, INK, 5)
        cv.poly([(cx - 46, 364 + by), (cx + 46, 364 + by), (cx + 42, 414 + by), (cx - 42, 414 + by)], BRN, INK, 4)
        for k in range(4): cv.line([(cx - 14, 372 + by + k * 10), (cx + 14, 382 + by + k * 10)], GOLD, 2.5); cv.line([(cx + 14, 372 + by + k * 10), (cx - 14, 382 + by + k * 10)], GOLD, 2.5)
        cv.poly([(cx - 62, 322 + by), (cx, 346 + by), (cx + 62, 322 + by), (cx + 70, 338 + by), (cx, 366 + by), (cx - 70, 338 + by)], GRN, INK, 4)
        cv.line([(cx - 66, 336 + by), (cx, 362 + by), (cx + 66, 336 + by)], GOLD, 2.5, True)
    else:
        cv.poly([(cx - 66, 322 + by), (cx + 66, 322 + by), (cx + 120, 520), (cx + 40, 548), (cx - 40, 548), (cx - 120, 520)], GRN, INK, 5)
        cv.line([(cx, 340 + by), (cx, 536)], GRN_D, 3); cv.poly([(cx - 20, 380 + by), (cx, 360 + by), (cx + 20, 380 + by), (cx, 410 + by)], GOLD, GOLD_D, 3)
    # staff in the viewer-left hand
    sxp = cx - 100 - 2; staff(cv, sxp, 118 + by + arm * .6, 520 + arm * .5 + by, tilt=-arm * .3)
    if not back:
        cv.poly([(cx - 8, 300 + by), (cx + 8, 300 + by), (cx + 12, 330 + by), (cx - 12, 330 + by)], SKIN_D, INK, 3)          # neck
        cv.ell(cx, 248 + by, 80, 76, SKIN, INK, 5)                                                                          # head
        for sx in (-1, 1): cv.ell(cx + sx * 79, 262 + by, 13, 19, SKIN, INK, 4); cv.ell(cx + sx * 80, 264 + by, 6, 10, SKIN_D, None, 0)   # human ears
        face_front(cv, cx, 262 + by)
        # bangs / fringe: parted at the centre, soft curtains
        cv.poly([(cx, 168 + by), (cx - 40, 172 + by), (cx - 78, 200 + by), (cx - 88, 248 + by), (cx - 70, 232 + by), (cx - 50, 214 + by), (cx - 22, 214 + by), (cx - 6, 196 + by)], HAIR, INK, 4)
        cv.poly([(cx, 168 + by), (cx + 40, 172 + by), (cx + 78, 200 + by), (cx + 88, 248 + by), (cx + 70, 232 + by), (cx + 50, 214 + by), (cx + 22, 214 + by), (cx + 6, 196 + by)], HAIR, INK, 4)
        cv.poly([(cx - 76, 214 + by), (cx - 100, 300 + by + sway * .2), (cx - 94, 372 + by + sway * .4), (cx - 78, 330 + by), (cx - 70, 262 + by)], HAIR, INK, 4)          # side locks
        cv.poly([(cx + 76, 214 + by), (cx + 100, 300 + by + sway * .2), (cx + 94, 372 + by + sway * .4), (cx + 78, 330 + by), (cx + 70, 262 + by)], HAIR, INK, 4)
        cv.poly([(cx - 70, 176 + by), (cx - 30, 150 + by), (cx + 30, 150 + by), (cx + 70, 176 + by), (cx + 40, 168 + by), (cx, 160 + by), (cx - 40, 168 + by)], HAIR_L, None, 0)
        flower(cv, cx + 64, 196 + by, 18, .2); leaf(cv, cx + 78, 202 + by, 30, .5); leaf(cv, cx + 66, 214 + by, 28, 1.3); flower(cv, cx + 86, 228 + by, 11, 1.0); flower(cv, cx - 74, 188 + by, 12, 0)
        cv.line([(cx - 60, 190 + by), (cx - 30, 176 + by)], GRN, 7); leaf(cv, cx - 60, 190 + by, 22, 3.4)
    else:
        cv.ell(cx, 248 + by, 80, 76, HAIR, INK, 5)
        cv.poly([(cx - 78, 230 + by), (cx - 40, 160 + by), (cx + 40, 160 + by), (cx + 78, 230 + by), (cx + 50, 300 + by), (cx, 330 + by), (cx - 50, 300 + by)], HAIR, INK, 4)
        cv.line([(cx, 170 + by), (cx - 10, 250 + by), (cx + 6, 320 + by)], HAIR_D, 4, True); cv.line([(cx - 40, 190 + by), (cx - 56, 270 + by)], HAIR_L, 4, True)
        flower(cv, cx + 62, 206 + by, 18, .3); leaf(cv, cx + 76, 212 + by, 28, .5); leaf(cv, cx + 64, 224 + by, 26, 1.3)
    return cv.out()
def side(cv, s, co, bob, sway, idle, t):
    cx = CX; by = bob; fl = max(0, s) * 24; bl = max(0, -s) * 24; fx = s * 46; bx = -s * 46
    # cloak trailing behind (to the left)
    cv.poly([(cx - 20, 330 + by), (cx - 30, 336 + by), (cx - 98 + sway, 480), (cx - 118 + sway * 1.4, 540), (cx - 40 + sway * .6, 548), (cx - 14, 470), (cx + 10, 370 + by)], GRN, INK, 5)
    cv.line([(cx - 118 + sway * 1.4, 540), (cx - 40 + sway * .6, 548)], GOLD, 3.5)
    hair_back(cv, cx - 28, 150 + by, 450 + by, 66, sway * 1.3)
    # back leg then front leg
    boot(cv, cx + bx - 8, FY - 8, bl, 0, 'side'); boot(cv, cx + fx - 8, FY - 8, fl, 0, 'side')
    hem = 520 + by * .5
    sk = [(cx - 40, 396 + by), (cx + 38, 396 + by), (cx + 82, hem - 26), (cx + 96, hem)]
    for k in range(4): sk.append((cx + 96 - (k + .5) * 40, hem + 18 + (k % 2) * -2)); sk.append((cx + 96 - (k + 1) * 40, hem - 4))
    sk += [(cx - 82 + sway * .3, hem), (cx - 60, hem - 34)]
    cv.poly(sk, IVORY, INK, 5, smooth=False)
    cv.poly([(cx - 26, 400 + by), (cx + 34, 400 + by), (cx + 70, hem - 8), (cx + 10, hem + 10), (cx - 40, hem - 6)], GRN, INK, 4)
    cv.line([(cx - 48, hem - 6), (cx + 8, hem + 8), (cx + 66, hem - 6)], GOLD, 4, True)
    # torso
    cv.poly([(cx - 40, 322 + by), (cx + 36, 322 + by), (cx + 42, 372 + by), (cx + 34, 412 + by), (cx - 34, 412 + by), (cx - 44, 372 + by)], IVORY, INK, 5)
    cv.poly([(cx - 34, 364 + by), (cx + 34, 364 + by), (cx + 30, 414 + by), (cx - 30, 414 + by)], BRN, INK, 4)
    for k in range(4): cv.line([(cx + 6, 372 + by + k * 10), (cx + 26, 380 + by + k * 10)], GOLD, 2.5)
    cv.poly([(cx - 44, 324 + by), (cx + 6, 346 + by), (cx + 44, 324 + by), (cx + 50, 338 + by), (cx + 6, 362 + by), (cx - 50, 338 + by)], GRN, INK, 4)
    # near arm + hand holding the staff in front
    arm = -s * 16
    cv.poly([(cx - 6, 334 + by), (cx + 34, 340 + by), (cx + 88 + arm, 420 + by), (cx + 76 + arm, 450 + by), (cx + 40 + arm, 436 + by), (cx - 6, 380 + by)], IVORY, INK, 5)
    cv.line([(cx + 88 + arm, 420 + by), (cx + 76 + arm, 450 + by), (cx + 40 + arm, 436 + by)], GOLD, 3); cv.ell(cx + 74 + arm, 452 + by, 15, 15, SKIN, INK, 3.5)
    staff(cv, cx + 76 + arm, 126 + by, 522 + by, tilt=arm * -.2)
    cv.ell(cx + 4, 248 + by, 74, 74, SKIN, INK, 5)
    cv.ell(cx - 8, 266 + by, 12, 18, SKIN, INK, 4); cv.ell(cx - 7, 268 + by, 5, 9, SKIN_D, None, 0)                      # human ear
    ex = cx + 40
    cv.ell(ex, 268 + by, 15, 22, c(255, 255, 255), INK, 3); cv.ell(ex + 3, 271 + by, 11, 18, c(86, 156, 92), None, 0); cv.ell(ex + 5, 274 + by, 7, 11, c(38, 86, 52), None, 0)
    cv.ell(ex - 1, 262 + by, 5, 6, c(255, 255, 255), None, 0)
    cv.line([(ex - 14, 252 + by), (ex, 245 + by), (ex + 14, 252 + by)], INK, 5, True); cv.line([(ex - 12, 234 + by), (ex + 14, 236 + by)], HAIR_D, 4, True)
    cv.ell(ex - 6, 298 + by, 12, 7, c(246, 160, 150, 140), None, 0); cv.line([(ex + 6, 304 + by), (ex + 22, 306 + by)], c(170, 90, 80), 4)
    cv.line([(cx + 74, 276 + by), (cx + 80, 284 + by)], SKIN_D, 3)
    # hair cap, bangs, side lock, flowers
    cv.poly([(cx - 70, 232 + by), (cx - 62, 176 + by), (cx - 20, 150 + by), (cx + 40, 156 + by), (cx + 72, 190 + by), (cx + 80, 236 + by), (cx + 58, 216 + by), (cx + 30, 200 + by), (cx - 4, 196 + by), (cx - 30, 220 + by), (cx - 40, 270 + by)], HAIR, INK, 4)
    cv.poly([(cx - 40, 170 + by), (cx, 154 + by), (cx + 44, 168 + by), (cx + 10, 170 + by), (cx - 20, 176 + by)], HAIR_L, None, 0)
    flower(cv, cx + 20, 190 + by, 18, .2); leaf(cv, cx + 36, 196 + by, 28, .5); leaf(cv, cx + 22, 208 + by, 26, 1.4); flower(cv, cx + 44, 220 + by, 10, 1.0)
    return cv.out()
DIRS = ['down', 'left', 'right', 'up']
def main():
    os.makedirs(OUT, exist_ok=True); frames = {}; sheet = []
    import numpy as np
    for d in DIRS:
        row = []
        for name, t, idle in [('idle_' + d, 0, True)] + [('walk_%s_%02d' % (d, k + 1), k / 6, False) for k in range(6)]:
            im = draw(d if d != 'right' else 'right', t, idle)
            if d == 'right': pass
            path = os.path.join(OUT, 'fiona_%s.png' % name); im.save(path, optimize=True)
            a = np.array(im)[..., 3] > 16; ys, xs = np.where(a)
            frames['fiona_' + name] = {'path': 'img/field/moss/real/fiona/fiona_%s.png' % name, 'width': W, 'height': H, 'bounds': [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)], 'anchor': [CX, FY], 'scale': 0.1}
            row.append(im)
        sheet.append(row)
    js = '/* Fiona field frames (generated by tools/field/make_fiona.py): 4 directions x (idle + 6-frame walk). Same shape as AidanFieldAssets.frames. */\nwindow.FionaFieldAssets = Object.freeze({frames: Object.freeze(' + json.dumps(frames, indent=1) + ')});\n'
    open(os.path.join(ROOT, 'js/field/fiona-field-assets.js'), 'w').write(js)
    if '--sheet' in sys.argv:
        out = sys.argv[sys.argv.index('--sheet') + 1]; w = 256; sh = Image.new('RGBA', (w * 7, 320 * 4), (84, 112, 84, 255))
        for r, row in enumerate(sheet):
            for i, im in enumerate(row): sh.alpha_composite(im.resize((w, 320)), (i * w, r * 320))
        sh.save(out)
    print('wrote', len(frames), 'frames')
if __name__ == '__main__': main()
