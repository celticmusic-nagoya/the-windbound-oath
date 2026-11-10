"""MORWEN-MODULAR-SPRITE-01: part-based HD pixel drawing primitives.

Every part is drawn as its own RGBA layer from explicit shapes (polygons / ellipses / lines / dots in 96x128 sprite
coordinates; k=2 draws the same part on the 48x64 grid with coordinates halved and fine patterns dropped), painted
only with the side walks' colour ramps (74G / 75), cel-shaded with light from the upper left, with a selective inner
contour per part. Layers are composited in a per-facing order and the silhouette gets the shared 1-px outline.
No painting pixels are copied: the official illustrations are only the design reference."""
import numpy as np
from PIL import Image, ImageDraw

OUTLINE = (12, 2, 12)


class Part:
    def __init__(self, name, k, slot=None):
        self.name, self.k, self.slot = name, k, slot
        self.W, self.H = 96 // k, 128 // k
        self.img = np.zeros((self.H, self.W, 4), np.uint8)
        self.mask = np.zeros((self.H, self.W), bool)

    # ---- geometry (coordinates in 96x128 units) ----
    def _c(self, pts):
        k = self.k
        return [(round(x / k), round(y / k)) for x, y in pts]

    def shape(self, kind, pts, **kw):
        m = Image.new('L', (self.W, self.H), 0); d = ImageDraw.Draw(m)
        p = self._c(pts)
        if kind == 'poly': d.polygon(p, fill=1)
        elif kind == 'ellipse': d.ellipse([p[0], p[1]], fill=1)
        elif kind == 'line': d.line(p, fill=1, width=max(1, kw.get('w', 1) // self.k))
        elif kind == 'rect': d.rectangle([p[0], p[1]], fill=1)
        return np.array(m) > 0

    def fill(self, mask, ramp, base=1, light=True, rim=True):
        """cel shade: 1 tone lighter on the upper-left quarter of each row span, 1 darker on the right quarter and
        the bottom rows; part contour (inside) takes the darkest tone."""
        r = np.array(ramp); n = len(r)
        ys, xs = np.where(mask)
        if not len(ys): return
        y0, y1 = ys.min(), ys.max()
        tone = np.full(mask.shape, base)
        if light:
            for y in range(y0, y1 + 1):
                row = np.where(mask[y])[0]
                if not len(row): continue
                a, b = row.min(), row.max(); w = max(1, b - a + 1)
                for x in row:
                    t = (x - a) / w
                    tone[y, x] = base + (1 if t < 0.28 else 0) - (1 if t > 0.74 else 0)
            bottom = y0 + (y1 - y0) * 0.85
            tone[(np.mgrid[0:mask.shape[0], 0:mask.shape[1]][0] > bottom) & mask] -= 1
        tone = np.clip(tone, 0, n - 1)
        self.img[mask, :3] = r[tone[mask]]; self.img[mask, 3] = 255
        if rim:
            pad = np.pad(mask, 1)
            edge = mask & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
            self.img[edge, :3] = r[0]
            if light and self.k == 1:                 # glossy rim: second pixel in from the upper-left contour
                inner = mask & ~edge
                p2 = np.pad(inner, 1)
                ul = inner & (~p2[:-2, 1:-1] | ~p2[1:-1, :-2])
                tt = np.clip(tone + 2, 0, n - 1)
                self.img[ul, :3] = r[tt[ul]]
        self.mask |= mask

    def paint(self, mask, color):
        m = mask
        self.img[m, :3] = color; self.img[m, 3] = 255; self.mask |= m

    def px(self, pts, color, only_on_part=False):
        """single pixels (96 coords). At 48 several 96 pixels may fall on one 48 pixel - that is intended."""
        for x, y in pts:
            xx, yy = round(x / self.k), round(y / self.k)
            if 0 <= xx < self.W and 0 <= yy < self.H and (not only_on_part or self.mask[yy, xx]):
                self.img[yy, xx, :3] = color; self.img[yy, xx, 3] = 255; self.mask[yy, xx] = True

    def line(self, pts, color, w=1):
        m = self.shape('line', pts, w=w); self.paint(m, color)

    def filigree(self, mask, colors, side='bottom', depth=3, step=4):
        """gold thorn filigree band just inside a trim: a dotted inner line plus a small 3-px thorn every `step` px."""
        if self.k != 1: return
        H, W = mask.shape
        ys, xs = np.where(mask)
        if not len(ys): return
        if side == 'bottom':
            for x in range(xs.min(), xs.max() + 1):
                col = np.where(mask[:, x])[0]
                if len(col) < depth + 2: continue
                yb = col.max() - depth
                if x % 2 == 0: self.img[yb, x, :3] = colors[0]
                if x % step == 0:
                    for dy, c in ((-1, colors[1]), (-2, colors[0])):
                        if mask[yb + dy, x]: self.img[yb + dy, x, :3] = c
        else:
            pad = np.pad(mask, 1)
            e = mask & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
            inner = mask & ~e
            for _ in range(depth - 1):
                p2 = np.pad(inner, 1); inner = inner & p2[:-2, 1:-1] & p2[2:, 1:-1] & p2[1:-1, :-2] & p2[1:-1, 2:]
            p2 = np.pad(inner, 1); ring = inner & ~(p2[:-2, 1:-1] & p2[2:, 1:-1] & p2[1:-1, :-2] & p2[1:-1, 2:])
            ry, rx = np.where(ring); sel = (rx + ry) % 2 == 0
            self.img[ry[sel], rx[sel], :3] = colors[0]
            sel2 = (rx + 2 * ry) % step == 0
            self.img[ry[sel2], rx[sel2], :3] = colors[1]

    def trim(self, mask, color, side='bottom'):
        """1-px gold trim along one side of a mask (bottom / top / left / right / all)."""
        H, W = mask.shape; pad = np.pad(mask, 1)
        if side == 'bottom': e = mask & ~pad[2:, 1:-1]
        elif side == 'top': e = mask & ~pad[:-2, 1:-1]
        elif side == 'left': e = mask & ~pad[1:-1, :-2]
        elif side == 'right': e = mask & ~pad[1:-1, 2:]
        else: e = mask & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
        self.paint(e, color)
        return e


def composite(parts, order):
    H, W = parts[order[0]].H, parts[order[0]].W
    out = np.zeros((H, W, 4), np.uint8)
    for n in order:
        p = parts[n]; m = p.img[:, :, 3] > 0; out[m] = p.img[m]
    a = out[:, :, 3] > 0; pad = np.pad(a, 1)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    out[edge, :3] = OUTLINE
    return out


def save_parts(parts, order, outdir, prefix, k):
    """per-part transparent PNG + manifest (z order, bbox, anchor = part bbox bottom-centre in sprite coords)."""
    outdir.mkdir(parents=True, exist_ok=True); man = []
    for z, n in enumerate(order):
        p = parts[n]; a = p.img[:, :, 3] > 0
        if not a.any(): continue
        ys, xs = np.where(a)
        fn = f'{prefix}_{n}_{96 // k}x{128 // k}.png'
        Image.fromarray(p.img, 'RGBA').save(outdir / fn)
        man.append(dict(part=n, slot=p.slot, z=z, file=fn, bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]))
    return man
