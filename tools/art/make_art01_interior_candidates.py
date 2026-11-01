#!/usr/bin/env python3
"""DIRECTIVE-ART-01B: interior candidate tiles for Rilde houses (first target: Aidan's house).

CANDIDATES ONLY — not formal assets, not referenced by the game, not in the asset registry.
Output: docs/art/candidates/art-01/*.png (deterministic; re-running reproduces identical bytes).

Style contract (measured from the existing interior furniture in img/field/moss/rilde/furn/*.png):
  * pixel blocks of 4x4 source px (= 2x2 world px), drawn at @2x and placed at half size (manifest w/h);
  * small flat palette: outline #2b211c, wood #7c5834/#9a7042/#b88c56, gold #d6ac46, cream #f6eed8;
  * floor / wall tones keep the current map fill colours (rilde_in_aidan: wall #76654f, floor #a98b5c, base #3a2c20).
Dimensions come from the current map geometry (wall band 150 world px, baseboard 12, outer walls 48,
exit opening 140) and the procedural plank pitch in js/field/forest-layer.js (28 world px).
"""
import argparse, hashlib, json, pathlib, random
from PIL import Image

B = 4  # source px per pixel-art block (= 2 world px)

def hx(s):
    s = s.lstrip('#'); return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)) + (255,)

OUT = hx('#2b211c')
P = {k: hx(v) for k, v in dict(
    # floor (map fill #a98b5c family)
    f_dk='#6e5636', f_md='#957a50', f_bs='#a98b5c', f_b2='#a28555', f_b3='#b09263', f_lt='#bc9d6b', f_hi='#c9aa76', f_nail='#5a4630',
    # wall planks (map fill #76654f family)
    w_dk='#4f4234', w_md='#665645', w_bs='#76654f', w_b2='#705f4a', w_b3='#7c6a53', w_lt='#86745b', w_hi='#968263',
    beam_dk='#3e3024', beam='#5a4632', beam_lt='#6e573e',
    # baseboard / wall top
    bb='#3a2c20', bb_lt='#54412e', cap='#33271d', cap_lt='#4a3a2b', cap_hi='#5e4a36',
    # door threshold
    stone_dk='#6b6458', stone='#8a8274', stone_lt='#a59c8b', light='#f2dfa8', light2='#e8c97e',
    # woven mat
    mat_dk='#7c5834', mat='#9a7042', mat_lt='#b88c56', mat_g='#467448', mat_gd='#2c5236', gold='#d6ac46', cream='#f6eed8',
).items()}


class Canvas:
    """Block-addressed canvas; save() upscales by B with nearest neighbour (crisp 4px pixels)."""
    def __init__(self, bw, bh, fill=(0, 0, 0, 0)):
        self.w, self.h = bw, bh; self.px = [[fill] * bw for _ in range(bh)]
    def set(self, x, y, c, wrap=False):
        if wrap: x %= self.w; y %= self.h
        if 0 <= x < self.w and 0 <= y < self.h: self.px[y][x] = c
    def rect(self, x, y, w, h, c, wrap=False):
        for j in range(y, y + h):
            for i in range(x, x + w): self.set(i, j, c, wrap)
    def image(self):
        im = Image.new('RGBA', (self.w, self.h))
        im.putdata([c for row in self.px for c in row])
        return im.resize((self.w * B, self.h * B), Image.NEAREST)


def floor_planks():
    """112x112 world tile (224 px, 56 blocks). Vertical boards 14 blocks (=28 world, procedural pitch). Seamless both axes."""
    rnd = random.Random(101); c = Canvas(56, 56, P['f_bs'])
    tones = [P['f_bs'], P['f_b2'], P['f_b3'], P['f_b2']]
    for k in range(4):
        x0 = k * 14; tone = tones[k]
        c.rect(x0, 0, 14, 56, tone)
        # end joints: two per board, staggered, wrapping vertically
        joints = [(k * 17 + 9) % 56, (k * 17 + 9 + 28 + (k % 2) * 6) % 56]
        for j in joints:
            c.rect(x0, j, 14, 1, P['f_dk'], wrap=True)
            c.rect(x0, j + 1, 14, 1, P['f_lt'], wrap=True)
            for nx in (x0 + 2, x0 + 11):  # nail pairs beside each joint
                c.set(nx, j - 2, P['f_nail'], True); c.set(nx, j + 3, P['f_nail'], True)
        # grain streaks (short, deterministic)
        for _ in range(4):
            gx = x0 + 2 + rnd.randrange(10); gy = rnd.randrange(56); ln = 3 + rnd.randrange(5)
            col = P['f_md']
            for t in range(ln): c.set(gx, gy + t, col, True)
        # board gap: dark line + lit edge
        c.rect(x0, 0, 1, 56, P['f_dk']); c.rect(x0 + 1, 0, 1, 56, P['f_lt'])
    return c


def wall_planks():
    """112x150 world strip (224x300 px, 56x75 blocks); tiles horizontally. Vertical planks + top rail + post at the seam."""
    rnd = random.Random(202); c = Canvas(56, 75, P['w_bs'])
    for k in range(8):  # 7-block planks (14 world)
        x0 = k * 7; tone = [P['w_bs'], P['w_b2'], P['w_bs'], P['w_b3']][k % 4]
        c.rect(x0, 0, 7, 75, tone)
        c.rect(x0, 0, 1, 75, P['w_dk'])
        for _ in range(2):
            gx = x0 + 2 + rnd.randrange(4); gy = 16 + rnd.randrange(50); ln = 3 + rnd.randrange(5)
            for t in range(ln): c.set(gx, gy + t, P['w_md'] if tone != P['w_md'] else P['w_dk'])
    # ceiling shadow and top rail beam
    c.rect(0, 0, 56, 3, P['beam_dk']); c.rect(0, 3, 56, 1, OUT)
    c.rect(0, 9, 56, 5, P['beam']); c.rect(0, 9, 56, 1, P['beam_lt']); c.rect(0, 14, 56, 1, OUT); c.rect(0, 15, 56, 1, P['w_dk'])
    # mid rail
    c.rect(0, 46, 56, 3, P['beam']); c.rect(0, 46, 56, 1, P['beam_lt']); c.rect(0, 49, 56, 1, OUT)
    # timber post on the tile seam (x=0, wraps visually because the next tile starts with it)
    c.rect(0, 0, 4, 75, P['beam']); c.rect(1, 0, 1, 75, P['beam_lt']); c.rect(3, 0, 1, 75, P['beam_dk']); c.rect(4, 0, 1, 75, OUT)
    for y in (11, 47):  # pegs where rails meet the post
        c.set(2, y, P['gold'] if y == 11 else P['beam_lt'])
    # lower wall in shade (floor bounce gets darker toward the baseboard)
    for y in range(70, 75):
        for x in range(56):
            if (x + y) % 2 == 0: c.set(x, y, P['w_dk'])
    return c


def baseboard():
    """112x12 world strip (224x24 px); tiles horizontally; sits on the wall/floor seam (map fill_3)."""
    c = Canvas(56, 6, P['bb'])
    c.rect(0, 0, 56, 1, P['bb_lt']); c.rect(0, 5, 56, 1, OUT)
    for x in range(0, 56, 14): c.set(x, 2, P['cap']); c.set(x, 3, P['cap'])
    return c


def wall_cap_side():
    """48x112 world (96x224 px): top of the left outer wall seen from above. Mirror horizontally for the right wall. Tiles vertically."""
    c = Canvas(24, 56, P['cap'])
    c.rect(0, 0, 24, 56, P['cap'])
    c.rect(19, 0, 1, 56, P['cap_hi']); c.rect(20, 0, 2, 56, P['cap_lt']); c.rect(22, 0, 1, 56, OUT)  # inner lit edge
    c.rect(23, 0, 1, 56, (0, 0, 0, 0))  # 1 block soft gap to the floor shadow drawn by the floor tile
    for y in range(0, 56, 14):  # log/beam joints
        c.rect(2, y, 16, 1, OUT); c.rect(2, y + 1, 16, 1, P['cap_lt'])
    for y in range(56):
        if y % 4 == 0: c.set(6 + (y // 4) % 3 * 4, y, P['cap_lt'])
    return c


def wall_cap_bottom():
    """112x48 world (224x96 px): top of the front (south) wall. Tiles horizontally. Lit edge faces the room (top)."""
    c = Canvas(56, 24, P['cap'])
    c.rect(0, 1, 56, 1, OUT); c.rect(0, 2, 56, 2, P['cap_lt']); c.rect(0, 4, 56, 1, P['cap_hi'])
    for x in range(0, 56, 14):
        c.rect(x, 6, 1, 16, OUT); c.rect(x + 1, 6, 1, 16, P['cap_lt'])
    for x in range(56):
        if x % 4 == 2: c.set(x, 12 + (x // 4) % 3 * 3, P['cap_lt'])
    c.rect(0, 0, 56, 1, (0, 0, 0, 0))
    return c


def wall_cap_corner():
    """48x48 world (96x96 px): south-west outer corner (mirror for south-east)."""
    c = Canvas(24, 24, P['cap'])
    c.rect(19, 0, 1, 2, P['cap_hi']); c.rect(20, 0, 2, 2, P['cap_lt']); c.rect(22, 0, 1, 2, OUT)
    c.rect(22, 1, 2, 1, OUT); c.rect(22, 2, 2, 2, P['cap_lt']); c.rect(22, 4, 2, 1, P['cap_hi'])
    c.rect(4, 6, 14, 1, OUT); c.rect(4, 7, 14, 1, P['cap_lt']); c.rect(10, 8, 1, 14, OUT)
    return c


def door_threshold():
    """140x48 world (280x96 px): door opening cut into the front wall over tr_exit (x 410-550, y 672-720 in rilde_in_aidan).
    Stone sill + warm daylight from outside; jambs at both ends. Opaque (it replaces the wall cap there)."""
    c = Canvas(70, 24, P['cap'])
    c.rect(5, 0, 60, 24, P['light2'])
    for y in range(0, 24):  # daylight gradient by dithering toward the room
        for x in range(5, 65):
            if y < 10 and (x + y) % 2 == 0: c.set(x, y, P['light'])
            elif y >= 10: c.set(x, y, P['light'])
    c.rect(5, 0, 60, 4, P['stone']); c.rect(5, 0, 60, 1, P['stone_lt']); c.rect(5, 4, 60, 1, P['stone_dk'])
    for x in range(5, 65, 10): c.set(x, 1, P['stone_dk']); c.set(x, 2, P['stone_dk'])
    for x0 in (0, 65):  # door jambs (timber)
        c.rect(x0, 0, 5, 24, P['beam']); c.rect(x0 + (4 if x0 == 0 else 0), 0, 1, 24, OUT)
        c.rect(x0 + (1 if x0 == 0 else 2), 0, 1, 24, P['beam_lt']); c.rect(x0 + 2, 3, 1, 1, P['gold'])
    c.rect(0, 0, 70, 1, OUT)
    return c


def doormat_woven():
    """84x36 world (168x72 px) — same footprint as furn_doormat; woven green/brown mat with gold border, transparent outside."""
    c = Canvas(42, 18)
    c.rect(1, 1, 40, 16, OUT)
    c.rect(2, 2, 38, 14, P['mat_g'])
    c.rect(2, 2, 38, 1, P['gold']); c.rect(2, 15, 38, 1, P['gold']); c.rect(2, 2, 1, 14, P['gold']); c.rect(39, 2, 1, 14, P['gold'])
    for y in range(4, 14):
        for x in range(4, 38):
            if (x // 2 + y) % 4 == 0: c.set(x, y, P['mat_gd'])
            elif (x // 2 + y) % 4 == 2: c.set(x, y, P['mat_dk'])
    c.rect(18, 7, 6, 4, P['mat_lt']); c.rect(19, 8, 4, 2, P['gold'])
    for x in range(3, 40, 3):  # fringe
        c.set(x, 0, P['cream']); c.set(x, 17, P['cream'])
    return c


class Mirror:
    def __init__(self, c): self.c = c
    def image(self): return self.c.image().transpose(Image.FLIP_LEFT_RIGHT)


SPECS = [
    # file, builder, world w, world h, category, alpha, notes
    ('art01_int_floor_planks_01.png', floor_planks, 112, 112, 'tile', 'opaque', 'floor fill; repeat both axes'),
    ('art01_int_wall_planks_01.png', wall_planks, 112, 150, 'tile', 'opaque', 'back wall band (rilde interiors: 150 world high); repeat X'),
    ('art01_int_baseboard_01.png', baseboard, 112, 12, 'tile', 'opaque', 'wall/floor seam strip (fill_3); repeat X'),
    ('art01_int_wallcap_left_01.png', wall_cap_side, 48, 112, 'tile', 'alpha', 'left (west) outer wall top; repeat Y'),
    ('art01_int_wallcap_right_01.png', lambda: Mirror(wall_cap_side()), 48, 112, 'tile', 'alpha', 'right (east) outer wall top = mirrored left; repeat Y'),
    ('art01_int_wallcap_bottom_01.png', wall_cap_bottom, 112, 48, 'tile', 'alpha', 'front wall top; repeat X'),
    ('art01_int_wallcap_corner_sw_01.png', wall_cap_corner, 48, 48, 'tile', 'opaque', 'south-west outer corner'),
    ('art01_int_wallcap_corner_se_01.png', lambda: Mirror(wall_cap_corner()), 48, 48, 'tile', 'opaque', 'south-east outer corner = mirrored SW'),
    ('art01_int_door_threshold_01.png', door_threshold, 140, 48, 'object', 'opaque', 'front-wall door opening over tr_exit'),
    ('art01_furn_doormat_woven_01.png', doormat_woven, 84, 36, 'object', 'alpha', 'alternative to furn_doormat (same footprint)'),
]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='docs/art/candidates/art-01'); a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True); meta = []
    for name, fn, ww, wh, cat, alpha, note in SPECS:
        im = fn().image()
        assert im.size == (ww * 2, wh * 2), (name, im.size)
        im.save(out / name, optimize=False)
        meta.append(dict(file=name, px=list(im.size), world=[ww, wh], category=cat, alpha=alpha, note=note,
                         sha256=hashlib.sha256((out / name).read_bytes()).hexdigest()))
    (out / 'candidates.json').write_text(json.dumps(dict(status='CANDIDATE (not adopted)', directive='DIRECTIVE-ART-01B', items=meta), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for m in meta: print(m['file'], m['px'], m['sha256'][:12])


if __name__ == '__main__':
    main()
