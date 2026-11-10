"""MORWEN-WALK-UP-76 base: chibi back view (96x128, same scale / ground / palette as the side walks) from the official
back profile (SHA-256 9cf2f274...). Head + hat and body are taken from the official image at two scales (the field
sprites are ~2.8 heads: head/hat 0.124, body 0.064 of the 1024x1536 painting); legs are drawn per frame (walk76).
"""
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
import cv2

H, W = 128, 96
HEAD_SRC = (0, 392)        # official rows for hat + head + hair (hair ends ~380)
BODY_SRC = (372, 1190)     # capelet .. cape hem (centre); legs below are drawn
HEAD_S, BODY_S = 0.124, 0.0625
HEAD_TOP, NECK = 2, 50     # sprite rows
CX = 48


def oklab(rgb):
    from oklab import rgb2oklab
    return rgb2oklab(rgb.astype(float))


def area_down(img, s):
    a = img[:, :, 3:4].astype(float) / 255
    pm = np.concatenate([img[:, :, :3] * a, a * 255], 2).astype(np.float32)
    h, w = img.shape[:2]
    small = cv2.resize(pm, (max(1, round(w * s)), max(1, round(h * s))), interpolation=cv2.INTER_AREA)
    al = small[:, :, 3] / 255
    rgb = np.where(al[..., None] > 1e-3, small[:, :, :3] / np.maximum(al[..., None], 1e-3), 0)
    out = np.zeros(small.shape[:2] + (4,), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255); out[..., 3] = np.where(al >= 0.5, 255, 0)
    return out


def palette(paths, k=64, seed=0):
    px = []
    for p in paths:
        a = np.array(Image.open(p).convert('RGBA')); px.append(a[a[:, :, 3] > 0][:, :3])
    px = np.concatenate(px).astype(float)
    km = KMeans(k, n_init=4, random_state=seed).fit(oklab(px))
    from oklab import oklab2rgb
    return np.clip(np.round(oklab2rgb(km.cluster_centers_)), 0, 255).astype(np.uint8)


def quantize(img, pal):
    op = img[:, :, 3] > 0
    lab = oklab(img[op][:, :3]); pl = oklab(pal)
    d = ((lab[:, None, :] - pl[None]) ** 2).sum(-1)
    out = img.copy(); out[op, :3] = pal[d.argmin(1)]
    return out


def place(canvas, layer, x0, y0):
    h, w = layer.shape[:2]
    for y in range(h):
        yy = y0 + y
        if not 0 <= yy < canvas.shape[0]: continue
        for x in range(w):
            xx = x0 + x
            if 0 <= xx < canvas.shape[1] and layer[y, x, 3]:
                canvas[yy, xx] = layer[y, x]


def sharpen(img, amount=0.9):
    op = img[:, :, 3] > 0
    rgb = img[:, :, :3].astype(np.float32)
    bl = cv2.GaussianBlur(rgb, (0, 0), 0.8)
    out = img.copy(); out[..., :3] = np.clip(rgb + amount * (rgb - bl), 0, 255).astype(np.uint8)
    out[~op] = 0
    return out


def base_layers(official_back, pal, k=1.0):
    """returns dict of 96x128 RGBA layers: head (hat+hair), body (capelet, cape, bag, hands)."""
    o = np.array(Image.open(official_back).convert('RGBA'))
    o[o[:, :, 3] < 200, 3] = 0
    ox = 512                                     # official centre column (figure centre)
    head_src = o[HEAD_SRC[0]:HEAD_SRC[1]].copy()
    # below the hair line keep only the hanging ribbon (violet, right of centre); capelet belongs to the body
    from oklab import lch
    L, C, h = lch(oklab(head_src[:, :, :3].reshape(-1, 3)))
    L, C, h = (v.reshape(head_src.shape[:2]) for v in (L, C, h))
    yy, xx = np.mgrid[0:head_src.shape[0], 0:head_src.shape[1]]
    ribbon = (C > 0.14) & (h > 290) & (h < 335) & (xx > 540)
    cut = (yy >= 372 - HEAD_SRC[0]) & ~ribbon
    head_src[cut, 3] = 0
    body_src = o[BODY_SRC[0]:BODY_SRC[1]].copy()
    hd = sharpen(area_down(head_src, HEAD_S * k)); bd = sharpen(area_down(body_src, BODY_S * k))
    hh, ww = int(H * k), int(W * k)
    head = np.zeros((hh, ww, 4), np.uint8); body = np.zeros((hh, ww, 4), np.uint8)
    place(head, hd, int(CX * k) - round(ox * HEAD_S * k), int(round(HEAD_TOP * k)))
    place(body, bd, int(CX * k) - round(ox * BODY_S * k), int(round((NECK - 2) * k)))
    head = quantize(head, pal); body = quantize(body, pal)
    return {'head': head, 'body': body}
