#!/usr/bin/env python3
"""Compare web image formats for WEBSITE-REBUILD-01 (read-only on originals).

For each sample: resize once (Lanczos) to the target width, then encode as
lossless WebP / lossy WebP / AVIF and measure bytes, PSNR, SSIM and the
maximum per-channel difference against the resized reference.
Writes site/img/FORMAT_COMPARISON.json. Encoded test files go to a temp dir
and are not committed.
"""
import io, json, os, sys, time
import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr, structural_similarity as ssim

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SAMPLES = [
    ('img/title/background-landscape.png', 1672, 'HERO PC'),
    ('img/title/background-portrait.png', 941, 'HERO SP'),
    ('img/battle/backgrounds/bg_BG-01_main.png', 1536, 'STORY bg'),
    ('assets/images/characters/portraits/fiona/fiona_normal.png', 640, 'CHAR (alpha)'),
    ('img/events/cg01_rue_encounter_landscape_16x9.png', 1672, 'GALLERY full'),
]
ENC = [
    ('webp-lossless', 'WEBP', dict(lossless=True, quality=100, method=6, exact=True)),
    ('webp-q95', 'WEBP', dict(quality=95, method=6, exact=True)),
    ('webp-q90', 'WEBP', dict(quality=90, method=6, exact=True)),
    ('avif-q90', 'AVIF', dict(quality=90, speed=4)),
    ('avif-q80', 'AVIF', dict(quality=80, speed=4)),
]


def arr(im):
    return np.asarray(im.convert('RGBA'), dtype=np.uint8)


def main():
    out = []
    for src, w, label in SAMPLES:
        im = Image.open(os.path.join(ROOT, src)); im.load(); im = im.convert('RGBA')
        alpha = im.getchannel('A').getextrema()[0] < 255
        if im.width > w:
            im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        if not alpha:
            im = im.convert('RGB')
        ref = arr(im)
        row = {'label': label, 'source': src, 'size': list(im.size), 'alpha': alpha, 'formats': {}}
        for name, fmt, kw in ENC:
            t = time.time(); buf = io.BytesIO(); im.save(buf, fmt, **kw); dt = time.time() - t
            dec = arr(Image.open(io.BytesIO(buf.getvalue())))
            rgb_r, rgb_d = ref[..., :3], dec[..., :3]
            row['formats'][name] = {
                'bytes': buf.tell(),
                'psnr': None if np.array_equal(ref, dec) else round(float(psnr(rgb_r, rgb_d, data_range=255)), 2),
                'ssim': round(float(ssim(rgb_r, rgb_d, channel_axis=2, data_range=255)), 5),
                'max_diff': int(np.abs(ref.astype(int) - dec.astype(int)).max()),
                'pixel_exact': bool(np.array_equal(ref, dec)),
                'encode_s': round(dt, 1),
            }
            print(label, name, row['formats'][name], flush=True)
        out.append(row)
    json.dump(out, open(os.path.join(ROOT, 'site', 'img', 'FORMAT_COMPARISON.json'), 'w'), indent=1)


if __name__ == '__main__':
    sys.exit(main())
