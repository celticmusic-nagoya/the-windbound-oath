"""Morwen part definitions for the back (76C) and front (77C) facings, drawn with partdraw.

Coordinates are 96x128 sprite units, centre column 48, ground row 124, laid out on the side walks' frame (74G / 75):
hat 2-40 with a ~62 px brim, face / hair to ~56, capelet 54-70, cape hem 106-114, boots to 124.
`pose` moves the skeleton joints (see RIG_SPEC): pelvis / chest / head offsets and per-leg foot row, lift and x.
Unconfirmed front-only ornaments (shoulder book crests, hair flower clips) are NOT drawn (see PARTS_SPEC.md)."""
import os, sys, glob
import numpy as np
from partdraw import Part, composite

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, '..', '..')
sys.path[:0] = [os.path.join(CAND, 'morwen-up-walk', '76B'), os.path.join(CAND, 'morwen-left-walk', '74D')]
import hdpix as HP

NEUTRAL = dict(head=(0, 0), chest=(0, 0), pelvis=(0, 0), hem=(0, 0),
               legR=dict(x=0, foot=124, lift=0), legL=dict(x=0, foot=124, lift=0), handR=0, handL=0, ribbon=0)


def ramps():
    """side-walk colour ramps (74G / 75 pixels). Purple 6 tones incl. the lavender highlight, gold 4, violet 5."""
    from PIL import Image
    from oklab import rgb2oklab, lch
    paths = (sorted(glob.glob(os.path.join(CAND, 'morwen-left-walk/74G/*_12f_[0-9][0-9]_96x128.png'))) +
             sorted(glob.glob(os.path.join(CAND, 'morwen-right-walk/75/*_12f_[0-9][0-9]_96x128.png'))))
    R = HP.side_ramps(paths)
    px = np.concatenate([np.array(Image.open(p).convert('RGBA')).reshape(-1, 4) for p in paths])
    px = px[px[:, 3] > 0][:, :3]
    L, C, h = lch(rgb2oklab(px.astype(float)))
    def ramp(m, qs):
        out = []
        for q in qs:
            t = np.percentile(L[m], q); j = np.argmin(np.abs(L[m] - t)); out.append(tuple(int(v) for v in px[m][j]))
        return out
    R['purple'] = ramp((h > 285) & (h < 335) & (C > 0.07) & (L > 0.18), [6, 22, 40, 58, 76, 92])
    R['gold'] = ramp((h > 50) & (h < 100) & (C > 0.09) & (L > 0.45), [10, 40, 70, 95])
    R['violet'] = ramp((h > 290) & (h < 330) & (C > 0.14), [8, 30, 55, 78, 95])
    return R


def T(pts, d):
    return [(x + d[0], y + d[1]) for x, y in pts]


def leg_parts(P, R, k, pose, front, xs):
    """knee socks + short boots. xs: {'R': x, 'L': x} leg centres. Socks end in a 1-px lighter band below the knee
    line (sock top); boots: shaft, buckle strap (gold) on the outer side, toe (front) or heel (back)."""
    sock, boot = P['socks'], P['boots']
    st = R['hair']                      # dark sock ramp = side walks' dark leg tones
    for side in ('R', 'L'):
        lg = pose['leg' + side]; cx = xs[side] + lg['x']; yg = lg['foot'] - lg['lift']
        top = 96 + pose['pelvis'][1]
        bt = yg - 13
        m = sock.shape('rect', [(cx - 3, top), (cx + 2, bt)])
        sock.fill(m, st, base=2)
        sock.px([(cx - 2, bt - 4), (cx - 1, bt - 4), (cx, bt - 4), (cx + 1, bt - 4)], st[3])         # sock top band (knee)
        out = 1 if (cx > 48) != front else -1                     # outer side: viewer side away from centre
        mb = boot.shape('rect', [(cx - 4, bt), (cx + 3, yg)])
        boot.fill(mb, R['purple'], base=1)
        if front:
            boot.paint(boot.shape('rect', [(cx - 4, yg - 2), (cx + 3, yg)]), R['purple'][1])        # toe cap
            for y in range(bt + 2, yg - 3, 2): boot.px([(cx - 1, y)], R['gold'][1])                # lacing
        else:
            boot.paint(boot.shape('rect', [(cx - 3, yg - 2), (cx + 2, yg)]), R['purple'][0])        # heel block
            if lg['lift'] > 1: boot.paint(boot.shape('rect', [(cx - 3, yg - 1), (cx + 2, yg)]), (17, 1, 20))  # sole
        for dy in (3, 8):
            y = bt + dy
            if y < yg - 2:
                boot.line([(cx - 4, y), (cx + 3, y)], R['purple'][0]); boot.px([(cx + (3 if out > 0 else -4), y)], R['gold'][2])


def back(k, R, pose=NEUTRAL):
    names = ['cape_lower', 'socks', 'boots', 'cape_upper', 'hands', 'bag', 'capelet', 'hair', 'hat_brim', 'hat_crown',
             'hat_ornament']
    slots = dict(cape_lower='Cape', cape_upper='Cape', capelet='Outer', socks='Legs', boots='Feet', hands='Body', bag='Bag',
                 hair='Body', hat_brim='Head', hat_crown='Head', hat_ornament='HairAccessory')
    P = {n: Part(n, k, slots[n]) for n in names}
    hd, ch, pv, hm = pose['head'], pose['chest'], pose['pelvis'], pose['hem']
    pu, gold, vio = R['purple'], R['gold'], R['violet']
    # lower cape: wide, handkerchief hem with five points, violet lining at the tips, gold border + two motifs
    lc = T([(26, 74), (70, 74), (79, 104), (73, 113), (63, 107), (48, 115), (33, 107), (23, 113), (17, 104)], (pv[0] + hm[0], pv[1]))
    m = P['cape_lower'].shape('poly', lc); P['cape_lower'].fill(m, pu, base=3)
    for tip in ((23, 113), (48, 115), (73, 113)):
        tx, ty = tip[0] + pv[0] + hm[0], tip[1] + pv[1]
        P['cape_lower'].paint(P['cape_lower'].shape('poly', [(tx - 3, ty - 4), (tx + 3, ty - 4), (tx, ty)]) & m, vio[1])
    P['cape_lower'].trim(m, gold[1], 'bottom'); P['cape_lower'].filigree(m, (gold[0], gold[2]))
    if k == 1:
        for cx in (31, 65):
            c = (cx + pv[0] + hm[0], 100 + pv[1])
            P['cape_lower'].px([(c[0] - 2, c[1]), (c[0] + 2, c[1]), (c[0], c[1] - 2), (c[0], c[1] + 2), (c[0], c[1]),
                                (c[0] - 1, c[1] - 1), (c[0] + 1, c[1] + 1), (c[0] + 1, c[1] - 1), (c[0] - 1, c[1] + 1)], gold[1], True)
    leg_parts(P, R, k, pose, False, {'R': 52, 'L': 44})
    # upper cape: narrower layer, three points, centre gold thorn line with a diamond
    uc = T([(31, 66), (65, 66), (72, 88), (61, 93), (48, 99), (35, 93), (24, 88)], (pv[0], pv[1]))
    m = P['cape_upper'].shape('poly', uc); P['cape_upper'].fill(m, pu, base=3)
    P['cape_upper'].trim(m, gold[1], 'bottom'); P['cape_upper'].filigree(m, (gold[0], gold[2]))
    cx = 48 + pv[0]
    if k == 1:
        P['cape_upper'].line([(cx, 72 + pv[1]), (cx, 94 + pv[1])], gold[0])
        P['cape_upper'].px([(cx - 1, 84 + pv[1]), (cx + 1, 84 + pv[1]), (cx, 82 + pv[1]), (cx, 86 + pv[1]),
                            (cx - 2, 78 + pv[1]), (cx + 2, 78 + pv[1]), (cx - 2, 90 + pv[1]), (cx + 2, 90 + pv[1])], gold[2], True)
        for x in (36, 60):
            P['cape_upper'].line([(x + pv[0], 74 + pv[1]), (x + (2 if x > 48 else -2) + pv[0], 88 + pv[1])], pu[1])   # folds
    else:
        P['cape_upper'].line([(cx, 74 + pv[1]), (cx, 94 + pv[1])], gold[1])
    # hands at the cape sides (white frill + skin)
    for hx, dy in ((22, pose['handL']), (73, pose['handR'])):
        y = 84 + pv[1] + dy
        P['hands'].paint(P['hands'].shape('rect', [(hx, y), (hx + 2, y + 1)]), R['white'][2])
        P['hands'].fill(P['hands'].shape('rect', [(hx, y + 2), (hx + 2, y + 4)]), R['skin'], base=2, light=False)
    # satchel on the character's right hip (viewer's right from behind) + strap over the left shoulder
    bx, by = 60 + pv[0], 78 + pv[1]
    P['bag'].line([(37 + ch[0], 58 + ch[1]), (bx + 2, by)], R['brown'][1], w=2)
    mb = P['bag'].shape('rect', [(bx - 1, by), (bx + 9, by + 10)]); P['bag'].fill(mb, R['brown'], base=1)
    P['bag'].paint(P['bag'].shape('rect', [(bx - 1, by), (bx + 9, by + 3)]), R['brown'][2])
    P['bag'].px([(bx + 4, by + 4), (bx + 4, by + 5)], gold[2])
    # capelet with the book crest (gold laurel ring) and thorn border
    cp = T([(36, 54), (60, 54), (69, 64), (68, 70), (48, 72), (28, 70), (27, 64)], ch)
    m = P['capelet'].shape('poly', cp); P['capelet'].fill(m, pu, base=2)
    P['capelet'].trim(m, gold[1], 'bottom')
    c = (48 + ch[0], 60 + ch[1])
    if k == 1:
        ring = [(c[0] + dx, c[1] + dy) for dx, dy in ((-3, 0), (-3, 1), (-2, 2), (-1, 3), (1, 3), (2, 2), (3, 1), (3, 0), (-2, -2), (2, -2))]
        P['capelet'].px(ring, gold[1], True)
        P['capelet'].px([(c[0] - 1, c[1]), (c[0], c[1]), (c[0] + 1, c[1]), (c[0] - 1, c[1] + 1), (c[0] + 1, c[1] + 1)], gold[2], True)
        P['capelet'].px([(x, 67 + ch[1]) for x in range(31 + ch[0], 66 + ch[0], 3)], gold[0], True)
    else:
        P['capelet'].px([c, (c[0] + 1, c[1])], gold[2], True)
    # bob hair (back): rounded, strands, lighter crown band, scalloped ends
    hy = hd[1]
    hp = T([(33, 42), (63, 42), (65, 50), (62, 56), (56, 57), (48, 58), (40, 57), (34, 56), (31, 50)], (hd[0], hy))
    m = P['hair'].shape('poly', hp); P['hair'].fill(m, R['hair'], base=2)
    if k == 1:
        for x in range(35, 62, 3): P['hair'].line([(x + hd[0], 46 + hy), (x + hd[0] + (1 if x > 48 else -1), 55 + hy)], R['hair'][1])
        P['hair'].px([(x + hd[0], 44 + hy) for x in range(36, 60, 2)], R['hair'][3], True)
    # hat brim (ellipse seen from above-behind) with gold rim and thorn embroidery
    bm = P['hat_brim'].shape('ellipse', T([(16, 32), (80, 50)], (hd[0], hy)))
    P['hat_brim'].fill(bm, pu, base=2)
    P['hat_brim'].trim(bm, gold[1], 'all'); P['hat_brim'].filigree(bm, (gold[0], gold[2]), 'all', 3, 5)
    if k == 1:
        inner = P['hat_brim'].shape('ellipse', T([(21, 35), (75, 47)], (hd[0], hy)))
        pad = np.pad(inner, 1); e = inner & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
        ys, xs = np.where(e); P['hat_brim'].img[ys[::2], xs[::2], :3] = gold[0]
    # crown: cone bending to the viewer's right, drooping tip, two gold laurel bands, chain + crystal
    cr = T([(34, 41), (35, 30), (39, 18), (45, 9), (52, 5), (59, 7), (65, 12), (70, 18), (74, 24), (73, 27), (68, 22),
            (63, 19), (61, 26), (62, 41)], (hd[0], hy))
    m = P['hat_crown'].shape('poly', cr); P['hat_crown'].fill(m, pu, base=2)
    for y in (30, 35):
        band = m & P['hat_crown'].shape('rect', T([(30, y), (66, y + 1)], (hd[0], hy)))
        P['hat_crown'].paint(band, gold[1])
        if k == 1:
            ys, xs = np.where(band)
            P['hat_crown'].img[ys[(xs + ys) % 3 == 0], xs[(xs + ys) % 3 == 0], :3] = gold[2]
    tip = (73 + hd[0], 27 + hy)
    P['hat_ornament'].px([(tip[0], tip[1] + 1), (tip[0], tip[1] + 2), (tip[0] + 1, tip[1] + 3)], gold[0])
    P['hat_ornament'].px([(tip[0] + 1, tip[1] + 4), (tip[0], tip[1] + 5), (tip[0] + 2, tip[1] + 5), (tip[0] + 1, tip[1] + 6),
                          (tip[0] + 1, tip[1] + 5)], vio[2])
    P['hat_ornament'].px([(tip[0] + 1, tip[1] + 7)], vio[0])
    # flower + bow + two ribbon tails on the hat's right side (viewer's right from behind)
    fx, fy = 59 + hd[0], 33 + hy
    P['hat_ornament'].fill(P['hat_ornament'].shape('ellipse', [(fx - 3, fy - 3), (fx + 3, fy + 3)]), vio, base=2)
    P['hat_ornament'].px([(fx, fy)], gold[2]); P['hat_ornament'].px([(fx - 1, fy), (fx + 1, fy), (fx, fy - 1), (fx, fy + 1)], gold[1])
    rb = pose['ribbon']
    for x0, x1 in ((fx - 1, fx + 1 + rb), (fx + 2, fx + 5 + rb)):
        P['hat_ornament'].fill(P['hat_ornament'].shape('poly', [(x0, fy + 3), (x0 + 2, fy + 3), (x1 + 1, fy + 20), (x1 - 1, fy + 21)]), vio, base=1)
    order = names
    return P, order


def front(k, R, pose=NEUTRAL):
    names = ['cape_lower', 'socks', 'boots', 'skirt', 'jacket', 'sleeves', 'hands', 'potions', 'bag', 'capelet', 'collar',
             'hair_back', 'face', 'hair_front', 'glasses', 'hat_brim', 'hat_crown', 'hat_ornament']
    slots = dict(cape_lower='Cape', socks='Legs', boots='Feet', skirt='Bottom', jacket='Inner', sleeves='Inner', hands='Body',
                 potions='Accessory', bag='Bag', capelet='Outer', collar='Inner', hair_back='Body', face='Body',
                 hair_front='Body', glasses='Accessory', hat_brim='Head', hat_crown='Head', hat_ornament='HairAccessory')
    P = {n: Part(n, k, slots[n]) for n in names}
    hd, ch, pv, hm = pose['head'], pose['chest'], pose['pelvis'], pose['hem']
    pu, gold, vio, sk, hr = R['purple'], R['gold'], R['violet'], R['skin'], R['hair']
    hx, hy = hd
    # cape seen from the front: flares out behind the arms, handkerchief points, violet lining, gold border
    lc = T([(30, 60), (66, 60), (80, 104), (74, 113), (64, 106), (58, 108), (38, 108), (32, 106), (22, 113), (16, 104)], (pv[0] + hm[0], pv[1]))
    m = P['cape_lower'].shape('poly', lc); P['cape_lower'].fill(m, pu, base=2)
    for tip in ((22, 113), (74, 113)):
        tx, ty = tip[0] + pv[0] + hm[0], tip[1] + pv[1]
        P['cape_lower'].paint(P['cape_lower'].shape('poly', [(tx - 4, ty - 6), (tx + 4, ty - 6), (tx, ty)]) & m, vio[1])
    P['cape_lower'].trim(m, gold[1], 'bottom'); P['cape_lower'].filigree(m, (gold[0], gold[2]))
    if k == 1:
        for cx in (25, 71):
            c = (cx + pv[0] + hm[0], 96 + pv[1])
            P['cape_lower'].px([(c[0] - 2, c[1]), (c[0] + 2, c[1]), (c[0], c[1] - 2), (c[0], c[1] + 2), (c[0], c[1])], gold[1], True)
    leg_parts(P, R, k, pose, True, {'R': 44, 'L': 52})
    # skirt: pleats, violet plaid panel (viewer's right), gold hem
    sp = T([(37, 78), (59, 78), (63, 98), (33, 98)], pv)
    m = P['skirt'].shape('poly', sp); P['skirt'].fill(m, pu, base=2)
    if k == 1:
        for x in range(37, 62, 3): P['skirt'].line([(x + pv[0], 81 + pv[1]), (x + pv[0] + (1 if x > 48 else -1), 97 + pv[1])], pu[0])
    pl = m & P['skirt'].shape('rect', T([(52, 82), (57, 97)], pv)); P['skirt'].fill(pl, vio, base=1, rim=False)
    if k == 1:
        P['skirt'].line(T([(52, 88), (57, 88)], pv), vio[3]); P['skirt'].line(T([(54, 82), (54, 97)], pv), vio[3])
    P['skirt'].trim(m, gold[1], 'bottom')
    # jacket: dark bodice, white shirt strip, two columns of gold buttons, belt with buckle
    jp = T([(38, 56), (58, 56), (60, 79), (36, 79)], ch)
    m = P['jacket'].shape('poly', jp); P['jacket'].fill(m, pu, base=1)
    P['jacket'].paint(P['jacket'].shape('rect', T([(47, 56), (49, 64)], ch)), R['white'][1])
    for y in (64, 68, 72): P['jacket'].px([(44 + ch[0], y + ch[1]), (52 + ch[0], y + ch[1])], gold[2])
    P['jacket'].paint(P['jacket'].shape('rect', T([(36, 77), (60, 78)], pv)), R['brown'][1])
    P['jacket'].px([(48 + pv[0], 77 + pv[1]), (49 + pv[0], 77 + pv[1]), (48 + pv[0], 78 + pv[1]), (49 + pv[0], 78 + pv[1])], gold[2])
    # sleeves + gold cuff + white frill + hands (swing 1 px opposite to the legs)
    for x0, dy in ((29, pose['handR']), (61, pose['handL'])):
        sm = P['sleeves'].shape('poly', T([(x0 + 2, 58), (x0 + 6, 58), (x0 + 6, 82 + dy), (x0, 82 + dy)], ch))
        P['sleeves'].fill(sm, pu, base=1)
        P['sleeves'].line(T([(x0, 80 + dy), (x0 + 6, 80 + dy)], ch), gold[1])
        P['hands'].paint(P['hands'].shape('rect', T([(x0, 83 + dy), (x0 + 6, 83 + dy)], ch)), R['white'][2])
        P['hands'].fill(P['hands'].shape('rect', T([(x0 + 1, 84 + dy), (x0 + 5, 87 + dy)], ch)), sk, base=2, light=False)
    # potions (two violet vials with gold caps and a chain), front-right of the belt
    for x in (53, 56):
        P['potions'].fill(P['potions'].shape('rect', T([(x, 80), (x + 1, 85)], pv)), vio, base=2, rim=False)
        P['potions'].px([(x + pv[0], 79 + pv[1]), (x + 1 + pv[0], 79 + pv[1])], gold[2])
    if k == 1: P['potions'].px([(x + pv[0], 86 + pv[1]) for x in range(49, 59, 2)], gold[1])
    # satchel on the character's right hip (viewer's left) + strap from the viewer-right shoulder
    bx, by = 28 + pv[0], 72 + pv[1]
    P['bag'].line(T([(60, 57), (37, 73)], ch), R['brown'][1], w=2)
    mb = P['bag'].shape('rect', [(bx, by), (bx + 10, by + 11)]); P['bag'].fill(mb, R['brown'], base=1)
    P['bag'].paint(P['bag'].shape('rect', [(bx, by), (bx + 10, by + 4)]), R['brown'][2])
    P['bag'].px([(bx + 5, by + 5), (bx + 5, by + 6)], gold[2])
    # capelet over the shoulders, open at the front; gold border (no shoulder crests: unconfirmed)
    for side in (-1, 1):
        cp = [(48 + side * 3, 54), (48 + side * 12, 54), (48 + side * 21, 64), (48 + side * 20, 70), (48 + side * 8, 68), (48 + side * 4, 60)]
        m = P['capelet'].shape('poly', T(cp, ch)); P['capelet'].fill(m, pu, base=2)
        P['capelet'].trim(m, gold[1], 'bottom')
    # collar frill + violet bow with the small flower
    P['collar'].paint(P['collar'].shape('rect', T([(43, 52), (53, 54)], ch)), R['white'][2])
    if k == 1: P['collar'].px([(x + ch[0], 54 + ch[1]) for x in range(43, 54, 2)], R['white'][0])
    P['collar'].fill(P['collar'].shape('poly', T([(42, 55), (48, 57), (54, 55), (54, 60), (48, 58), (42, 60)], ch)), vio, base=1)
    P['collar'].px([(48 + ch[0], 57 + ch[1])], gold[2])
    # hair behind the face (bob sides), face, bangs
    m = P['hair_back'].shape('poly', T([(33, 32), (63, 32), (65, 50), (62, 56), (56, 55), (40, 55), (34, 56), (31, 50)], (hx, hy)))
    P['hair_back'].fill(m, hr, base=2)
    fm = P['face'].shape('ellipse', T([(38, 33), (58, 52)], (hx, hy))); P['face'].fill(fm, sk, base=2, light=False, rim=False)
    P['face'].paint(fm & P['face'].shape('rect', T([(38, 49), (58, 52)], (hx, hy))), sk[1])           # chin shade
    bang = T([(36, 32), (60, 32), (60, 38), (57, 39), (54, 37), (51, 39), (48, 37), (45, 39), (42, 37), (39, 39), (36, 38)], (hx, hy))
    m = P['hair_front'].shape('poly', bang); P['hair_front'].fill(m, hr, base=2)
    for sx in (-1, 1):                                    # side locks framing the face
        lk = [(48 + sx * 10, 36), (48 + sx * 13, 36), (48 + sx * 13, 53), (48 + sx * 11, 54), (48 + sx * 10, 48)]
        P['hair_front'].fill(P['hair_front'].shape('poly', T(lk, (hx, hy))), hr, base=2)
    if k == 1:
        P['hair_front'].px([(x + hx, 34 + hy) for x in range(37, 60, 2)], hr[3], True)
        P['hair_front'].px([(x + hx, 33 + hy) for x in range(38, 59, 4)], (150, 110, 160), True)
    # eyes (violet, catch-light), round gold glasses, mouth, earrings
    g = P['glasses']
    if k == 1:
        for ex in (40, 53):
            ex += hx; ey = 40 + hy
            g.px([(ex, ey), (ex + 1, ey), (ex + 2, ey)], hr[0])                                    # lash
            g.px([(ex, ey + 1), (ex + 1, ey + 1), (ex + 2, ey + 1)], vio[0])
            g.px([(ex, ey + 2), (ex + 2, ey + 2), (ex, ey + 3), (ex + 1, ey + 3), (ex + 2, ey + 3)], vio[2])
            g.px([(ex + 1, ey + 2)], vio[1]); g.px([(ex + 1, ey + 4)], vio[4])
            g.px([(ex, ey + 1)], (255, 255, 255)); g.px([(ex + 2, ey + 3)], (240, 220, 255))
            ring = [(ex - 1, ey - 1), (ex - 2, ey), (ex - 2, ey + 1), (ex - 2, ey + 2), (ex - 2, ey + 3), (ex - 1, ey + 4),
                    (ex + 3, ey - 1), (ex + 4, ey), (ex + 4, ey + 1), (ex + 4, ey + 2), (ex + 4, ey + 3), (ex + 3, ey + 4),
                    (ex, ey - 2), (ex + 1, ey - 2), (ex + 2, ey - 2), (ex, ey + 5), (ex + 1, ey + 5), (ex + 2, ey + 5)]
            g.px(ring, gold[2])
        g.px([(47 + hx, 41 + hy), (48 + hx, 41 + hy), (49 + hx, 41 + hy)], gold[1])
        g.px([(47 + hx, 48 + hy), (48 + hx, 48 + hy)], (190, 100, 110))
        for ex in (35, 61): g.px([(ex + hx, 50 + hy), (ex + hx, 51 + hy)], vio[2])
    else:
        for ex in (42, 53):
            g.px([(ex + hx, 41 + hy)], hr[0]); g.px([(ex + hx, 42 + hy)], vio[1])
        g.px([(48 + hx, 47 + hy)], sk[0])
    # hat: wide brim, crown bending to the viewer's left with drooping tip, gold bands, flower, ribbon, chain crystal
    bm = P['hat_brim'].shape('ellipse', T([(14, 22), (82, 40)], (hx, hy)))
    P['hat_brim'].fill(bm, pu, base=2)
    under = bm & P['hat_brim'].shape('ellipse', T([(30, 30), (66, 40)], (hx, hy)))
    P['hat_brim'].paint(under, pu[0])                                  # brim underside shadow over the face
    P['hat_brim'].trim(bm, gold[1], 'all'); P['hat_brim'].filigree(bm & ~under, (gold[0], gold[2]), 'all', 3, 5)
    cr = T([(32, 30), (33, 20), (36, 12), (40, 7), (34, 6), (27, 9), (22, 15), (21, 19), (24, 15), (29, 11), (35, 10),
            (44, 5), (52, 4), (58, 8), (62, 16), (64, 30)], (hx, hy))
    m = P['hat_crown'].shape('poly', cr); P['hat_crown'].fill(m, pu, base=2)
    for y in (22, 26):
        band = m & P['hat_crown'].shape('rect', T([(28, y), (68, y + 1)], (hx, hy)))
        P['hat_crown'].paint(band, gold[1])
        if k == 1:
            ys, xs = np.where(band); P['hat_crown'].img[ys[(xs + ys) % 3 == 0], xs[(xs + ys) % 3 == 0], :3] = gold[2]
    tip = (21 + hx, 19 + hy)
    P['hat_ornament'].px([(tip[0], tip[1] + 1), (tip[0], tip[1] + 2), (tip[0] - 1, tip[1] + 3)], gold[0])
    P['hat_ornament'].px([(tip[0] - 1, tip[1] + 4), (tip[0] - 2, tip[1] + 5), (tip[0], tip[1] + 5), (tip[0] - 1, tip[1] + 6),
                          (tip[0] - 1, tip[1] + 5)], vio[2])
    P['hat_ornament'].px([(tip[0] - 1, tip[1] + 7)], vio[0])
    fx, fy = 37 + hx, 25 + hy
    P['hat_ornament'].fill(P['hat_ornament'].shape('ellipse', [(fx - 4, fy - 4), (fx + 4, fy + 4)]), vio, base=2)
    P['hat_ornament'].px([(fx, fy)], gold[2]); P['hat_ornament'].px([(fx - 1, fy), (fx + 1, fy), (fx, fy - 1), (fx, fy + 1)], gold[1])
    rb = pose['ribbon']
    for x0, x1 in ((fx - 4, fx - 6 + rb), (fx - 1, fx - 2 + rb)):
        P['hat_ornament'].fill(P['hat_ornament'].shape('poly', [(x0, fy + 4), (x0 + 2, fy + 4), (x1 + 1, fy + 24), (x1 - 1, fy + 25)]), vio, base=1)
    return P, names


def render(view, k, R, pose=NEUTRAL):
    P, order = (back if view == 'back' else front)(k, R, pose)
    return composite(P, order), P, order
