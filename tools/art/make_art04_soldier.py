#!/usr/bin/env python3
"""DIRECTIVE-ART-04C: royal soldier, front idle — CANDIDATE ONLY (not adopted, not referenced by the game).

Field spec kept from the current slot (img/field/moss/manifest.json ^npc_slot_soldier$): world 56x84, bottom-centre anchor,
source @2x = 112x168 RGBA. Existing design kept: steel kettle helmet with a red top tuft, blue tunic with a gold belt band,
spear on the right of the image, red framed shield on the left, brown boots. No new equipment is introduced.
Proportions follow the delivered villagers (SD, head ~1/3 of the height, large eyes with a highlight).
"""
import argparse, hashlib, json, pathlib
import numpy as np
from art04_pixel import *  # noqa: F401,F403

R = pathlib.Path(__file__).resolve().parents[2]
W, H = 112, 168

BLUE = ramp('#16213f', '#203260', '#2c4682', '#3a5ca3', '#4f75bd', '#6b91d2')
STEEL = ramp('#2c3036', '#464c55', '#646b75', '#848b95', '#a7aeb6', '#cdd3d8', '#eef1f2')
SKIN = ramp('#7a4a34', '#a8684a', '#c98a66', '#e3a984', '#f2c4a0', '#fbdcc0')
HAIR = ramp('#2b170d', '#43271a', '#5f3b26', '#7c5034')
BOOT = ramp('#24150d', '#3a2216', '#55331f', '#6e452b', '#8a5a39')
PANTS = ramp('#1d2030', '#2a2e44', '#3a3f5a', '#4c5270')


def m_poly(*pts): return poly_mask(W, H, pts)
def m_ell(x0, y0, x1, y1): return ellipse_mask(W, H, (x0, y0, x1, y1))
def m_rect(x0, y0, x1, y1): return rect_mask(W, H, x0, y0, x1, y1)


def soldier():
    img = Img(W, H)

    def part(mask, pal, k=5, base=.5, round_=.4, slope=.35, edge=None, light=(-.6, -.8), dither=.3):
        img.put(mask, pal, shade(mask, k=k, base=base, round_=round_, slope=slope, light=light), dither=dither)
        outline(img, mask, edge if edge is not None else pal[0])

    # spear shaft (behind the hand), right side of the image
    shaft = m_rect(86, 22, 90, 165)
    part(shaft, WOOD, k=2, light=(-.9, 0), dither=None)
    tip = m_poly((88, 2), (94, 18), (91, 24), (85, 24), (82, 18))
    part(tip, STEEL, k=3, base=.6, edge=STEEL[0])
    img.solid(m_rect(84, 23, 93, 26), BRASS[1])
    # boots + legs
    for x0 in (36, 54):
        leg = m_rect(x0 + 1, 132, x0 + 12, 152); part(leg, PANTS, k=3)
        boot = m_poly((x0, 150), (x0 + 13, 150), (x0 + 15, 160), (x0 + 15, 165), (x0 - 1, 165), (x0 - 1, 156))
        part(boot, BOOT, k=3, base=.45, slope=.4)
        img.solid(m_rect(x0 + 1, 151, x0 + 13, 153), BOOT[4])
    # tunic (trapezoid) + gold hem and belt band
    tunic = m_poly((36, 90), (68, 90), (74, 138), (30, 138))
    part(tunic, BLUE, k=7, base=.5, round_=.45, slope=.35)
    hem = m_poly((31, 133), (73, 133), (74, 139), (30, 139)); part(hem, GOLD, k=2, base=.55, slope=.3, edge=GOLD[0])
    belt = m_rect(34, 114, 71, 121); part(belt, GOLD, k=2, base=.6, slope=.35, edge=GOLD[0])
    buckle = m_rect(48, 113, 56, 122); img.solid(buckle, BRASS[3]); img.solid(m_rect(50, 115, 54, 120), BRASS[1])
    # tunic centre seam (fold) for volume
    img.solid(m_rect(52, 122, 53, 132), BLUE[1])
    # arms: right arm (image right) down to the spear hand, left arm behind the shield
    rarm = m_poly((66, 92), (74, 96), (82, 116), (76, 120), (68, 104)); part(rarm, BLUE, k=3)
    rhand = m_ell(78, 112, 90, 124); part(rhand, SKIN, k=3, base=.6, edge=SKIN[0])
    larm = m_poly((38, 92), (30, 98), (24, 112), (32, 114), (38, 104)); part(larm, BLUE, k=3)
    # shield (red, framed, brass boss) on the left of the image
    sh = m_poly((10, 98), (40, 98), (40, 126), (25, 142), (10, 126))
    part(sh, RED, k=6, base=.5, round_=.5, slope=.35, edge=RED[0])
    rim_in = m_poly((14, 102), (36, 102), (36, 124), (25, 136), (14, 124))
    rim = sh & ~rim_in; part(rim, WOOD, k=2, base=.55, slope=.3, edge=DARKWOOD[0])
    boss = m_ell(20, 110, 30, 120); part(boss, BRASS, k=3, base=.6, edge=BRASS[0])
    # neck / collar
    neck = m_rect(46, 84, 58, 92); part(neck, SKIN, k=2, base=.4, edge=SKIN[0])
    collar = m_poly((40, 88), (64, 88), (60, 95), (44, 95)); part(collar, STEEL, k=2, base=.5, edge=STEEL[0])
    # head: face oval, hair at the sides under the helmet
    hairm = m_ell(26, 46, 78, 90); part(hairm, HAIR, k=4, base=.45, edge=HAIR[0])
    face = m_ell(30, 50, 74, 90); part(face, SKIN, k=8, base=.6, round_=.4, slope=.3, edge=SKIN[1])
    ear_l = m_ell(26, 66, 34, 78); ear_r = m_ell(70, 66, 78, 78)
    for e in (ear_l, ear_r): part(e, SKIN, k=2, base=.55, edge=SKIN[1])
    # eyes (villager style: tall dark iris with a highlight), brows, nose, mouth, cheeks
    for ex in (40, 57):
        eye = m_ell(ex, 66, ex + 8, 78); img.solid(eye, HAIR[0])
        img.solid(m_rect(ex + 1, 70, ex + 7, 77), hx('#4a2c1c'))
        img.solid(m_rect(ex + 2, 68, ex + 4, 71), hx('#ffffff')); img.solid(m_rect(ex + 5, 73, ex + 6, 75), hx('#d9c2b0'))
        img.solid(m_rect(ex, 62, ex + 8, 64), HAIR[1])
    img.solid(m_rect(51, 78, 53, 80), SKIN[1])
    img.solid(m_rect(49, 83, 56, 84), hx('#8a4a3a')); img.solid(m_rect(50, 84, 55, 85), hx('#c06a58'))
    for cx in (36, 64):
        img.solid(m_rect(cx, 79, cx + 5, 81), hx('#eba08a'))
    # helmet: kettle hat (dome + wide brim) with a red tuft on top
    dome = m_ell(28, 26, 76, 70) & m_rect(0, 0, W, 58)
    part(dome, STEEL, k=7, base=.52, round_=.5, slope=.4, edge=STEEL[0])
    band = m_rect(29, 50, 75, 55); img.put(band, STEEL, np.full((H, W), .35))
    for rx in (34, 46, 58, 70): img.solid(m_rect(rx, 51, rx + 2, 53), STEEL[5])  # rivets
    brim = m_ell(16, 52, 88, 66); part(brim, STEEL, k=4, base=.45, round_=.35, slope=.4, light=(-.3, -.95), edge=STEEL[0])
    img.solid(m_ell(18, 53, 86, 58) & ~m_ell(20, 55, 84, 66), STEEL[5])   # lit rim of the brim
    tuft = m_poly((48, 28), (46, 18), (50, 10), (55, 8), (59, 13), (58, 22), (56, 28))
    part(tuft, RED, k=3, base=.55, slope=.4, edge=RED[0])
    img.solid(m_rect(47, 26, 57, 30), BRASS[2])
    return img


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='docs/art/candidates/art-04'); a = ap.parse_args()
    out = R / a.out; out.mkdir(parents=True, exist_ok=True)
    img = soldier(); name = 'art04_npc_soldier_front_idle_01.png'; img.save(out / name)
    info = dict(status='CANDIDATE (not adopted)', directive='DIRECTIVE-ART-04C', file=name, px=[W, H], world=[56, 84], anchor='bottom-centre (feet at y=165)',
                replaces='img/field/moss/props/npc_soldier.png (front idle) - same slot size', sha256=hashlib.sha256((out / name).read_bytes()).hexdigest())
    (out / 'soldier.json').write_text(json.dumps(info, ensure_ascii=False, indent=1) + '\n', encoding='utf-8'); print(info['sha256'][:10])


if __name__ == '__main__':
    main()
