#!/usr/bin/env python3
"""Build web derivatives for the official site (site/img/).

Originals under img/ and assets/ are only read, never modified.
Derivatives: Lanczos downscale (never upscale), aspect ratio kept,
alpha kept, encoded as lossless WebP. A JSON report with before/after
bytes is written to site/img/IMAGE_REPORT.json.

Run from repo root:  python3 site/tools/build_images.py
"""
import hashlib, json, os, sys
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'site', 'img')

# (source, output name, max width)
JOBS = [
    ('img/title/background-landscape.png', 'hero/bg-landscape.webp', 1672),
    ('img/title/background-portrait.png', 'hero/bg-portrait.webp', 941),
    ('img/title/logo.png', 'hero/logo.webp', 1200),
    ('img/title/aidan-portrait.png', 'hero/aidan-back.webp', 760),
    ('assets/images/characters/portraits/aidan/aidan_normal.png', 'chars/aidan.webp', 640),
    ('assets/images/characters/portraits/fiona/fiona_normal.png', 'chars/fiona.webp', 640),
    ('assets/images/characters/portraits/lou/lou_normal.png', 'chars/lou.webp', 720),
    ('assets/images/characters/portraits/emma/emma_normal.png', 'chars/emma.webp', 640),
    ('img/battle/backgrounds/bg_BG-01_main.png', 'story/bg-01.webp', 1536),
    ('img/title/background-landscape.png', 'gallery/key-visual-thumb.webp', 640),
    ('img/events/cg01_rue_encounter_landscape_16x9.png', 'gallery/cg01-full.webp', 1672),
    ('img/events/cg01_rue_encounter_landscape_16x9.png', 'gallery/cg01-thumb.webp', 640),
    ('img/events/cg03_fiona_wind_dance_landscape_16x9.png', 'gallery/cg03-full.webp', 1672),
    ('img/events/cg03_fiona_wind_dance_landscape_16x9.png', 'gallery/cg03-thumb.webp', 640),
    ('img/battle/backgrounds/bg_BG-01_main.png', 'gallery/bg-01-thumb.webp', 640),
    ('img/battle/characters/aidan/aidan_battle_idle.png', 'gallery/aidan-battle-full.webp', 1536),
    ('img/battle/characters/aidan/aidan_battle_idle.png', 'gallery/aidan-battle-thumb.webp', 640),
    ('img/battle/characters/fiona/fiona_battle_idle.png', 'gallery/fiona-battle-full.webp', 1536),
    ('img/battle/characters/fiona/fiona_battle_idle.png', 'gallery/fiona-battle-thumb.webp', 640),
    ('img/battle/characters/lou/lou_battle_idle.png', 'gallery/lou-battle-full.webp', 1312),
    ('img/battle/characters/lou/lou_battle_idle.png', 'gallery/lou-battle-thumb.webp', 640),
    # favicon (the game's sign prop is 1MB; the site only needs a small icon)
    ('img/field/lind/props/lind_sign.png', 'favicon-64.png', 64),
    # srcset variants (same lossless encoding, smaller widths for smaller slots)
    ('assets/images/characters/portraits/aidan/aidan_normal.png', 'chars/aidan-360.webp', 360),
    ('assets/images/characters/portraits/aidan/aidan_normal.png', 'chars/aidan-480.webp', 480),
    ('assets/images/characters/portraits/fiona/fiona_normal.png', 'chars/fiona-360.webp', 360),
    ('assets/images/characters/portraits/fiona/fiona_normal.png', 'chars/fiona-480.webp', 480),
    ('assets/images/characters/portraits/lou/lou_normal.png', 'chars/lou-360.webp', 360),
    ('assets/images/characters/portraits/lou/lou_normal.png', 'chars/lou-480.webp', 480),
    ('assets/images/characters/portraits/emma/emma_normal.png', 'chars/emma-360.webp', 360),
    ('assets/images/characters/portraits/emma/emma_normal.png', 'chars/emma-480.webp', 480),
    ('img/title/background-landscape.png', 'gallery/key-visual-thumb-360.webp', 360),
    ('img/events/cg01_rue_encounter_landscape_16x9.png', 'gallery/cg01-thumb-360.webp', 360),
    ('img/events/cg03_fiona_wind_dance_landscape_16x9.png', 'gallery/cg03-thumb-360.webp', 360),
    ('img/battle/backgrounds/bg_BG-01_main.png', 'gallery/bg-01-thumb-360.webp', 360),
    ('img/battle/characters/aidan/aidan_battle_idle.png', 'gallery/aidan-battle-thumb-360.webp', 360),
    ('img/battle/characters/fiona/fiona_battle_idle.png', 'gallery/fiona-battle-thumb-360.webp', 360),
    ('img/battle/characters/lou/lou_battle_idle.png', 'gallery/lou-battle-thumb-360.webp', 360),
]
# Gameplay captures (real game, DEV overlays hidden only) are added after director approval.
EXTRA = [l.split('|') for l in os.environ.get('SITE_EXTRA_JOBS', '').split(';') if l]


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main():
    report, cache = [], {}
    for src, name, maxw in JOBS + [(a, b, int(c)) for a, b, c in EXTRA]:
        sp = os.path.join(ROOT, src)
        before = sha(sp)
        im = Image.open(sp)
        im.load()
        im = im.convert('RGBA')
        # Treat as transparent only when some pixel is actually not opaque.
        has_alpha = im.getchannel('A').getextrema()[0] < 255
        if not has_alpha:
            im = im.convert('RGB')
        w, h = im.size
        if w > maxw:
            nh = round(h * maxw / w)
            im = im.resize((maxw, nh), Image.LANCZOS)
        op = os.path.join(OUT, name)
        os.makedirs(os.path.dirname(op), exist_ok=True)
        # Set REBUILD=1 to re-encode outputs that already exist.
        if os.environ.get('REBUILD') == '1' or not os.path.exists(op):
            if op.endswith('.png'):
                im.save(op, 'PNG', optimize=True)
            else:
                im.save(op, 'WEBP', lossless=True, quality=100, method=6, exact=True)
        assert sha(sp) == before, 'source changed: ' + src
        chk = Image.open(op)
        assert chk.size == im.size
        if has_alpha:
            assert chk.mode == 'RGBA', 'alpha lost: ' + name
        report.append({
            'source': src, 'output': 'site/img/' + name,
            'source_size': [w, h], 'output_size': list(im.size),
            'aspect_delta': abs(w / h - im.size[0] / im.size[1]),
            'alpha': has_alpha,
            'source_bytes': os.path.getsize(sp), 'output_bytes': os.path.getsize(op),
            'source_sha256': before,
        })
    tot_s = sum(r['source_bytes'] for r in report)
    tot_o = sum(r['output_bytes'] for r in report)
    json.dump({'encoder': 'Pillow WebP lossless (method 6, exact)', 'resample': 'LANCZOS',
               'total_source_bytes': tot_s, 'total_output_bytes': tot_o, 'items': report},
              open(os.path.join(OUT, 'IMAGE_REPORT.json'), 'w'), indent=1, ensure_ascii=False)
    for r in report:
        print(f"{r['output']:45s} {r['source_bytes']/1e6:6.2f}MB -> {r['output_bytes']/1e6:6.2f}MB {r['output_size']}")
    print(f'TOTAL {tot_s/1e6:.1f}MB -> {tot_o/1e6:.1f}MB')


if __name__ == '__main__':
    sys.exit(main())
