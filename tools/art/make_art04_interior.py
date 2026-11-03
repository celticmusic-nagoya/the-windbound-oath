#!/usr/bin/env python3
"""DIRECTIVE-ART-04B: high-detail interior candidates for rilde_in_aidan (CANDIDATES ONLY - not adopted, not referenced by the game).

Footprints are taken from the current game data so collision / event zones / anchors stay valid:
  furniture = same manifest w/h (world px), bottom-centre anchor, drawn at @2x;
  tiles = current map geometry (wall band 150, outer walls 48, exit 140) with world-origin repetition.
Output: docs/art/candidates/art-04/*.png + candidates.json (deterministic).
"""
import argparse, hashlib, json, math, pathlib
import numpy as np
from art04_pixel import *  # noqa: F401,F403

R = pathlib.Path(__file__).resolve().parents[2]


# ======================================================================= tiles
def wood_planks(w, h, pal, board, seed, vertical=True, joints=True, nails=True, contrast=.16):
    """Seamless plank field. board = board width in px; grain runs along the boards."""
    img = Img(w, h); rng = np.random.default_rng(seed)
    L = w if vertical else h; nb = L // board
    n_fine = pnoise(w, h, 2 if vertical else 64, 64 if vertical else 2, seed + 1, 3)
    n_big = pnoise(w, h, 56, 56, seed + 2, 2)
    v = np.zeros((h, w)); joint = np.zeros((h, w), bool); hil = np.zeros((h, w), bool); nail = np.zeros((h, w), bool)
    tones = rng.uniform(-.13, .13, nb)
    for k in range(nb):
        a0 = k * board
        sl = (slice(None), slice(a0, a0 + board)) if vertical else (slice(a0, a0 + board), slice(None))
        v[sl] = .52 + tones[k]
        # grain: thin darker streaks along the board, wobbling with noise
        across = np.arange(board)
        streak = (np.sin((across[None, :] if vertical else across[:, None]) * 1.7 + rng.uniform(0, 6)) * .5 + .5)
        v[sl] += (streak - .5) * .05
        # board edge: 1px dark gap + 1px lit edge
        if vertical:
            joint[:, a0] = True; hil[:, (a0 + 1) % w] = True
        else:
            joint[a0, :] = True; hil[(a0 + 1) % h, :] = True
        if joints:  # end joints: one per board per tile, staggered
            jpos = (k * 97 + 23) % (h if vertical else w)
            if vertical:
                joint[jpos, a0:a0 + board] = True; hil[(jpos + 1) % h, a0 + 1:a0 + board] = True
                if nails:
                    for nx in (a0 + 5, a0 + board - 6):
                        for ny in ((jpos - 4) % h, (jpos + 5) % h): nail[ny, nx] = True
            else:
                joint[a0:a0 + board, jpos] = True; hil[a0 + 1:a0 + board, (jpos + 1) % w] = True
    v += (n_fine - .5) * contrast * 1.4 + (n_big - .5) * .05
    full = np.ones((h, w), bool)
    img.put(full, pal, v, dither=.25)
    # fine grain lines: 1px darker strokes along each board, varied length (wrap so the tile stays seamless)
    gl = np.zeros((h, w), bool)
    for k in range(nb):
        for _ in range(6):
            off = int(rng.integers(3, board - 3)); st = int(rng.integers(0, h if vertical else w)); ln = int(rng.integers(14, 60))
            for t in range(ln):
                q = (st + t) % (h if vertical else w); wob = int(round(1.2 * math.sin((st + t) / 9.0)))
                a = k * board + min(board - 2, max(2, off + wob))
                if vertical: gl[q, a] = True
                else: gl[a, q] = True
    dark = np.clip(quant(v, pal) - 1, 0, len(pal) - 1)
    img.rgb[gl] = pal[dark][gl]
    img.solid(joint, pal[0]); img.solid(hil & ~joint, pal[min(len(pal) - 1, 5)])
    img.solid(nail, DARKWOOD[1])
    return img


def floor_tile():
    # 112x112 world -> 224x224 px; boards 28 world (current procedural pitch) = 56 px
    return wood_planks(224, 224, WOOD_FLOOR, 56, 401, vertical=True)


def wall_tile():
    """224x150 world -> 448x300 px, repeats in X. Ceiling beam, plaster panels between posts, a brace in one panel,
    mid rail, wood wainscot and its cap rail. Matches the half-timbered exterior of Aidan's house."""
    W, H = 448, 300; img = Img(W, H)
    pn = pnoise(W, H, 16, 16, 7, 3); speck = np.random.default_rng(8).random((H, W))
    plaster = np.ones((H, W), bool)
    v = .62 + (pn - .5) * .35; v -= (speck > .985) * .25; v += (speck < .01) * .15
    # ambient occlusion near beams (darker bands, no blur: hard steps)
    img.put(plaster, PLASTER, v, dither=.5)
    def beam(mask, vertical, pal=WOOD, k=4):
        g = pnoise(W, H, 4 if vertical else 40, 40 if vertical else 4, 11, 2)
        s = shade(mask, k=k, light=(-.9, -.4) if vertical else (-.2, -.98), base=.42, round_=.45, slope=.25) + (g - .5) * .22
        img.put(mask, pal, s, dither=.3); outline(img, mask, DARKWOOD[1])
    def ao(mask, px=3, amt=.18):
        ring = np.zeros_like(mask)
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            ring |= np.roll(np.roll(mask, dy * px, 0), dx * px, 1)
        ring &= ~mask
        img.rgb[ring] = (img.rgb[ring] * (1 - amt)).astype(np.uint8)
    top = rect_mask(W, H, 0, 0, W, 26)
    rail = rect_mask(W, H, 0, 176, W, 188)
    wain = rect_mask(W, H, 0, 196, W, H)
    cap = rect_mask(W, H, 0, 188, W, 198)
    posts = rect_mask(W, H, 0, 0, 20, H) | rect_mask(W, H, 224, 0, 244, 196)
    brace = poly_mask(W, H, [(244, 172), (258, 176), (434, 30), (420, 26)])
    for m in (top, rail, posts, brace): ao(m)
    # wainscot boards (vertical, darker wood)
    wb = wood_planks(W, H, WOOD, 28, 33, vertical=True, joints=False, nails=False, contrast=.12)
    img.rgb[wain] = wb.rgb[wain]; img.a[wain] = 255
    sh = np.zeros((H, W)); sh[196:206] = -.25  # wainscot top shade under the cap
    img.rgb[rect_mask(W, H, 0, 198, W, 202)] = (img.rgb[rect_mask(W, H, 0, 198, W, 202)] * .78).astype(np.uint8)
    beam(brace, False); beam(top, False, DARKWOOD, k=6); beam(rail, False); beam(posts, True)
    beam(cap, False)
    # pegs where beams meet
    for (x, y) in ((10, 13), (10, 182), (234, 13), (234, 182)):
        img.solid(rect_mask(W, H, x - 2, y - 2, x + 2, y + 2), DARKWOOD[0]); img.solid(rect_mask(W, H, x - 1, y - 2, x + 1, y - 1), WOOD[5])
    # lower edge darkening toward the floor seam
    img.rgb[rect_mask(W, H, 0, 292, W, 300)] = (img.rgb[rect_mask(W, H, 0, 292, W, 300)] * .72).astype(np.uint8)
    return img


def baseboard_tile():
    W, H = 224, 24; img = Img(W, H); m = np.ones((H, W), bool)
    g = pnoise(W, H, 40, 4, 55, 2)
    img.put(m, DARKWOOD, .5 + (g - .5) * .3 - np.linspace(-.25, .25, H)[:, None] * 1.2, dither=.3)
    img.solid(rect_mask(W, H, 0, 0, W, 2), WOOD[4]); img.solid(rect_mask(W, H, 0, H - 2, W, H), DARKWOOD[0])
    return img


def wallcap(w, h, seed, vertical):
    """Top of the outer wall seen from above: a thick dark beam with grain and a lit inner edge."""
    img = Img(w, h); m = np.ones((h, w), bool)
    g = pnoise(w, h, 4 if vertical else 40, 40 if vertical else 4, seed, 3)
    img.put(m, DARKWOOD, .38 + (g - .5) * .45, dither=.4)
    if vertical:  # inner edge on the right for the left wall
        img.solid(rect_mask(w, h, w - 8, 0, w - 4, h), DARKWOOD[4]); img.solid(rect_mask(w, h, w - 4, 0, w - 2, h), WOOD[4]); img.solid(rect_mask(w, h, w - 2, 0, w, h), EDGE)
        for y in range(0, h, 56): img.solid(rect_mask(w, h, 6, y, w - 10, y + 2), DARKWOOD[0])
    else:  # inner edge on the top for the front wall
        img.solid(rect_mask(w, h, 0, 0, w, 2), EDGE); img.solid(rect_mask(w, h, 0, 2, w, 6), WOOD[4]); img.solid(rect_mask(w, h, 0, 6, w, 10), DARKWOOD[4])
        for x in range(0, w, 56): img.solid(rect_mask(w, h, x, 14, x + 2, h - 6), DARKWOOD[0])
    return img


def flip(img):
    o = Img(img.w, img.h); o.rgb = img.rgb[:, ::-1].copy(); o.a = img.a[:, ::-1].copy(); return o


def corner(seed):
    img = wallcap(96, 96, seed, False)
    img.solid(rect_mask(96, 96, 88, 0, 92, 10), DARKWOOD[4]); img.solid(rect_mask(96, 96, 92, 0, 94, 10), WOOD[4]); img.solid(rect_mask(96, 96, 94, 0, 96, 10), EDGE)
    return img


def doorway():
    """140x48 world -> 280x96 px. Deep door frame (jambs show their thickness), worn stone sill, warm daylight outside."""
    W, H = 280, 96; img = Img(W, H)
    # daylight beyond the door: bright warm gradient, dithered bands
    out = rect_mask(W, H, 30, 0, 250, H)
    yy = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    img.put(out, ramp('#c99a55', '#ddb26a', '#ecc983', '#f6dea1', '#fcefc6', '#fffae6'), .25 + yy * .8, dither=.8)
    # stone sill (two worn slabs)
    for i, (x0, x1) in enumerate(((30, 140), (140, 250))):
        m = rect_mask(W, H, x0, 0, x1, 20)
        g = pnoise(W, H, 8, 8, 70 + i, 3)
        img.put(m, STONE, shade(m, k=4, base=.6, round_=.3, slope=.3) + (g - .5) * .3, dither=.4); outline(img, m, STONE[0])
    # door jambs with visible thickness (inner face lit on the left jamb, shaded on the right)
    for x0, face_left in ((0, True), (250, False)):
        jamb = rect_mask(W, H, x0, 0, x0 + 30, H)
        g = pnoise(W, H, 4, 40, 90 + x0, 2)
        img.put(jamb, WOOD, shade(jamb, k=5, light=(-.95, -.3), base=.4, round_=.4, slope=.2) + (g - .5) * .25, dither=.3)
        face = rect_mask(W, H, x0 + (22 if face_left else 0), 0, x0 + (30 if face_left else 8), H)
        img.put(face, WOOD, np.full((H, W), .78 if face_left else .3), dither=None)
        outline(img, jamb, DARKWOOD[0])
        for y in (18, 70):  # iron hinge straps on the jambs
            img.solid(rect_mask(W, H, x0 + 6, y, x0 + 22, y + 5), IRON[1]); img.solid(rect_mask(W, H, x0 + 7, y, x0 + 21, y + 1), IRON[3])
    img.solid(rect_mask(W, H, 0, 0, W, 2), EDGE)
    return img


# ======================================================================= furniture (@2x of the current manifest footprint)
def window():
    """furn_window_wall 64x76 world -> 128x152. Timber frame, 4 panes with sky + soft reflection, sill, light spill."""
    W, H = 128, 152; img = Img(W, H)
    frame = rect_mask(W, H, 6, 4, 122, 138)
    g = pnoise(W, H, 4, 30, 101, 2)
    img.put(frame, WOOD, shade(frame, k=6, base=.48, round_=.4, slope=.3) + (g - .5) * .2, dither=.3); outline(img, frame, DARKWOOD[0])
    glass = rect_mask(W, H, 20, 18, 108, 124)
    yy = np.linspace(0, 1, H)[:, None] * np.ones((1, W)); xx = np.ones((H, 1)) * np.linspace(0, 1, W)[None, :]
    img.put(glass, GLASS, .95 - yy * .7 + (pnoise(W, H, 32, 16, 102, 2) - .5) * .15, dither=.7)
    refl = poly_mask(W, H, [(28, 112), (40, 112), (82, 22), (70, 22)]) & glass
    img.put(refl, GLASS, np.full((H, W), 1.0)); refl2 = poly_mask(W, H, [(46, 112), (50, 112), (92, 22), (88, 22)]) & glass
    img.put(refl2, GLASS, np.full((H, W), .9))
    for m in (rect_mask(W, H, 60, 18, 68, 124), rect_mask(W, H, 20, 66, 108, 74)):  # mullions
        img.put(m, WOOD, shade(m, k=3, base=.55, round_=.4, slope=.3)); outline(img, m, DARKWOOD[1])
    inner = rect_mask(W, H, 18, 16, 110, 126) & ~rect_mask(W, H, 20, 18, 108, 124)
    img.solid(inner, DARKWOOD[1])
    sill = rect_mask(W, H, 0, 132, W, 146)
    img.put(sill, WOOD, shade(sill, k=4, light=(-.2, -.98), base=.55, round_=.4, slope=.4), dither=.3); outline(img, sill, DARKWOOD[0])
    img.solid(rect_mask(W, H, 2, 133, W - 2, 135), WOOD[6])
    return img


def stones(img, mask, seed, pal=STONE, cell=(26, 18)):
    """Irregular masonry inside mask: offset courses, each stone its own tone and volume, dark mortar."""
    H, W = mask.shape; rng = np.random.default_rng(seed); g = pnoise(W, H, 6, 6, seed + 1, 3)
    mortar = mask.copy(); img.solid(mask, pal[0])
    y = 0; row = 0
    while y < H:
        ch = cell[1] + int(rng.integers(-3, 4)); x = -int(rng.integers(0, cell[0]))
        while x < W:
            cw = cell[0] + int(rng.integers(-6, 9))
            m = rect_mask(W, H, x + 1, y + 1, x + cw - 1, y + ch - 1) & mask
            if m.sum() > 12:
                t = rng.uniform(-.2, .14)
                img.put(m, pal, shade(m, k=4, base=.55 + t, round_=.45, slope=.35) + (g - .5) * .25, dither=.35)
                mortar &= ~m
            x += cw
        y += ch; row += 1
    return mortar


def fireplace():
    """furn_fireplace 152x136 world -> 304x272. Stone hearth with arch, logs and a layered fire, wooden mantel."""
    W, H = 304, 272; img = Img(W, H)
    body = rect_mask(W, H, 8, 30, 296, 268)
    stones(img, body, 211)
    outline(img, body, STONE[0])
    # mantel beam
    mant = rect_mask(W, H, 0, 22, W, 46)
    img.put(mant, WOOD, shade(mant, k=5, light=(-.2, -.98), base=.5, round_=.45, slope=.35) + (pnoise(W, H, 50, 4, 212, 2) - .5) * .2, dither=.3)
    outline(img, mant, DARKWOOD[0]); img.solid(rect_mask(W, H, 2, 23, W - 2, 25), WOOD[6])
    # small items on the mantel: candle + jug
    img.put(rect_mask(W, H, 40, 6, 48, 22), CREAM, np.full((H, W), .85)); img.solid(rect_mask(W, H, 43, 2, 45, 6), FIRE[5])
    jug = ellipse_mask(W, H, (246, 4, 268, 24)); img.put(jug, RED, shade(jug, k=4, base=.5), dither=.3); outline(img, jug, RED[0])
    # arch opening
    arch = rect_mask(W, H, 62, 120, 242, 268) | ellipse_mask(W, H, (62, 70, 242, 170))
    ring = arch.copy()
    for dx, dy in ((0, -8), (8, 0), (-8, 0)):
        ring |= np.roll(np.roll(arch, dy, 0), dx, 1)
    ring &= body & ~arch
    img.put(ring, STONE, shade(ring, k=3, base=.7, round_=.3, slope=.3), dither=.3)
    yy = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    img.put(arch, ramp('#0b0706', '#160e0a', '#24150d', '#3a1f10', '#5a2b12'), .1 + yy * .5, dither=.6)
    # warm glow on the inner back wall (hard bands)
    glow = ellipse_mask(W, H, (92, 150, 212, 262)) & arch
    img.put(glow, ramp('#3a1f10', '#5a2b12', '#7a3814'), shade(glow, k=8, base=.4, round_=.8, slope=0), dither=.6)
    # logs
    for (x0, y0, x1, y1, s) in ((92, 230, 214, 258, 213), (108, 214, 200, 240, 214)):
        lg = ellipse_mask(W, H, (x0, y0, x1, y1)); img.put(lg, DARKWOOD, shade(lg, k=4, base=.5, round_=.4, slope=.4) + (pnoise(W, H, 30, 3, s, 2) - .5) * .3, dither=.3)
        outline(img, lg, DARKWOOD[0]); end = ellipse_mask(W, H, (x1 - 12, y0 + 2, x1 - 2, y1 - 2)); img.put(end, WOOD, np.full((H, W), .7))
    # fire: layered flame tongues
    rng = np.random.default_rng(215)
    def flame(cx, base_y, hgt, wid, layer):
        pts = [(cx - wid, base_y)]
        for t in np.linspace(0, 1, 9)[1:-1]:
            pts.append((cx - wid * (1 - t) + rng.uniform(-3, 3), base_y - hgt * t * (0.9 + .2 * math.sin(t * 7))))
        pts.append((cx + rng.uniform(-4, 4), base_y - hgt))
        for t in np.linspace(1, 0, 9)[1:-1]:
            pts.append((cx + wid * (1 - t) + rng.uniform(-3, 3), base_y - hgt * t * (0.85 + .2 * math.cos(t * 6))))
        pts.append((cx + wid, base_y))
        return poly_mask(W, H, pts) & arch
    for layer, (pal_lo, scale) in enumerate(((0, 1.0), (2, .78), (4, .55), (5, .32))):
        for cx, hh, ww in ((128, 96, 26), (156, 118, 30), (184, 88, 24), (142, 70, 18), (170, 76, 18)):
            m = flame(cx, 240, hh * scale, ww * scale, layer)
            img.solid(m, FIRE[min(6, pal_lo + 1)])
    img.solid(flame(156, 240, 30, 10, 9), FIRE[6])
    # iron pot hook
    img.solid(rect_mask(W, H, 152, 120, 156, 150), IRON[1]); img.solid(rect_mask(W, H, 146, 150, 162, 154), IRON[2])
    # hearth floor slab
    slab = rect_mask(W, H, 30, 256, 274, 270); img.put(slab, STONE, shade(slab, k=3, base=.6, round_=.3, slope=.3), dither=.3); outline(img, slab, STONE[0])
    return img


def celtic_band(img, x0, y0, x1, y1, pal_bg, pal_fg, step=12):
    """Simple interlace border: alternating gold knots on a dark band (readable at phone size)."""
    H, W = img.h, img.w; band = rect_mask(W, H, x0, y0, x1, y1); img.put(band, pal_bg, np.full((H, W), .25))
    cy = (y0 + y1) // 2; r = max(2, (y1 - y0) // 2 - 2)
    for x in range(x0 + step // 2, x1 - 2, step):
        k = ellipse_mask(W, H, (x - r, cy - r, x + r, cy + r)) & ~ellipse_mask(W, H, (x - r + 2, cy - r + 2, x + r - 2, cy + r - 2))
        img.put(k, pal_fg, np.full((H, W), .75))
        if x + step < x1 - 2: img.solid(rect_mask(W, H, x + r - 1, cy - 1, x + step - r + 1, cy + 1), pal_fg[2])


def bed():
    """furn_bed 124x92 world -> 248x184. Carved headboard, cream pillow, green quilt with a gold Celtic border."""
    W, H = 248, 184; img = Img(W, H)
    frame = rect_mask(W, H, 10, 26, 238, 178)
    img.put(frame, WOOD, shade(frame, k=6, base=.45, round_=.4, slope=.3) + (pnoise(W, H, 40, 6, 301, 2) - .5) * .2, dither=.3); outline(img, frame, DARKWOOD[0])
    head = rect_mask(W, H, 4, 0, 244, 40)
    img.put(head, WOOD, shade(head, k=6, light=(-.3, -.95), base=.5, round_=.4, slope=.35) + (pnoise(W, H, 50, 5, 302, 2) - .5) * .2, dither=.3); outline(img, head, DARKWOOD[0])
    for px in (4, 228):
        post = rect_mask(W, H, px, 0, px + 16, 44); img.put(post, WOOD, shade(post, k=4, light=(-.9, -.3), base=.55)); outline(img, post, DARKWOOD[0])
        knob = ellipse_mask(W, H, (px + 1, -4, px + 15, 10)); img.put(knob, WOOD, shade(knob, k=4, base=.65)); outline(img, knob, DARKWOOD[0])
    celtic_band(img, 30, 14, 218, 28, DARKWOOD, GOLD, step=14)
    sheet = rect_mask(W, H, 20, 40, 228, 166)
    img.put(sheet, CREAM, shade(sheet, k=6, base=.6, round_=.3, slope=.25), dither=.4)
    pil = ellipse_mask(W, H, (34, 44, 214, 84)) & rect_mask(W, H, 34, 46, 214, 84)
    pil = rect_mask(W, H, 40, 46, 208, 82) | ellipse_mask(W, H, (32, 46, 52, 82)) | ellipse_mask(W, H, (196, 46, 216, 82))
    img.put(pil, CREAM, shade(pil, k=8, base=.66, round_=.5, slope=.35), dither=.4); outline(img, pil, CREAM[0])
    img.solid(rect_mask(W, H, 120, 58, 128, 60), CREAM[1])
    quilt = rect_mask(W, H, 18, 96, 230, 170)
    q = pnoise(W, H, 10, 10, 303, 2)
    folds = np.sin((np.arange(W)[None, :] * .9 + np.arange(H)[:, None] * 1.6) / 11.0) * .07
    img.put(quilt, GREEN, shade(quilt, k=8, base=.55, round_=.4, slope=.3) + (q - .5) * .05 + folds, dither=.3); outline(img, quilt, GREEN[0])
    fold = rect_mask(W, H, 18, 90, 230, 102); img.put(fold, CREAM, shade(fold, k=3, light=(-.2, -.98), base=.6, round_=.4, slope=.4)); outline(img, fold, CREAM[0])
    celtic_band(img, 26, 156, 222, 166, GREEN, GOLD, step=12)
    # quilt stitches (diamond grid, sparse)
    for y in range(110, 152, 14):
        for x in range(34 + (y // 14 % 2) * 14, 220, 28): img.solid(rect_mask(W, H, x, y, x + 2, y + 2), GOLD[2])
    foot = rect_mask(W, H, 8, 166, 240, 182); img.put(foot, WOOD, shade(foot, k=4, light=(-.2, -.98), base=.45)); outline(img, foot, DARKWOOD[0])
    return img


def cupboard():
    """furn_cupboard 92x116 world -> 184x232 (タンス: event position unchanged). Two panelled doors, brass pulls, carved crest."""
    W, H = 184, 232; img = Img(W, H)
    body = rect_mask(W, H, 8, 20, 176, 228)
    img.put(body, WOOD, shade(body, k=6, base=.45, round_=.35, slope=.3) + (pnoise(W, H, 6, 50, 401, 3) - .5) * .22, dither=.3); outline(img, body, DARKWOOD[0])
    crown = rect_mask(W, H, 0, 6, W, 26)
    img.put(crown, WOOD, shade(crown, k=4, light=(-.2, -.98), base=.55, round_=.45, slope=.4), dither=.3); outline(img, crown, DARKWOOD[0])
    img.solid(rect_mask(W, H, 2, 7, W - 2, 9), WOOD[6])
    crest = ellipse_mask(W, H, (74, 0, 110, 22)); img.put(crest, WOOD, shade(crest, k=4, base=.6)); outline(img, crest, DARKWOOD[0])
    knot = ellipse_mask(W, H, (84, 4, 100, 18)) & ~ellipse_mask(W, H, (87, 7, 97, 15)); img.put(knot, GOLD, np.full((H, W), .7))
    for x0 in (16, 94):
        door = rect_mask(W, H, x0, 30, x0 + 74, 206)
        img.put(door, WOOD, shade(door, k=6, base=.5, round_=.3, slope=.3) + (pnoise(W, H, 5, 60, 402 + x0, 3) - .5) * .25, dither=.3); outline(img, door, DARKWOOD[1])
        for (py0, py1) in ((42, 108), (122, 194)):
            p = rect_mask(W, H, x0 + 10, py0, x0 + 64, py1)
            img.put(p, WOOD, shade(p, k=5, light=(.6, .8), base=.45, round_=.2, slope=.3), dither=.3)  # recessed: lit from the opposite side
            outline(img, p, DARKWOOD[1])
    for x in (82, 102):
        pull = ellipse_mask(W, H, (x - 4, 112, x + 4, 122)); img.put(pull, BRASS, shade(pull, k=3, base=.6)); outline(img, pull, BRASS[0])
    base = rect_mask(W, H, 4, 206, 180, 230); img.put(base, DARKWOOD, shade(base, k=4, light=(-.2, -.98), base=.55)); outline(img, base, DARKWOOD[0])
    for fx in (12, 160):
        img.solid(rect_mask(W, H, fx, 222, fx + 12, 232), DARKWOOD[0])
    return img


SPECS = [
    # file, builder, world w, world h, kind, alpha, replaces / role
    ('art04_int_floor_planks_01.png', floor_tile, 112, 112, 'tile', 'opaque', 'floor (fill_2) — repeat XY'),
    ('art04_int_wall_timber_01.png', wall_tile, 224, 150, 'tile', 'opaque', 'back wall band (fill_1) — repeat X; beam/plaster/brace/wainscot'),
    ('art04_int_baseboard_01.png', baseboard_tile, 112, 12, 'tile', 'opaque', 'baseboard (fill_3) — repeat X'),
    ('art04_int_wallcap_left_01.png', lambda: wallcap(96, 224, 501, True), 48, 112, 'tile', 'opaque', 'west outer wall top — repeat Y'),
    ('art04_int_wallcap_right_01.png', lambda: flip(wallcap(96, 224, 501, True)), 48, 112, 'tile', 'opaque', 'east outer wall top — repeat Y'),
    ('art04_int_wallcap_bottom_01.png', lambda: wallcap(224, 96, 502, False), 112, 48, 'tile', 'opaque', 'front wall top — repeat X'),
    ('art04_int_wallcap_corner_sw_01.png', lambda: corner(503), 48, 48, 'tile', 'opaque', 'SW corner'),
    ('art04_int_wallcap_corner_se_01.png', lambda: flip(corner(503)), 48, 48, 'tile', 'opaque', 'SE corner'),
    ('art04_int_doorway_01.png', doorway, 140, 48, 'object', 'opaque', 'front-wall doorway over tr_exit (x410)'),
    ('art04_furn_window_wall_01.png', window, 64, 76, 'furniture', 'alpha', 'remake of furn_window_wall (same footprint)'),
    ('art04_furn_fireplace_01.png', fireplace, 152, 136, 'furniture', 'alpha', 'remake of furn_fireplace (same footprint)'),
    ('art04_furn_bed_01.png', bed, 124, 92, 'furniture', 'alpha', 'remake of furn_bed (same footprint)'),
    ('art04_furn_cupboard_01.png', cupboard, 92, 116, 'furniture', 'alpha', 'remake of furn_cupboard (same footprint; タンス event unchanged)'),
]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='docs/art/candidates/art-04'); a = ap.parse_args()
    out = R / a.out; out.mkdir(parents=True, exist_ok=True); meta = []
    for name, fn, ww, wh, kind, alpha, role in SPECS:
        img = fn(); assert (img.w, img.h) == (ww * 2, wh * 2), (name, img.w, img.h)
        if alpha == 'opaque': img.a[:] = 255
        img.save(out / name)
        meta.append(dict(file=name, px=[img.w, img.h], world=[ww, wh], kind=kind, alpha=alpha, role=role, anchor='bottom-centre' if kind == 'furniture' else 'top-left of rect',
                         sha256=hashlib.sha256((out / name).read_bytes()).hexdigest()))
    (out / 'candidates.json').write_text(json.dumps(dict(status='CANDIDATE (not adopted)', directive='DIRECTIVE-ART-04B', items=meta), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for m in meta: print(m['file'], m['px'], m['sha256'][:10])


if __name__ == '__main__':
    main()
