import sys, json, numpy as np
from PIL import Image
from skimage import color
# material classes: (name, hue range deg, L range)
CLS = [("gold", (30, 75), (55, 101)), ("gold_dark", (30, 75), (0, 55)),
       ("skin", (0, 35), (70, 101)), ("leather", (0, 35), (0, 70)),
       ("purple", (275, 325), (0, 101)), ("magenta", (325, 360), (0, 101)),
       ("green", (75, 170), (0, 101))]
FEATHER_H, FEATHER_L = 8.0, 6.0
import os
KC_MIN = float(os.environ.get("KC_MIN", "0.75"))   # final-align-01 used 0.75; final-04 uses 0.6

def prep(path):
    a = np.asarray(Image.open(path).convert("RGBA")).astype(np.float64)
    rgb = a[..., :3] / 255.0
    lab = color.rgb2lab(rgb)
    hsv = color.rgb2hsv(rgb)
    return a, lab, hsv

def weights(lab, hsv, rng_h, rng_l):
    h = hsv[..., 0] * 360; s = hsv[..., 1]; L = lab[..., 0]
    def tri(x, lo, hi, f):
        return np.clip(np.minimum(x - lo + f, hi - x + f) / (2 * f), 0, 1)
    wh = tri(h, *rng_h, FEATHER_H)
    if rng_h[0] == 0: wh = np.maximum(wh, tri(h, 360 - FEATHER_H, 360 + FEATHER_H, FEATHER_H))
    if rng_h[1] == 360: wh = np.maximum(wh, tri(h, -FEATHER_H, 0 + FEATHER_H, FEATHER_H))
    wl = tri(L, *rng_l, FEATHER_L)
    ws = np.clip((s - 0.10) / 0.12, 0, 1)
    return wh * wl * ws

def stats(lab, w, mask):
    w = w * mask
    t = w.sum()
    if t < 500: return None
    L = lab[..., 0]; A = lab[..., 1]; B = lab[..., 2]
    C = np.hypot(A, B); H = np.arctan2(B, A)
    mL = (w * L).sum() / t; sL = np.sqrt((w * (L - mL) ** 2).sum() / t)
    mC = (w * C).sum() / t
    mH = np.arctan2((w * np.sin(H)).sum(), (w * np.cos(H)).sum())
    return dict(mL=mL, sL=sL, mC=mC, mH=mH, n=float(t))

if __name__ == "__main__":
    refs = sys.argv[1].split(","); target, out = sys.argv[2], sys.argv[3]
    strength = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    R = {}
    for name, rh, rl in CLS:
        acc = []
        for p in refs:
            a, lab, hsv = prep(p); m = a[..., 3] >= 240
            st = stats(lab, weights(lab, hsv, rh, rl), m)
            if st: acc.append(st)
        if acc:
            tot = sum(s["n"] for s in acc)
            R[name] = {k: sum(s[k] * s["n"] for s in acc) / tot for k in ("mL", "sL", "mC")}
            R[name]["mH"] = np.arctan2(sum(np.sin(s["mH"]) * s["n"] for s in acc), sum(np.cos(s["mH"]) * s["n"] for s in acc))
    a, lab, hsv = prep(target); m = a[..., 3] >= 1
    L = lab[..., 0]; A = lab[..., 1]; B = lab[..., 2]; C = np.hypot(A, B); H = np.arctan2(B, A)
    dL = np.zeros_like(L); kC = np.zeros_like(L); dH = np.zeros_like(L); W = np.zeros_like(L)
    log = {}
    for name, rh, rl in CLS:
        if name not in R: continue
        w = weights(lab, hsv, rh, rl); st = stats(lab, w, a[..., 3] >= 240)
        if not st: continue
        r = R[name]
        sratio = np.clip(r["sL"] / max(st["sL"], 1e-3), 0.85, 1.15)
        Lnew = (L - st["mL"]) * sratio + r["mL"]
        dL += w * (np.clip(Lnew - L, -8, 8))
        kC += w * np.clip(r["mC"] / max(st["mC"], 1e-3), KC_MIN, 1.15)
        dh = (r["mH"] - st["mH"] + np.pi) % (2 * np.pi) - np.pi
        dH += w * np.clip(dh, -0.12, 0.12)
        W += w
        log[name] = dict(target=dict(L=round(st["mL"], 1), C=round(st["mC"], 1), H=round(np.degrees(st["mH"]), 1)),
                         ref=dict(L=round(r["mL"], 1), C=round(r["mC"], 1), H=round(np.degrees(r["mH"]), 1)))
    Wc = np.maximum(W, 1)
    act = np.clip(W, 0, 1) * strength
    L2 = L + act * dL / Wc
    C2 = C * (1 + act * (kC / Wc - 1))
    H2 = H + act * dH / Wc
    lab2 = np.dstack([np.clip(L2, 0, 100), C2 * np.cos(H2), C2 * np.sin(H2)])
    rgb2 = np.clip(color.lab2rgb(lab2), 0, 1)
    o = a.copy(); o[..., :3] = np.round(rgb2 * 255)
    o[a[..., 3] == 0, :3] = 0
    Image.fromarray(o.astype(np.uint8), "RGBA").save(out)
    print(json.dumps(log, ensure_ascii=False))
