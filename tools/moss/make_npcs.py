#!/usr/bin/env python3
"""Stand-in NPC / furniture sprites for the fort and capital maps: front-facing 2.5-head chibi, warm retro pixel look, one transparent PNG each
(1 art pixel = 2 world px = 4 image px, feet bottom-centre). Registered as manifest node rules for asset ids npc_slot_<look>
(the map props that mark NPC slots, see tools/moss/build_town_maps.py). Replace any of them with hand-drawn art by editing manifest.json only.
usage: python3 tools/moss/make_npcs.py"""
import json, os, random, sys, zlib
sys.path.insert(0, os.path.dirname(__file__))
from make_props import Art, INK, WOOD, STONE, MOSS, ROPE, S, K
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'img/field/moss/props'); MAN = os.path.join(ROOT, 'img/field/moss/manifest.json')
SKIN = [(244, 208, 170, 255), (226, 178, 138, 255), (204, 150, 112, 255)]
def shade(c, f): return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)

# 6-frame walk cycle: (lift of the left foot, lift of the right foot, body bob, arm swing) in art px; frame 0 = idle contact pose
WALK = [(0, 0, 0, 0), (2, 0, 1, 1), (1, 0, 0, 0), (0, 0, 0, 0), (0, 2, 1, -1), (0, 1, 0, 0)]
def chibi(look, W=56, H=84, step=None):
    L = LOOKS[look]; a = Art(W, H, zlib.crc32(look.encode()) % 997); cx = a.w // 2; bot = a.h - 2
    lL, lR, bob, arm = WALK[step] if step is not None else (0, 0, 0, 0)
    sc = L.get('scale', 1.0); hh = int(12 * sc); bh = int(10 * sc); lh = int(6 * sc)
    a.shadow(cx, bot + 1, int(8 * sc))
    legs_top = bot - lh - bob; body_top = legs_top - bh; head_top = body_top - hh + 2
    skin = L.get('skin', SKIN[0]); cloth = L['cloth']; trim = L.get('trim', shade(cloth, .7))
    # legs + boots
    for dx, lf in ((-3, lL), (2, lR)):
        a.rect(cx + dx, legs_top, cx + dx + 2, bot - 2 - lf, L.get('legs', shade(cloth, .6))); a.rect(cx + dx - 1, bot - 2 - lf, cx + dx + 3, bot - lf, L.get('boots', (84, 58, 38, 255)))
    # body (trapezoid) + arms
    for y in range(body_top, legs_top + 1):
        t = (y - body_top) / max(1, legs_top - body_top); half = int(5 * sc + 2 * t * sc)
        for x in range(cx - half, cx + half + 1): a.put(x, y, cloth if x > cx - half else shade(cloth, 1.18))
    a.rect(cx - int(5 * sc), legs_top - 2, cx + int(5 * sc), legs_top - 1, trim)           # belt
    if L.get('apron'): a.rect(cx - 3, body_top + 2, cx + 3, legs_top + 1, L['apron'])
    for sx in (-1, 1):                                                                 # arms
        ao = arm * sx * -1; ax = cx + sx * int(6.5 * sc); a.rect(ax - 1, body_top + 1 + ao, ax, legs_top - 2 + ao, shade(cloth, .9)); a.rect(ax - 1, legs_top - 2 + ao, ax, legs_top - 1 + ao, skin)
    # head
    for y in range(head_top, body_top + 1):
        t = (y - head_top) / max(1, body_top - head_top); half = int((6 - abs(t - .45) * 3) * sc)
        for x in range(cx - half, cx + half + 1): a.put(x, y, skin if x > cx - half else shade(skin, 1.05))
    ey = head_top + int(hh * .55)
    for ex in (-3, 2): a.put(cx + ex, ey, INK); a.put(cx + ex, ey + 1, INK)
    a.put(cx - 1, ey + 3, shade(skin, .75)); a.put(cx, ey + 3, shade(skin, .75))      # mouth
    for ex in (-4, 3): a.put(cx + ex, ey + 2, (232, 150, 130, 255))                    # blush
    hair = L.get('hair')
    if hair:
        for y in range(head_top - 1, head_top + 3):
            half = int((6 - (head_top + 3 - y) * .5) * sc)
            for x in range(cx - half, cx + half + 1): a.put(x, y, hair)
        for y in range(head_top + 3, ey): a.put(cx - int(6 * sc), y, hair); a.put(cx + int(6 * sc), y, hair)
        if L.get('longhair'):
            for y in range(ey, body_top): a.put(cx - int(6 * sc), y, hair); a.put(cx + int(6 * sc), y, hair); a.put(cx - int(6 * sc) - 1, y, hair)
    if L.get('beard'):
        for y in range(ey + 3, ey + 7):
            for x in range(cx - 4 + (y - ey - 3) // 2, cx + 5 - (y - ey - 3) // 2): a.put(x, y, L['beard'])
    if L.get('helmet'):
        for y in range(head_top - 3, head_top + 3):
            half = int((7 - max(0, head_top - y) * .6) * sc)
            for x in range(cx - half, cx + half + 1): a.put(x, y, STONE[1] if x > cx - 2 else STONE[2])
        a.rect(cx - 1, head_top - 5, cx + 1, head_top - 4, (176, 52, 48, 255))          # plume
        a.rect(cx - 7, head_top + 2, cx + 7, head_top + 2, STONE[0])
    if L.get('scarf'): a.rect(cx - 7, head_top - 1, cx + 7, head_top + 3, L['scarf']); a.rect(cx + 5, head_top + 3, cx + 8, head_top + 8, L['scarf'])
    if L.get('hat'): a.rect(cx - 8, head_top - 1, cx + 8, head_top, L['hat']); a.rect(cx - 5, head_top - 4, cx + 5, head_top - 2, L['hat'])
    if L.get('spear'):
        a.rect(cx + 11, head_top - 8, cx + 11, bot, WOOD[1]); a.rect(cx + 10, head_top - 11, cx + 12, head_top - 8, STONE[2])
    if L.get('shield'): a.rect(cx - 13, body_top, cx - 8, body_top + 7, WOOD[2]); a.rect(cx - 12, body_top + 1, cx - 9, body_top + 6, (176, 52, 48, 255))
    if L.get('bag'): a.rect(cx + 6, body_top + 3, cx + 10, body_top + 8, (150, 110, 66, 255)); a.rect(cx + 6, body_top + 3, cx + 10, body_top + 3, WOOD[0])
    if L.get('lute'): a.rect(cx + 5, body_top + 2, cx + 10, body_top + 7, WOOD[2]); a.rect(cx + 10, body_top - 3, cx + 10, body_top + 2, WOOD[0])
    if L.get('staff'): a.rect(cx + 10, head_top + 2, cx + 10, bot, WOOD[0])
    if L.get('mark'): a.rect(cx - 1, head_top - 9, cx + 1, head_top - 5, (240, 200, 70, 255)); a.put(cx, head_top - 3, (240, 200, 70, 255))   # "!" quest marker
    a.outline(); return a

R = lambda r, g, b: (r, g, b, 255)
LOOKS = {
    'soldier':    {'cloth': R(70, 96, 150), 'trim': R(200, 170, 80), 'helmet': True, 'spear': True, 'shield': True, 'skin': SKIN[1]},
    'captain':    {'cloth': R(120, 40, 44), 'trim': R(220, 190, 90), 'helmet': True, 'skin': SKIN[1], 'mark': True},
    'merchant':   {'cloth': R(156, 100, 56), 'apron': R(236, 226, 200), 'hat': R(120, 70, 44), 'hair': R(90, 60, 40), 'bag': True},
    'townsman':   {'cloth': R(92, 130, 100), 'hair': R(110, 74, 44), 'skin': SKIN[0]},
    'townswoman': {'cloth': R(176, 92, 116), 'hair': R(150, 90, 50), 'longhair': True, 'apron': R(240, 232, 214), 'skin': SKIN[0]},
    'elder':      {'cloth': R(120, 100, 150), 'hair': R(230, 230, 226), 'beard': R(230, 230, 226), 'staff': True, 'skin': SKIN[1], 'scale': .95},
    'child':      {'cloth': R(220, 170, 70), 'hair': R(70, 48, 34), 'scale': .72},
    'bard':       {'cloth': R(60, 120, 130), 'hat': R(176, 52, 48), 'hair': R(60, 44, 36), 'lute': True},
    'questgiver': {'cloth': R(150, 120, 170), 'scarf': R(230, 220, 200), 'longhair': True, 'hair': R(190, 190, 190), 'staff': True, 'mark': True, 'skin': SKIN[1]},
    'guard':      {'cloth': R(70, 96, 150), 'trim': R(200, 170, 80), 'helmet': True, 'spear': True, 'skin': SKIN[2]},
}
def bed():
    a = Art(72, 52, 5); cx = a.w // 2; bot = a.h - 2
    a.shadow(cx, bot + 1, 14)
    a.rect(cx - 15, 8, cx + 15, bot - 2, WOOD[1]); a.rect(cx - 15, 8, cx + 15, 9, WOOD[2]); a.rect(cx - 15, bot - 2, cx + 15, bot - 2, WOOD[0])   # frame
    a.rect(cx - 13, 10, cx + 13, bot - 4, (226, 220, 200, 255))                                                                                # sheet
    a.rect(cx - 13, 10, cx - 1, 15, (250, 246, 236, 255))                                                                                     # pillow
    a.rect(cx - 13, 17, cx + 13, bot - 4, (120, 60, 66, 255)); a.rect(cx - 13, 17, cx + 13, 18, (150, 84, 88, 255))                           # blanket
    a.rect(cx - 15, 3, cx - 13, bot, WOOD[0]); a.rect(cx + 13, 3, cx + 15, bot, WOOD[0])
    a.outline(); return a
def board():
    a = Art(80, 84, 6); cx = a.w // 2; bot = a.h - 2
    a.shadow(cx, bot + 1, 12)
    a.rect(cx - 15, 6, cx + 15, 36, WOOD[1]); a.rect(cx - 15, 6, cx + 15, 7, WOOD[2]); a.rect(cx - 15, 36, cx + 15, 36, WOOD[0])
    for (x0, y0, c) in ((cx - 12, 10, (236, 226, 196, 255)), (cx - 2, 12, (226, 214, 176, 255)), (cx + 6, 9, (240, 232, 206, 255)), (cx - 10, 22, (232, 220, 186, 255)), (cx + 2, 23, (238, 228, 200, 255))):
        a.rect(x0, y0, x0 + 6, y0 + 8, c); a.put(x0 + 3, y0, (176, 52, 48, 255))
        for k in range(3): a.rect(x0 + 1, y0 + 2 + k * 2, x0 + 5, y0 + 2 + k * 2, (120, 100, 80, 255))
    a.rect(cx - 13, 37, cx - 11, bot, WOOD[0]); a.rect(cx + 11, 37, cx + 13, bot, WOOD[0])
    a.outline(); return a

def main():
    rules = []; os.makedirs(OUT, exist_ok=True)
    items = {k: (lambda k=k: chibi(k), 56, 84) for k in LOOKS}
    items['bed'] = (bed, 72, 52); items['board'] = (board, 80, 84)
    for look, (fn, w, h) in items.items():
        a = fn(); size = a.png(os.path.join(OUT, 'npc_%s.png' % look)); assert size == (w * K, h * K), (look, size)
        rule = {'match': '^npc_slot_%s$' % look, 'file': 'props/npc_%s.png' % look, 'w': w, 'h': h, 'gen': 'make_npcs'}
        if look in LOOKS:   # 6-frame walk cycle next to the idle sprite: npc_<look>_walk_01..06.png (same canvas, feet bottom-centre)
            for k in range(6): chibi(look, step=k).png(os.path.join(OUT, 'npc_%s_walk_%02d.png' % (look, k + 1)))
            rule['walk'] = {'file': 'props/npc_%s_walk_{n}.png' % look, 'frames': 6}
        rules.append(rule)
    m = json.load(open(MAN, encoding='utf-8'))
    m['node'] = [r for r in m['node'] if r.get('gen') != 'make_npcs']; m['node'][0:0] = rules
    open(MAN, 'w', encoding='utf-8').write(json.dumps(m, ensure_ascii=False, indent=1)); print('wrote %d sprites + manifest rules' % len(rules))
if __name__ == '__main__': main()
