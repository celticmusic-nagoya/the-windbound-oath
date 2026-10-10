#!/usr/bin/env python3
"""Mob NPC "少年剣士" (boy swordsman at the training ground): idle + 6-frame wooden-sword attack loop, generated pixel art.
Spec: 1 art dot = 2 world px (= 4 image px), feet bottom-centre, 1 frame = 1 transparent RGBA PNG, all frames share one canvas (72x64 world px).
Writes img/field/lind/npc/villagers/boy_swordsman_idle.png + boy_swordsman_attack_01..06.png and registers their bounds
(js/field/lind-content-bounds.js). Faces RIGHT; the field flips it via actor.direction. Not the protagonist: no battle-manifest use.
usage: python3 tools/lind/make_swordboy.py"""
import os, re, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'moss'))
from make_props import Art, INK, WOOD
import numpy as np
ROOT = os.path.join(os.path.dirname(__file__), '..', '..'); OUT = os.path.join(ROOT, 'img/field/lind/npc/villagers/')
SKIN = (244, 208, 170, 255); HAIR = (92, 62, 40, 255); TUNIC = (88, 148, 96, 255); TUNIC_D = (62, 112, 72, 255); PANTS = (118, 92, 66, 255); BOOT = (84, 58, 38, 255); BAND = (190, 60, 52, 255)
FLASH = (255, 250, 232, 255); FLASH2 = (255, 240, 200, 200)
W, H = 72, 64
# per frame: sword angle (deg, 0 = forward/right, -90 = up, +90 = down), body lean (art px), front-foot step, slash arc range
POSES = [dict(a=-25, lean=0, step=0, arc=None), dict(a=-80, lean=0, step=0, arc=None), dict(a=-140, lean=-1, step=0, arc=None),
         dict(a=-30, lean=1, step=1, arc=(-110, -30)), dict(a=45, lean=2, step=2, arc=(-30, 50)), dict(a=15, lean=1, step=1, arc=None)]
IDLE = dict(a=60, lean=0, step=0, arc=None)
def line(a, x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1): a.put(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)
def boy(p):
    a = Art(W, H, 7); cx = a.w // 2; bot = a.h - 2; lean = p['lean']
    a.shadow(cx + p['step'] // 2, bot + 1, 7)
    legs_top = bot - 5; body_top = legs_top - 6; head_top = body_top - 8
    # legs: rear foot planted, front foot steps forward on the strike
    a.rect(cx - 3, legs_top, cx - 2, bot - 2, PANTS); a.rect(cx - 4, bot - 1, cx - 1, bot, BOOT)
    fx = cx + 1 + p['step']; a.rect(fx, legs_top, fx + 1, bot - 2, PANTS); a.rect(fx, bot - 1, fx + 3, bot, BOOT)
    # torso (leans with the swing) + belt
    for y in range(body_top, legs_top + 1):
        sh = lean * (legs_top - y) // 6
        for x in range(cx - 3 + sh, cx + 3 + sh): a.put(x, y, TUNIC if x > cx - 3 + sh else TUNIC_D)
    a.rect(cx - 3 + lean // 2, legs_top - 1, cx + 2 + lean // 2, legs_top - 1, WOOD[0])
    sx, sy = cx + 1 + lean, body_top + 2                                    # shoulder (front arm)
    # head: side view facing right
    hx = cx + lean + 1
    for y in range(head_top, body_top + 1):
        for x in range(hx - 3, hx + 3): a.put(x, y, SKIN)
    for y in range(head_top - 1, head_top + 3):
        for x in range(hx - 4, hx + 3): a.put(x, y, HAIR)
    a.rect(hx - 4, head_top + 1, hx + 2, head_top + 1, BAND); a.put(hx - 5, head_top + 2, BAND); a.put(hx - 6, head_top + 3, BAND)   # headband + tail
    a.put(hx + 1, head_top + 4, INK); a.put(hx + 1, head_top + 5, INK)       # eye
    a.put(hx - 3, head_top + 3, HAIR); a.put(hx - 3, head_top + 4, HAIR)      # side hair
    a.put(hx - 2, head_top + 5, (232, 150, 130, 255))                       # blush
    # arm + wooden sword
    r = math.radians(p['a']); hx_, hy_ = round(sx + math.cos(r) * 3), round(sy + math.sin(r) * 3 + 1)
    line(a, sx, sy, hx_, hy_, SKIN if False else TUNIC_D); a.put(hx_, hy_, SKIN)
    tx, ty = round(hx_ + math.cos(r) * 12), round(hy_ + math.sin(r) * 12)
    line(a, hx_, hy_, tx, ty, WOOD[2]); line(a, hx_ + 1, hy_, tx + 1, ty, WOOD[1]) if abs(math.sin(r)) < .5 else line(a, hx_, hy_ + 1, tx, ty + 1, WOOD[1])
    gx, gy = round(hx_ + math.cos(r) * 2), round(hy_ + math.sin(r) * 2)         # crossguard
    line(a, gx - round(math.sin(r)), gy + round(math.cos(r)), gx + round(math.sin(r)), gy - round(math.cos(r)), WOOD[0])
    a.put(tx, ty, WOOD[0])
    a.outline()
    if p['arc']:                                                              # slash flash drawn after the outline so it stays soft
        t0, t1 = p['arc']
        for d in range(t0, t1 + 1, 6):
            rr = math.radians(d)
            for rad in (13, 14): a.put(round(sx + math.cos(rr) * rad), round(sy + math.sin(rr) * rad), FLASH if rad == 13 else FLASH2)
    return a
def main():
    from PIL import Image
    bounds = {}
    for name, p in [('boy_swordsman_idle', IDLE)] + [('boy_swordsman_attack_%02d' % (i + 1), q) for i, q in enumerate(POSES)]:
        a = boy(p); path = OUT + name + '.png'; a.png(path); im = Image.open(path)
        assert im.size == (W * 2, H * 2) and im.mode == 'RGBA', im.size
        al = np.array(im)[..., 3] > 16; ys, xs = np.where(al)
        bounds[name] = [im.width, im.height, int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]
    p = os.path.join(ROOT, 'js/field/lind-content-bounds.js'); s = open(p, encoding='utf-8').read()
    s = re.sub(r',\n  "boy_swordsman_[a-z_0-9]+": \[[^\]]*\]', '', s)
    add = ''.join(',\n  "%s": [\n    %s\n  ]' % (k, ',\n    '.join(map(str, b))) for k, b in bounds.items())
    i = s.rindex('\n};'); open(p, 'w', encoding='utf-8').write(s[:i] + add + s[i:])
    print('idle bounds', bounds['boy_swordsman_idle'], '-> registry height for 2 world px/dot =', bounds['boy_swordsman_idle'][5] / 2)
main()
