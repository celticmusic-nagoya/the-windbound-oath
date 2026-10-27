"""Issue #70: altar contract-activation FX -> clean, fully transparent PNG aligned to moss_ancient_altar_idle_v1.png.

Deterministic image processing only (no image generation):
  1. clean   - remove the broad low-alpha haze/flare around the effect while keeping the drawn lines, magic circle,
               light beam, wind ribbons, sparks and a local glow (<= GLOW_R px from the drawn effect, then a short fade);
               nothing touches the canvas edge (the beam that was cut by the top edge fades out instead).
  2. align   - scale the cleaned FX by SCALE and place it on the altar's 1536x1024 canvas so the FX magic circle sits on
               the altar floor rune circle. The output therefore composites on the altar at offset (0, 0), same size.
  3. tidy    - fully transparent pixels carry no colour (no fringes when the engine resamples).

usage: python3 tools/assets/clean_altar_contract_fx.py <fx_base.png> <altar_v1.png> <out.png>
"""
import hashlib, json, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HAZE = 12          # alpha below this is background haze -> 0 (remapped smoothly, no visible step)
CORE = 96          # alpha at/above this is the drawn effect
GLOW_R = 18        # local glow kept within this distance (px, base resolution) of the drawn effect ...
GLOW_FADE = 10     # ... then faded to 0 over this many px
EDGE_FADE = 40     # alpha fades to 0 towards the canvas edge
FX_CENTRE = (783, 703)     # FX magic-circle centre on the 1536x1024 base canvas (measured)
ALTAR_CENTRE = (765, 610)  # altar v1 floor rune-circle centre (measured)
SCALE = 0.45               # FX outer ring (~487 px half-width) -> altar rune circle (~220 px half-width)


def clean(fx):
    im = np.array(fx.convert('RGBA')).astype(np.float64)
    a = im[..., 3]
    a1 = np.clip((a - HAZE) / (255 - HAZE), 0, 1) * 255
    core = ndi.binary_opening(a >= CORE, iterations=1) | (a >= 200)
    dist = ndi.distance_transform_edt(~core)
    a2 = a1 * np.clip(1 - (dist - GLOW_R) / GLOW_FADE, 0, 1)
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum.reduce([yy, xx, h - 1 - yy, w - 1 - xx]).astype(np.float64)
    a3 = np.round(a2 * np.clip(edge / EDGE_FADE, 0, 1) ** 1.5).astype(np.uint8)
    out = im.astype(np.uint8)
    out[..., 3] = a3
    out[a3 == 0, :3] = 0
    return Image.fromarray(out, 'RGBA')


def align(fx, size):
    w, h = fx.size
    f = fx.resize((round(w * SCALE), round(h * SCALE)), Image.LANCZOS)
    ox, oy = round(ALTAR_CENTRE[0] - FX_CENTRE[0] * SCALE), round(ALTAR_CENTRE[1] - FX_CENTRE[1] * SCALE)
    canvas = Image.new('RGBA', size, (0, 0, 0, 0))
    canvas.alpha_composite(f, (max(ox, 0), max(oy, 0)), (max(-ox, 0), max(-oy, 0)))
    g = np.array(canvas)
    g[g[..., 3] == 0, :3] = 0
    return Image.fromarray(g, 'RGBA'), (ox, oy)


def qa(img):
    g = np.array(img); a = g[..., 3]; nz = a > 0
    ys, xs = np.nonzero(nz)
    return {'size': list(img.size), 'nonzero_px': int(nz.sum()),
            'low_alpha_1_15_px': int(((a > 0) & (a < 16)).sum()),
            'border_nonzero_px': int(nz[0].sum() + nz[-1].sum() + nz[:, 0].sum() + nz[:, -1].sum()),
            'alpha0_with_rgb_px': int(((a == 0) & g[..., :3].any(-1)).sum()),
            'bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]}


if __name__ == '__main__':
    src, altar_path, dst = sys.argv[1:4]
    altar = Image.open(altar_path)
    out, offset = align(clean(Image.open(src)), altar.size)
    out.save(dst, optimize=True)
    rep = {'source_sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(),
           'altar_sha256': hashlib.sha256(open(altar_path, 'rb').read()).hexdigest(),
           'params': {'HAZE': HAZE, 'CORE': CORE, 'GLOW_R': GLOW_R, 'GLOW_FADE': GLOW_FADE, 'EDGE_FADE': EDGE_FADE,
                      'SCALE': SCALE, 'offset': offset},
           'output_sha256': hashlib.sha256(open(dst, 'rb').read()).hexdigest(), 'qa': qa(out)}
    print(json.dumps(rep, indent=1))
    ok = rep['qa']['border_nonzero_px'] == 0 and rep['qa']['alpha0_with_rgb_px'] == 0
    sys.exit(0 if ok else 1)
