#!/usr/bin/env python3
"""Forest Bat field frames: img/battle/enemies/forest_bat/idle/*.png (1536x1024, delivered battle art) -> img/field/monsters/forest_bat/forest_bat_idle_NN.png
Cropped to the shared union box so the flap keeps one canvas, then downscaled (field sprite is shown at 0.5x of the stored size). Provisional: the 4 idle frames double as the field flap cycle."""
import glob, os
from PIL import Image
SRC = 'img/battle/enemies/forest_bat/idle/forest_bat_idle_%02d.png'; DST = 'img/field/monsters/forest_bat/forest_bat_idle_%02d.png'
W, H = 320, 214
ims = [Image.open(SRC % i).convert('RGBA') for i in range(4)]
bb = [im.getchannel('A').point(lambda v: 255 if v > 16 else 0).getbbox() for im in ims]   # ignore the faint halo
box = [min(b[k] for b in bb) if k < 2 else max(b[k] for b in bb) for k in range(4)]
os.makedirs(os.path.dirname(DST), exist_ok=True)
for i, im in enumerate(ims):
    out = im.crop(box).resize((W, round(W * (box[3] - box[1]) / (box[2] - box[0]))), Image.LANCZOS)
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0)); canvas.paste(out, (0, (H - out.height) // 2)); canvas.save(DST % (i + 1), optimize=True)
print('ok', box)
