"""part masks of the 74C left-side reference (right-view coords), built from the pipeline's own region masks."""
import numpy as np
from PIL import Image, ImageDraw
HAIR_POLY = [(36, 31), (46, 27), (56, 23), (62, 24), (64, 30), (68, 34), (68, 49), (56, 51), (38, 52), (34, 46), (35, 38)]
EYE_BOX = (59, 32, 68, 43)      # eye + glasses (x0, y0, x1, y1 inclusive)
EAR_BOX = (45, 43, 50, 50)      # earring


def poly_mask(poly, h=128, w=96):
    im = Image.new('L', (w, h), 0); ImageDraw.Draw(im).polygon(poly, fill=1); return np.array(im) > 0


def box(b, h=128, w=96):
    yy, xx = np.mgrid[0:h, 0:w]; return (xx >= b[0]) & (xx <= b[2]) & (yy >= b[1]) & (yy <= b[3])


def part_masks(m, op, ub_op):
    """m: region masks (build_morwen74c.region_masks8 on the 74C reference). op: opaque front, ub_op: opaque back layer."""
    head = m['immutable_details'] | m['hair_tips']
    keep = (box(EYE_BOX) | box(EAR_BOX)) & head
    hair = head & poly_mask(HAIR_POLY) | m['hair_tips']
    parts = {
        'hair': hair & ~keep,
        'hat': head & ~hair & ~keep,
        'bow': m['collar_ribbon'],
        'jacket': m['torso'] | m['cape_front'] | m['arm'] | m['accessories_fixed'],
        'skirt': m['skirt'] | m['redraw'],
        'mantle': m['mantle'],
        'potion': m['potions'],
    }
    # back layer / anything unassigned: nearest assigned part
    lab = np.full(op.shape, -1); names = list(parts)
    for i, n in enumerate(names): lab[parts[n]] = i
    todo = (op | ub_op) & (lab < 0) & ~keep
    ys, xs = np.where(lab >= 0)
    for y, x in zip(*np.where(todo)):
        j = int(np.argmin((ys - y) ** 2 + (xs - x) ** 2)); lab[y, x] = lab[ys[j], xs[j]]
    return {n: lab == i for i, n in enumerate(names)}, keep
