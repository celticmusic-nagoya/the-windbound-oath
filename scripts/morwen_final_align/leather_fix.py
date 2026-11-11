"""Back view only: the shoulder-bag leather came out mauve (Lab hue ~22 deg in the bag box) against brown in front/right
(~33-40 deg). Rotate the hue of leather-class pixels inside the strap/bag box towards the reference.
Usage: python3 leather_fix.py IN.png OUT.png [x0 y0 x1 y1 shift_deg]"""
import sys, numpy as np
from PIL import Image
from skimage import color
import colormatch as cm
BOX = (380, 280, 760, 800)    # default box (final-align-01 back): x0, y0, x1, y1 in 1024x1536 source coords
SHIFT_DEG = 18.0
if len(sys.argv) > 3:          # optional: x0 y0 x1 y1 shift_deg
    BOX = tuple(map(int, sys.argv[3:7])); SHIFT_DEG = float(sys.argv[7])
a, lab, hsv = cm.prep(sys.argv[1])
# leather membership: Lab hue angle 5..60 deg (reddish-brown to brown), lightness < 75, chroma 6..45.
# (The HSV-based class weights miss low-saturation leather, so the membership is defined in Lab here.)
hdeg = np.degrees(np.arctan2(lab[..., 2], lab[..., 1]))
Cm = np.hypot(lab[..., 1], lab[..., 2])
w = (np.clip((hdeg - 5) / 6, 0, 1) * np.clip((60 - hdeg) / 6, 0, 1) * (lab[..., 0] < 75)
     * np.clip((Cm - 6) / 4, 0, 1) * (Cm < 45)).astype(np.float64)
box = np.zeros(w.shape); x0, y0, x1, y1 = BOX; box[y0:y1, x0:x1] = 1
w = w * box
C = np.hypot(lab[..., 1], lab[..., 2]); H = np.arctan2(lab[..., 2], lab[..., 1]) + np.radians(SHIFT_DEG) * w
lab2 = np.dstack([lab[..., 0], C * np.cos(H), C * np.sin(H)])
o = a.copy(); o[..., :3] = np.round(np.clip(color.lab2rgb(lab2), 0, 1) * 255); o[a[..., 3] == 0, :3] = 0
Image.fromarray(o.astype(np.uint8), "RGBA").save(sys.argv[2])
