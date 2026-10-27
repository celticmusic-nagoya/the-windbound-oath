#!/usr/bin/env python3
"""Derive the portrait-only title foreground from the adopted meadow PNG (DIRECTIVE-17E, user-approved option 1, 2026-10-27).
The source img/title/foreground-meadow.png is read only and never written. Output: img/title/foreground-meadow-portrait.png.
Steps (deterministic):
  1. take the rock-free grass / small-flower area of the source (its left part, x 20-560, y 330-530: the flowery top layer, no rock, no mound contour on top),
  2. (no mirroring / tiling: one continuous piece of the original grass),
  3. grade it toward the foot of the portrait backdrop (darker, less saturated, olive) - partial match, highlights kept,
  4. depth: a light blur on the upper fringe only (the backdrop there is out of focus); the lower grass stays sharp,
  5. alpha: soft ramps on the left / right ends and the top (no edge or horizon line); the bottom runs off the screen.
usage: make_title_foreground_portrait.py [--check]   (--check: exit 1 if the committed output differs from a fresh build)"""
import sys, hashlib, io
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'img/title/foreground-meadow.png'; SRC_SHA = 'cfcc624adbfa8c29994f9c3fd81f41d606dfa623325bedbcca5b3743e554c9f1'
OUT = ROOT / 'img/title/foreground-meadow-portrait.png'
CROP = (20, 330, 560, 530)
GAIN = np.array([0.62, 0.68, 0.80])      # ~ (backdrop foot mean / meadow mean) ** 0.7 per channel, measured on the 390x844 title
def smooth(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
def build():
    raw = SRC.read_bytes(); assert hashlib.sha256(raw).hexdigest() == SRC_SHA, 'source meadow changed'
    src = np.asarray(Image.open(io.BytesIO(raw)).convert('RGBA')).astype(np.float64) / 255
    band = src[CROP[1]:CROP[3], CROP[0]:CROP[2]].copy(); h, W = band.shape[:2]
    rgb, al = band[..., :3], band[..., 3]
    lum = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2])[..., None]
    graded = rgb * GAIN
    keep = smooth((lum - 0.72) / 0.2) * 0.45          # bright flower petals keep part of their whiteness
    rgb = graded * (1 - keep) + rgb * keep
    img = Image.fromarray((np.dstack([rgb, al]) * 255 + .5).astype(np.uint8), 'RGBA')
    soft = np.asarray(img.filter(ImageFilter.GaussianBlur(2.2))).astype(np.float64) / 255
    sharp = np.asarray(img.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float64) / 255
    y = np.linspace(0, 1, h)[:, None, None]
    mix = smooth((0.4 - y) / 0.3)                        # 1 at the top fringe -> 0 from 40 % down
    out = soft * mix + sharp * (1 - mix)
    x = np.linspace(0, 1, W)[None, :]
    edge = smooth(x / 0.2) * smooth((1 - x) / 0.2)       # left / right ramps
    top = smooth((y[..., 0] - 0.02) / 0.3)               # top ramp
    out[..., 3] = out[..., 3] * edge * top
    out[..., :3] = np.where(out[..., 3:4] > 0, out[..., :3], 0)
    o = Image.fromarray((out * 255 + .5).clip(0, 255).astype(np.uint8), 'RGBA')
    buf = io.BytesIO(); o.save(buf, 'PNG', optimize=True); return buf.getvalue()
if __name__ == '__main__':
    data = build()
    if '--check' in sys.argv:
        ok = OUT.exists() and OUT.read_bytes() == data; print('portrait foreground up to date' if ok else 'STALE: rebuild with tools/assets/make_title_foreground_portrait.py'); sys.exit(0 if ok else 1)
    OUT.write_bytes(data); print(OUT.relative_to(ROOT), hashlib.sha256(data).hexdigest(), Image.open(io.BytesIO(data)).size)
