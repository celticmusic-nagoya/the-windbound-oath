#!/usr/bin/env python3
"""Arm-motion analysis for the 4-frame down cycle (01->05->02->06->01).
For each arm (screen-left = anatomical right, screen-right = anatomical left) and each frame transition:
dense optical flow (Farneback) on glove/gauntlet pixels, minus the chest/shoulder shift, so only the arm's own motion
remains. Reports median (dx, dy) and the 75th-percentile speed. usage: arm_motion.py F01 F05 F02 F06"""
import json, sys
import numpy as np, cv2
from PIL import Image

def load(p):
    a = np.array(Image.open(p).convert('RGBA')).astype(np.float32); bg = np.array([70, 100, 70], np.float32)
    return (a[..., :3] * a[..., 3:] / 255 + bg * (1 - a[..., 3:] / 255)).astype(np.uint8)

def arm_px(rgb):
    h = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(int); H, S, V = h[..., 0] * 2, h[..., 1] / 255, h[..., 2] / 255
    return (H < 35) & (S > 0.45) & (V > 0.12)

ROIS = {'screen_left_anat_right': (840, 560, 1000, 800), 'screen_right_anat_left': (1210, 580, 1370, 840)}
names = ['01', '05', '02', '06']; I = dict(zip(names, map(load, sys.argv[1:5])))
seq = names + ['01']; out = {}
for arm, (x0, y0, x1, y1) in ROIS.items():
    rows = []; total = 0.0
    for a, b in zip(seq, seq[1:]):
        ga, gb = cv2.cvtColor(I[a], cv2.COLOR_RGB2GRAY), cv2.cvtColor(I[b], cv2.COLOR_RGB2GRAY)
        (sx, sy), _ = cv2.phaseCorrelate(ga[300:500, 760:1340].astype(np.float32), gb[300:500, 760:1340].astype(np.float32))
        flow = cv2.calcOpticalFlowFarneback(ga, gb, None, 0.5, 4, 31, 5, 7, 1.5, 0)
        m = np.zeros(ga.shape, bool); m[y0:y1, x0:x1] = arm_px(I[a])[y0:y1, x0:x1]
        f = flow[m] - np.array([sx, sy]); mag = np.hypot(f[:, 0], f[:, 1]); p75 = float(np.percentile(mag, 75)); total += p75
        rows.append({'transition': a + '->' + b, 'median_dx': round(float(np.median(f[:, 0])), 1), 'median_dy': round(float(np.median(f[:, 1])), 1), 'speed_p75': round(p75, 1)})
    out[arm] = {'transitions': rows, 'cycle_total_speed_p75': round(total, 1)}
print(json.dumps(out, indent=1))
