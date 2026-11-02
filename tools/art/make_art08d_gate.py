#!/usr/bin/env python3
"""DIRECTIVE-ART-08D gate 1: Aidan right-walk 01 / 04 (alternating contact) - CANDIDATES ONLY.

Facing right, the character's RIGHT side faces the camera, so the right leg is the NEAR leg and the left leg the FAR leg.
  01 = right foot forward & planted  -> the adopted walk_right_01 whose FRONT leg is near (bright), rear leg far (shaded)
  04 = left foot forward & planted   -> the adopted walk_right_04 whose FRONT leg is far (shaded), rear leg near (bright)
The adopted frames already paint opposite contacts, but both legs carry identical colours, so 01 and 04 read as the same pose.
The far leg is put in shade (x0.66, slight desaturation) on leg-coloured pixels inside measured regions; no pixel is moved or
redrawn (regions/method shared with tools/art/make_art08c_aidan_side.py). Outputs + verification sheets: docs/art/candidates/art-08d/."""
import hashlib, json, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import make_art08c_aidan_side as C

R = pathlib.Path(__file__).resolve().parents[2]; OUT = R / 'docs/art/candidates/art-08d'
F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 18); FS = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 14)
GATE = {'01': ('01_rear', '右足（手前）が前・接地／左足（奥）は後ろ'), '04': ('04_front', '左足（奥）が前・接地／右足（手前）は後ろ')}
NEAR = {'01': [(1130, 880), (1250, 880), (1262, 1000), (1275, 1110), (1380, 1125), (1380, 1228), (1185, 1228), (1180, 1110), (1140, 1000)],   # front leg in 01
        '04': [(822, 1088), (895, 1060), (960, 990), (1010, 945), (1082, 945), (1078, 1012), (1005, 1060), (972, 1150), (972, 1235), (825, 1235)]}  # rear leg in 04


def build():
    OUT.mkdir(parents=True, exist_ok=True); info = {}; out = {}
    for k, (far, note) in GATE.items():
        a = np.array(Image.open(C.SRC / f'aidan_walk_right_{k}.png').convert('RGBA'))
        m = C.mask(far) & C.legcolour(a); o = C.shade(a, m); out[k] = (a, o, m)
        name = f'aidan_walk_right_{k}_candidate.png'; Image.fromarray(o, 'RGBA').save(OUT / name, optimize=True)
        diff = (o != a).any(2)
        info[name] = dict(pose=note, source=f'aidan_walk_right_{k}.png (adopted, unchanged)', far_leg_region=far, shaded_pixels=int(m.sum()),
                          changed_pixels=int(diff.sum()), changed_outside_far_leg=int((diff & ~m).sum()), alpha_identical=bool((o[..., 3] == a[..., 3]).all()),
                          sha256=hashlib.sha256((OUT / name).read_bytes()).hexdigest())
    return info, out


def outline(img, poly, col, w=4):
    ImageDraw.Draw(img).line(poly + [poly[0]], fill=col, width=w)


def sheets(out):
    # 1) legs side by side x1 (full-res crop) with near/far contours: cyan = near (right) leg, magenta = far (left) leg
    cells = []
    for k in ('01', '04'):
        a, o, m = out[k]
        for tag, arr, lines in (('現行（採用）', a, False), ('候補', o, True)):
            im = Image.fromarray(arr, 'RGBA'); B = Image.new('RGBA', im.size, (72, 84, 66, 255)); B.alpha_composite(im)
            if lines:
                outline(B, [tuple(p) for p in NEAR[k]], (0, 230, 255)); outline(B, [tuple(p) for p in C.POLY[GATE[k][0]]], (255, 60, 220))
            c = B.crop((780, 840, 1420, 1240)).resize((480, 300), Image.LANCZOS)
            cell = Image.new('RGB', (480, 340), (20, 24, 22)); cell.paste(c.convert('RGB'), (0, 40)); d = ImageDraw.Draw(cell)
            d.text((6, 2), f'walk_{k}｜{tag}', fill=(240, 228, 190), font=F); d.text((6, 22), GATE[k][1], fill=(200, 210, 200), font=FS); cells.append(cell)
    S = Image.new('RGB', (2 * 492 + 12, 2 * 352 + 52), (10, 14, 12)); d = ImageDraw.Draw(S)
    d.text((12, 10), 'ART-08D ゲート1｜01と04の脚の入れ替わり（水色＝手前の右脚、桃色＝奥の左脚。線は確認用で画像には含まない）', fill=(240, 228, 190), font=FS)
    for i, c in enumerate(cells): S.paste(c, (12 + (i % 2) * 492, 40 + (i // 2) * 352))
    S.save(OUT / 'gate_01_04_legs.png')
    # 2) whole figure, game scale x1 and x3 (runtime scale 0.0625), current vs candidate
    rows = []
    for k in ('01', '04'):
        a, o, m = out[k]
        for z in (1, 3):
            row = Image.new('RGB', (2 * (128 * z + 20) + 20, 80 * z + 40), (52, 62, 48)); dd = ImageDraw.Draw(row)
            for j, arr in enumerate((a, o)):
                im = Image.fromarray(arr, 'RGBA').resize((128 * z, 80 * z), Image.LANCZOS); x = 10 + j * (128 * z + 20); row.paste(im, (x, 30), im)
                dd.text((x, 4), f'walk_{k} {"現行" if j == 0 else "候補"} ×{z}', fill=(240, 228, 190), font=FS)
            rows.append(row)
    Wd = max(r.width for r in rows); S2 = Image.new('RGB', (Wd, sum(r.height for r in rows)), (20, 24, 22)); y = 0
    for r in rows: S2.paste(r, (0, y)); y += r.height
    S2.save(OUT / 'gate_01_04_gamescale.png')
    # 3) alternation GIF: 01 <-> 04 at a slow rate so the swap is easy to judge (x3 game scale), current vs candidate
    frames = []
    for k in ('01', '04', '01', '04'):
        a, o, m = out[k]; S3 = Image.new('RGB', (2 * 404 + 30, 270), (52, 62, 48)); dd = ImageDraw.Draw(S3)
        for j, (arr, t) in enumerate(((a, '現行（採用）'), (o, '候補'))):
            im = Image.fromarray(arr, 'RGBA').resize((384, 240), Image.LANCZOS); x = 10 + j * 414; S3.paste(im, (x, 26), im); dd.text((x, 4), f'{t} walk_{k}', fill=(240, 228, 190), font=FS)
        frames.append(S3)
    frames[0].save(OUT / 'gate_01_04_alternate.gif', save_all=True, append_images=frames[1:], duration=600, loop=0)


def main():
    info, out = build(); sheets(out)
    (OUT / 'qa.json').write_text(json.dumps(dict(gate='01/04', near_leg='right (camera side when facing right)', shade=C.SHADE, **info), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(info, ensure_ascii=False, indent=0))


if __name__ == '__main__':
    main()
