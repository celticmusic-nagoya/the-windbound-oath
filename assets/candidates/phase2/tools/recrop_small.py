"""Claude repair of Delivery 1 small items: re-crop from the Delivery 1 reference_sheet.png with wider boxes and remove the
neutral (white/grey, low-saturation) panel + drop shadow, including enclosed gaps between legs. Output raw RGBA for normalize fit."""
import sys, json, pathlib
import numpy as np
from PIL import Image
from scipy import ndimage

BOX = {  # x0,y0,x1,y1 on reference_sheet.png (Delivery 1), widened vs crops.json
    'table_small': [1150, 380, 1362, 515], 'stool': [430, 660, 530, 758],
    'jar': [15, 870, 142, 1006], 'chair_back': [10, 595, 140, 763]}

def cut(sheet, key, out, tol_chroma=16, min_val=150, enclosed_min=25):
    a = np.array(Image.open(sheet).convert('RGBA').crop(BOX[key])).astype(int)
    rgb = a[..., :3]; mx = rgb.max(2); mn = rgb.min(2)
    neutral = ((mx - mn) <= tol_chroma) & (mx >= min_val)
    lab, n = ndimage.label(neutral)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sizes = ndimage.sum(neutral, lab, range(1, n + 1))
    bg = np.zeros_like(neutral)
    for i in range(1, n + 1):
        if i in border or sizes[i - 1] >= enclosed_min: bg |= lab == i
    fg = ~bg; fl, fn = ndimage.label(fg, np.ones((3, 3)))
    keep = fl == (1 + int(np.argmax(ndimage.sum(fg, fl, range(1, fn + 1)))))   # the object only (drops captions / neighbours)
    keep = ndimage.binary_fill_holes(keep) & ~bg
    a[..., 3] = np.where(keep, 255, 0); a[~keep, :3] = 0
    p = pathlib.Path(out) / f'{key}.png'; Image.fromarray(a.astype(np.uint8), 'RGBA').save(p)
    return dict(key=key, removed_bg=int(bg.sum()), kept=int(keep.sum()))

if __name__ == '__main__':
    for k in BOX: print(json.dumps(cut(sys.argv[1], k, sys.argv[2])))
