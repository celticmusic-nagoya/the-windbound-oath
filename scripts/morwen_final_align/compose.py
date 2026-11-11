import json, sys, numpy as np
from PIL import Image
W, H, AX, AY = 1200, 1600, 600, 1540
# source file, scale, contact anchor in source px (x = centre of support, y = ground row)
SPEC = {
 "front": ("front_src.png", 1.00, (512.5, 1510)),
 "right": ("right_fix.png", 1.00, (605.5, 1524)),
 "back":  ("back_cm2l.png", 1.00, (500.0, 1519)),
 "left":  ("left_cm2c.png",1.07, (426.5, 1435.5)),
}
def premul(a):
    a = a.astype(np.float64); a[..., :3] *= a[..., 3:4] / 255.0; return a
def unpremul(a):
    out = a.copy(); al = a[..., 3:4]
    out[..., :3] = np.where(al > 0, a[..., :3] * 255.0 / np.maximum(al, 1e-6), 0)
    return out
meta = {}
for d, (src, s, (ax, ay)) in SPEC.items():
    im = Image.open(src).convert("RGBA")
    if s != 1.0:
        pm = premul(np.asarray(im))
        ch = [Image.fromarray(pm[..., c].astype(np.float32), "F").resize((round(im.width * s), round(im.height * s)), Image.LANCZOS) for c in range(4)]
        a = np.clip(unpremul(np.dstack([np.asarray(c) for c in ch])), 0, 255)
        im = Image.fromarray(np.round(a).astype(np.uint8), "RGBA")
    ox, oy = round(AX - ax * s), round(AY - ay * s)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sx, sy = max(0, -ox), max(0, -oy)
    assert not np.asarray(im)[:sy, :, 3].any() and not np.asarray(im)[:, :sx, 3].any(), "content would be cut"
    canvas.alpha_composite(im.crop((sx, sy, im.width, im.height)), (ox + sx, oy + sy))
    a = np.asarray(canvas).copy()
    al = a[..., 3]
    al[al >= 250] = 255; al[al <= 12] = 0
    a[al == 0, :3] = 0
    Image.fromarray(a, "RGBA").save(f"final/morwen_{d}_final.png", optimize=True)
    meta[d] = dict(source=src, scale=s, source_anchor=[ax, ay], offset=[ox, oy], anchor_error_px=[round(ox + ax * s - AX, 2), round(oy + ay * s - AY, 2)])
json.dump(meta, open("final/compose_meta.json", "w"), indent=1)
print(json.dumps(meta))
