#!/usr/bin/env python3
"""DIRECTIVE-ART-08E previews.
  loop   : offline, distance-driven like the runtime: current 4 frames @90 vs trial 6 frames @50, right and left, ground ticks
  ingame : real game (trial branch as committed), peaceful village road; walk right, left, down, up with the keyboard;
           PC 1280x720 / Android landscape 915x412 / portrait 412x915 (emulation); x3 crop around the camera-centred hero
  log    : which frame is shown per sample while walking (sequence check, 06 -> 01 wrap, front/back unchanged)
Needs python3 -m http.server 8765. Output: docs/art/qa/art-08e/"""
import json, pathlib, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

R = pathlib.Path(__file__).resolve().parents[2]; OUT = R / 'docs/art/qa/art-08e'; TMP = pathlib.Path('/tmp/art08e')
F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 14)
K = 3; SC = .0625 * K; AN = (1024, 1230)


def ld(p):
    im = Image.open(p).convert('RGBA'); return im.resize((round(im.width * SC), round(im.height * SC)), Image.LANCZOS)


def loop():
    sets = {}
    for side in ('right', 'left'):
        sets[side] = ([ld(R / f'img/field/characters/aidan/aidan_walk_{side}_{i:02d}.png') for i in range(1, 5)],
                      [ld(R / f'img/field/characters/aidan/side6/aidan_walk_{side}_{i:02d}.png') for i in range(1, 7)])
    def panel(dist, fr, stride, title, side):
        W, H = 300, 250; S = Image.new('RGB', (W, H), (52, 62, 48)); d = ImageDraw.Draw(S); gy = 212
        d.rectangle([0, gy, W, H], fill=(150, 120, 80)); sh = int(dist * K) % (10 * K) * (1 if side == 'right' else -1)
        for wx in range(-70, 80, 10): sx = W // 2 + wx * K - sh; d.line([(sx, gy), (sx, gy + 8)], fill=(90, 70, 45), width=2)
        n = len(fr); ph = int(dist // (stride / n)) % n; im = fr[ph]
        S.paste(im, (W // 2 - round(AN[0] * SC), gy - round(AN[1] * SC)), im)
        d.text((6, 4), title, fill=(240, 228, 190), font=F); d.text((6, 22), f'{ph + 1:02d}/{n:02d}', fill=(200, 210, 200), font=F); return S
    frames = []
    for t in range(140):
        dist = t * 1.5; S = Image.new('RGB', (2 * 310 + 10, 2 * 260), (20, 24, 22))
        for r, side in enumerate(('right', 'left')):
            old, new = sets[side]
            S.paste(panel(dist, old, 90, f'現行4コマ・周期90（{side}）', side), (0, r * 260)); S.paste(panel(dist, new, 50, f'候補6コマ・周期50（{side}）', side), (320, r * 260))
        frames.append(S.convert('P', palette=Image.ADAPTIVE, colors=220))
    frames[0].save(OUT / 'loop_side_4vs6_slow.gif', save_all=True, append_images=frames[1:], duration=33, loop=0)
    # game speed: keyboard ~300 world/s (field-movement pointerStep 5 world per 60 Hz frame); 50 fps GIF = 6 world per tick
    frames = []
    for t in range(150):
        dist = t * 6.0; S = Image.new('RGB', (3 * 310 + 10, 260), (20, 24, 22)); old, new = sets['right']
        for j, (fr, st, tt) in enumerate(((old, 90, '現行4コマ・周期90'), (new, 50, '候補6コマ・周期50'), (new, 72, '候補6コマ・周期72'))):
            S.paste(panel(dist, fr, st, tt + '（実速度）', 'right'), (j * 310, 0))
        frames.append(S.convert('P', palette=Image.ADAPTIVE, colors=220))
    frames[0].save(OUT / 'loop_side_gamespeed.gif', save_all=True, append_images=frames[1:], duration=20, loop=0)
    # still strip, both sides
    S = Image.new('RGB', (6 * 230 + 20, 2 * 250 + 20), (20, 24, 22)); d = ImageDraw.Draw(S)
    for r, side in enumerate(('right', 'left')):
        for i in range(6):
            im = Image.open(R / f'img/field/characters/aidan/side6/aidan_walk_{side}_{i + 1:02d}.png').convert('RGBA').crop((700, 140, 1500, 1240)).resize((218, 300), Image.LANCZOS).crop((0, 60, 218, 300))
            B = Image.new('RGBA', im.size, (72, 84, 66, 255)); B.alpha_composite(im); S.paste(B.convert('RGB'), (10 + i * 230, 10 + r * 250)); d.text((14 + i * 230, 12 + r * 250), f'{side}_{i + 1:02d}', fill=(255, 255, 255), font=F)
    S.save(OUT / 'strip_side6.png')


SAMPLE = r'''async (ms)=>{const out=[];const t0=performance.now();while(performance.now()-t0<ms){const e=document.querySelector('.forest-aidan:not([hidden])');
  out.push(e?e.src.split('/').pop().split('?')[0]:null);await new Promise(r=>setTimeout(r,30));}return out;}'''


def ingame():
    res = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for v, (w, h) in (('pc', (1280, 720)), ('land', (915, 412)), ('port', (412, 915))):
            vd = TMP / v; shutil.rmtree(vd, ignore_errors=True); vd.mkdir(parents=True)
            ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=v != 'pc', has_touch=v != 'pc', record_video_dir=str(vd), record_video_size={'width': w, 'height': h})
            pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.goto('http://localhost:8765/index.html?title=0'); pg.wait_for_timeout(1500); pg.evaluate('storyStage=1')
            pg.evaluate("MossForestStory.enterMap('rilde_village','from_inn')"); pg.wait_for_timeout(3000); pg.evaluate('closeDialogue()')
            pg.evaluate("([x,y])=>MossForest.goFeet(x,y)", [600, 712]); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
            seqs = {}; box = None
            for key, ms in (('ArrowRight', 1500), ('ArrowLeft', 1500), ('ArrowDown', 900), ('ArrowUp', 900)):
                pg.keyboard.down(key); pg.wait_for_timeout(300)
                if box is None: box = pg.evaluate("(()=>{const r=document.querySelector('.forest-aidan:not([hidden])').getBoundingClientRect();return [r.left,r.top,r.width,r.height]})()")
                seqs[key] = pg.evaluate(SAMPLE, ms - 400); pg.keyboard.up(key); pg.wait_for_timeout(450)
            vp = pg.video.path(); ctx.close()
            def compress(seq):
                o = []
                for s in seq:
                    if s and (not o or o[-1] != s): o.append(s)
                return o
            res[v] = {k: compress(s) for k, s in seqs.items()}; res[v]['pageErrors'] = errs
            cx, cy = box[0] + box[2] / 2, box[1] + box[3] * .55; out = OUT / f'ingame_side6_{v}_x3.mp4'
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-sseof', '-7.5', '-i', vp, '-vf', f'crop=220:150:{int(cx - 110)}:{int(cy - 80)},scale=660:450:flags=neighbor',
                            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p', '-an', str(out)], check=True)
        b.close()
    (OUT / 'ingame_frame_sequence.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    for v, r in res.items():
        print(v, {k: [x.replace('aidan_walk_', '').replace('.png', '') for x in s][:14] for k, s in r.items() if k != 'pageErrors'}, r['pageErrors'][:1])


def shots():
    """Sharper in-game clips: clipped screenshots while walking (right, left, down, up), assembled with their real timestamps."""
    with sync_playwright() as p:
        b = p.chromium.launch()
        for v, (w, h) in (('pc', (1280, 720)), ('land', (915, 412)), ('port', (412, 915))):
            pg = b.new_page(viewport={'width': w, 'height': h}, is_mobile=v != 'pc', has_touch=v != 'pc')
            pg.goto('http://localhost:8765/index.html?title=0'); pg.wait_for_timeout(1500); pg.evaluate('storyStage=1')
            pg.evaluate("MossForestStory.enterMap('rilde_village','from_inn')"); pg.wait_for_timeout(3000); pg.evaluate('closeDialogue()')
            pg.evaluate("([x,y])=>MossForest.goFeet(x,y)", [600, 712]); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
            d = TMP / f'shots_{v}'; shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True); lst = []; n = 0; import time
            for key, ms in (('ArrowRight', 1600), ('ArrowLeft', 1600), ('ArrowDown', 900), ('ArrowUp', 900)):
                pg.keyboard.down(key); t0 = time.time()
                while time.time() - t0 < ms / 1000:
                    r = pg.evaluate("(()=>{const e=document.querySelector('.forest-aidan:not([hidden])');const b=e.getBoundingClientRect();return [b.left+b.width/2,b.top+b.height*.55]})()")
                    f = d / f'{n:04d}.png'; pg.screenshot(path=str(f), clip={'x': max(0, r[0] - 90), 'y': max(0, r[1] - 60), 'width': 180, 'height': 110}); lst.append((f, time.time())); n += 1
                pg.keyboard.up(key); pg.wait_for_timeout(300)
            pg.close()
            with open(d / 'list.txt', 'w') as fh:
                for (f, t), (_, t2) in zip(lst, lst[1:] + [(None, lst[-1][1] + .05)]): fh.write(f"file '{f}'\nduration {max(.01, t2 - t):.3f}\n")
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(d / 'list.txt'), '-vf', 'scale=540:330:flags=neighbor,fps=30',
                            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', str(OUT / f'ingame_side6_{v}_x3.mp4')], check=True)
        b.close()


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True); loop(); ingame(); shots()   # shots() overwrites the recorded clips with sharper ones
