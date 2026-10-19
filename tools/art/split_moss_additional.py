"""Split the 7 multi-object delivery sheets into 17 independent transparent PNGs. Pixels are copied untouched (no resample/recolor);
every opaque pixel is assigned to exactly one object (connected-component labelling, tiny stray fragments go to the nearest object);
each crop gets a fixed transparent margin. Order = left to right = asset-ID order (verified against the production descriptions)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'docs/art/delivered/moss_additional_20261019/originals'
DST = ROOT / 'img/field/moss/art'
PAD = 16
SHEETS = {'fern_cluster_01-03': 3, 'bush_forest_01-03': 3, 'rock_moss_01-03': 3, 'root_exposed_01-02': 2,
          'stump_rot_01-02': 2, 'mushroom_cluster_01-02': 2, 'ruins_stone_01-02': 2}
rep = []
for sheet, n in SHEETS.items():
    base = sheet.rsplit('_', 1)[0]
    im = Image.open(SRC / (sheet + '.png')).convert('RGBA'); arr = np.array(im); a = arr[..., 3]
    op = a > 0
    lab, k = ndi.label(ndi.binary_dilation(a > 8, iterations=6))
    sizes = ndi.sum(np.ones_like(lab), lab, range(1, k + 1)); big = [i + 1 for i in np.argsort(-sizes)[:n]]
    assert k >= n and all(sizes[i - 1] > 20000 for i in big), (sheet, sizes)
    # distance-to-object assignment for every opaque pixel (small strays + dilation-excluded faint pixels)
    mainmask = np.isin(lab, big)
    idx = ndi.distance_transform_edt(~mainmask, return_distances=False, return_indices=True)
    owner = lab[idx[0], idx[1]]
    owner = np.where(op, owner, 0)
    order = sorted(big, key=lambda i: np.where(lab == i)[1].mean())
    tot = 0
    for j, i in enumerate(order, 1):
        m = (owner == i) & op
        ys, xs = np.where(m); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        h, w = y1 - y0 + 2 * PAD, x1 - x0 + 2 * PAD
        out = np.zeros((h, w, 4), np.uint8)
        sub = arr[y0:y1, x0:x1].copy(); sub[~m[y0:y1, x0:x1]] = 0
        out[PAD:PAD + (y1 - y0), PAD:PAD + (x1 - x0)] = sub
        name = '%s_%02d' % (base, j); Image.fromarray(out, 'RGBA').save(DST / (name + '.png'), optimize=True)
        tot += int(m.sum())
        rep.append({'id': name, 'source': sheet + '.png', 'order': j, 'size': [int(w), int(h)], 'crop_xywh_in_sheet': [int(x0), int(y0), int(x1 - x0), int(y1 - y0)], 'opaque_px': int(m.sum())})
    assert tot == int(op.sum()), (sheet, tot, int(op.sum()))   # every source pixel kept exactly once
json.dump(rep, open(ROOT / 'docs/art/delivered/moss_additional_20261019/split_report.json', 'w'), indent=1, ensure_ascii=False)
print(len(rep), 'objects')
