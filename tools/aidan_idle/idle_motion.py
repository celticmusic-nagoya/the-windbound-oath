#!/usr/bin/env python3
"""Aidan idle v1 -- secondary-motion model (reference renderer).

One MASTER still is warped by a smooth, periodic displacement field D(x, y, t) (master pixels).  Nothing is repainted, so the design,
sword and palette stay the MASTER's.  Region weights are soft (Gaussian-blurred) masks:
   torso    chest / shoulders / head follow the breath      (zero from the waist down: feet and legs never move)
   arms     gloves + sword + forearms move as ONE rigid group (rotation about the hands' pivot + the torso's rise), faded into the torso
   hair     loose delayed sway, strongest at the strand tips
   cloak    big back cloak + ribbons: delayed wave, amplitude grows with distance from the shoulders
   flaps    white lower drapes: slower, smaller delayed wave (kept away from the boots)
Loop: P = 8 s, every component has an integer number of cycles in P -> the loop is exactly periodic (no seam).
"""
import json, math, numpy as np, cv2
from PIL import Image, ImageDraw

P = 8.0          # loop length (s)
H_, W_ = 1199, 1312

def cap(m, p0, p1, r0, r1):
    """capsule from p0 to p1 with radius r0 -> r1"""
    n = 64
    for i in range(n + 1):
        t = i / n; x = p0[0] + (p1[0] - p0[0]) * t; y = p0[1] + (p1[1] - p0[1]) * t; r = r0 + (r1 - r0) * t
        cv2.circle(m, (int(round(x)), int(round(y))), int(round(r)), 1.0, -1)
def ell(m, cx, cy, rx, ry, ang=0):
    cv2.ellipse(m, (int(cx), int(cy)), (int(rx), int(ry)), ang, 0, 360, 1.0, -1)
def poly(m, pts):
    cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0)
def blur(m, s): return cv2.GaussianBlur(m, (0, 0), s)
def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def regions(alpha):
    Z = lambda: np.zeros((H_, W_), np.float32)
    R = {}
    # ---- sword (blade + guard) and hands / forearms: one rigid group
    sw = Z(); cap(sw, (140, 14), (640, 500), 14, 62); ell(sw, 640, 512, 78, 58, 35); R['sword'] = sw
    hands = Z(); ell(hands, 700, 600, 95, 90); ell(hands, 780, 560, 70, 60); R['hands'] = hands
    arm = Z(); cap(arm, (905, 430), (760, 590), 52, 66); cap(arm, (720, 430), (690, 560), 40, 52); R['forearms'] = arm
    # ---- torso: chest, shoulders, scarf, head
    tor = Z(); poly(tor, [(590, 330), (700, 300), (850, 300), (1010, 330), (1030, 430), (1000, 560), (950, 700), (700, 700), (600, 600), (560, 430)]); R['torso'] = tor
    head = Z(); ell(head, 860, 190, 180, 150); ell(head, 870, 290, 100, 80); R['head'] = head
    # ---- hair: head minus the face
    hair = Z(); ell(hair, 860, 150, 200, 135); ell(hair, 790, 260, 95, 80); ell(hair, 960, 210, 75, 90)
    face = Z(); ell(face, 885, 262, 78, 92); ell(face, 905, 330, 60, 40)
    R['hair'] = np.clip(hair - face, 0, 1)
    # ---- cloak (back, left of the sword), shoulder ribbons (right)
    cl = Z(); poly(cl, [(20, 505), (50, 330), (140, 215), (330, 172), (480, 196), (570, 320), (540, 470), (340, 545), (140, 565), (40, 525)])
    cr = Z(); poly(cr, [(960, 360), (1070, 420), (1210, 520), (1312, 700), (1260, 790), (1110, 725), (1010, 610), (980, 480)])
    R['cloakL'] = np.clip(cl - np.clip(sw * 1.0, 0, 1), 0, 1); R['cloakR'] = cr
    fl = Z(); poly(fl, [(0, 590), (150, 545), (330, 560), (480, 600), (565, 685), (470, 790), (330, 865), (150, 890), (30, 890), (0, 840)])
    fr = Z(); poly(fr, [(930, 770), (1050, 825), (1230, 880), (1312, 965), (1270, 1085), (1190, 1010), (1060, 900), (960, 850)])
    R['flapsL'] = fl; R['flapsR'] = fr
    sk = Z(); poly(sk, [(470, 690), (620, 650), (880, 690), (960, 800), (900, 940), (740, 990), (560, 960), (470, 820)]); R['skirt'] = sk
    return R

def weights(alpha):
    R = regions(alpha); Wt = {}
    for k, m in R.items():
        s = {'sword': 12, 'hands': 22, 'forearms': 28, 'torso': 40, 'head': 30, 'hair': 16, 'cloakL': 34, 'cloakR': 30, 'flapsL': 36, 'flapsR': 36, 'skirt': 40}[k]
        Wt[k] = np.clip(blur(m, s), 0, 1)
    return Wt

YY, XX = np.mgrid[0:H_, 0:W_].astype(np.float32)

class Idle:
    def __init__(self, alpha):
        self.W = weights(alpha)
        W = self.W
        # waist-down fade: nothing below ~y 760 follows the breath; legs / boots are never moved
        self.fade = (1 - smoothstep(690, 800, YY))
        # group weights (arms group overrides the torso weight where it applies)
        self.w_group = np.clip(np.maximum.reduce([W['sword'], W['hands'], W['forearms']]), 0, 1)
        self.w_torso = np.clip(W['torso'] * (1 - self.w_group * 0.9), 0, 1) * self.fade
        self.w_head = np.clip(W['head'] * (1 - W['hair'] * 0), 0, 1)
        self.w_hair = W['hair']
        # distance from the shoulders (cloak attachment) normalised 0..1: later phase, bigger amplitude farther out
        sh = np.array([830.0, 400.0])
        dist = np.hypot(XX - sh[0], YY - sh[1]); self.dist_c = np.clip(dist / 900.0, 0, 1)
        self.dist_f = np.clip(np.hypot(XX - 760, YY - 760) / 900.0, 0, 1)
        self.hair_h = np.clip((230 - YY) / 180.0, 0, 1)                    # strand tips (higher up) swing more
        self.pivot = (800.0, 560.0)

    def field(self, t):
        """displacement (dx, dy) in master px at time t (s).  Output pixel (x,y) shows the master at (x - dx, y - dy)."""
        u = (t % P) / P; tau = 2 * math.pi
        br = 0.5 - 0.5 * math.cos(tau * 2 * u)                           # breath: 4 s cycle (2 per loop), 0..1
        br2 = math.sin(tau * 2 * u)
        W = self.W
        dx = np.zeros((H_, W_), np.float32); dy = np.zeros((H_, W_), np.float32)
        # --- torso / head: chest rises and widens a little
        rise = -3.0 * br
        dy += self.w_torso * rise + self.w_head * (-1.8 * br)
        dx += self.w_torso * ((XX - 800) * 0.0016 * br)
        # --- arms + hands + sword: one rigid group: follows the torso's rise, plus a tiny rotation about the grip (lags the chest by ~0.07 cycle)
        th = math.radians(0.20) * math.sin(tau * (2 * u - 0.07)) - math.radians(0.08) * br
        c, s = math.cos(th), math.sin(th); px, py = self.pivot
        gx = (XX - px) * c - (YY - py) * s + px - XX; gy = (XX - px) * s + (YY - py) * c + py - YY
        dx += self.w_group * (gx); dy += self.w_group * (gy + rise * 0.8)
        # --- hair: delayed horizontal sway (+ a small vertical lift) with a second harmonic so it never looks metronomic
        ph = 2 * u - 0.16
        hs = math.sin(tau * ph) + 0.28 * math.sin(tau * (3 * u - 0.30))
        dx += self.w_hair * (1.0 + 1.4 * self.hair_h) * 2.1 * hs
        dy += self.w_hair * (0.5 + 1.0 * self.hair_h) * (-0.9) * (0.5 - 0.5 * math.cos(tau * (2 * u - 0.22)))
        # --- cloak and ribbons: delayed wave, amplitude grows outwards
        for key, a, lag in (('cloakL', 6.2, 0.34), ('cloakR', 5.3, 0.30)):
            w = W[key]
            wave = np.sin(tau * (2 * u - lag * self.dist_c - 0.12)) + 0.35 * np.sin(tau * (u - 0.5 * lag * self.dist_c))
            dy += w * (a * (0.35 + self.dist_c)) * wave * 0.8
            dx += w * (a * 0.55 * self.dist_c) * np.sin(tau * (2 * u - lag * self.dist_c - 0.30))
        # --- white drapes (slow, small, never near the boots: fade towards the lower edge)
        for key, a, lag in (('flapsL', 4.4, 0.42), ('flapsR', 3.4, 0.40)):
            w = W[key] * (1 - smoothstep(930, 1060, YY))
            wave = np.sin(tau * (2 * u - lag * self.dist_f - 0.20))
            dy += w * (a * (0.3 + self.dist_f)) * wave * 0.8
            dx += w * (a * 0.5 * self.dist_f) * np.sin(tau * (2 * u - lag * self.dist_f - 0.45))
        dy += W['skirt'] * 1.0 * np.sin(tau * (2 * u - 0.30)) * (1 - smoothstep(930, 1020, YY))
        # --- ground contact: the soles never move
        g = 1 - smoothstep(960, 1010, YY)
        return dx * (g if False else 1.0), dy

def warp(rgba, dx, dy):
    """backward warp with premultiplied alpha, bilinear"""
    a = rgba[..., 3:4].astype(np.float32) / 255
    pm = np.concatenate([rgba[..., :3].astype(np.float32) * a, a * 255], -1)
    mx = (XX - dx).astype(np.float32); my = (YY - dy).astype(np.float32)
    out = cv2.remap(pm, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    al = out[..., 3:4] / 255
    rgb = np.where(al > 1e-4, out[..., :3] / np.maximum(al, 1e-4), 0)
    return np.concatenate([np.clip(rgb, 0, 255), np.clip(out[..., 3:4], 0, 255)], -1).astype(np.uint8)

def region_overlay(master, Wt):
    cols = {'sword': (255, 0, 0), 'hands': (255, 120, 0), 'forearms': (255, 200, 0), 'torso': (0, 200, 255), 'head': (0, 120, 255), 'hair': (255, 0, 255),
            'cloakL': (0, 255, 0), 'cloakR': (120, 255, 0), 'flapsL': (255, 255, 255), 'flapsR': (200, 200, 255), 'skirt': (0, 255, 160)}
    base = np.array(Image.alpha_composite(Image.new('RGBA', master.size, (60, 60, 60, 255)), master).convert('RGB')).astype(np.float32)
    out = base.copy()
    for k, w in Wt.items():
        c = np.array(cols[k], np.float32)[None, None, :]
        out = out * (1 - 0.45 * w[..., None]) + c * 0.45 * w[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

if __name__ == '__main__':
    import sys
    master = Image.open(sys.argv[1]).convert('RGBA'); idle = Idle(np.array(master)[..., 3])
    region_overlay(master, idle.W).save(sys.argv[2])
