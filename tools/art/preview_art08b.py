#!/usr/bin/env python3
"""DIRECTIVE-ART-08B: Aidan side-walk cadence in the real game, STRIDE 90 (?aidanSideStride=90) vs 52 (test default).
Walks right then left on the peaceful village road (keyboard), then down/up to show the front/back sets are unchanged.
Records 1280x720, crops x3 around the player element (camera-centred). Needs python3 -m http.server 8765."""
import pathlib, shutil, subprocess
from playwright.sync_api import sync_playwright

R = pathlib.Path(__file__).resolve().parents[2]; OUT = R / 'docs/art/qa/art-08b'; TMP = pathlib.Path('/tmp/art08b')


def run(stride):
    tag = f'stride{stride}'; vd = TMP / tag; shutil.rmtree(vd, ignore_errors=True); vd.mkdir(parents=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1280, 'height': 720}, record_video_dir=str(vd), record_video_size={'width': 1280, 'height': 720})
        pg = ctx.new_page(); q = '' if stride == 52 else f'&aidanSideStride={stride}'
        pg.goto(f'http://localhost:8765/index.html?title=0{q}'); pg.wait_for_timeout(1500); pg.evaluate('storyStage=1')
        pg.evaluate("MossForestStory.enterMap('rilde_village','from_inn')"); pg.wait_for_timeout(3000); pg.evaluate('closeDialogue()')
        pg.evaluate("([x,y])=>MossForest.goFeet(x,y)", [600, 712]); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
        box = pg.evaluate("(()=>{const e=document.querySelector('.forest-aidan:not([hidden])')||document.getElementById('player');const r=e.getBoundingClientRect();return [r.left,r.top,r.width,r.height]})()")
        t0 = pg.evaluate('performance.now()')
        for key, ms in (('ArrowRight', 1300), ('ArrowLeft', 1300), ('ArrowDown', 700), ('ArrowUp', 700)):
            pg.keyboard.down(key); pg.wait_for_timeout(ms); pg.keyboard.up(key); pg.wait_for_timeout(500)
        dur = (pg.evaluate('performance.now()') - t0) / 1000; v = pg.video.path(); ctx.close(); b.close()
    cx = box[0] + box[2] / 2; cy = box[1] + box[3] / 2
    x0, y0 = int(cx - 110), int(cy - 70)
    out = OUT / f'aidan_ingame_side_{tag}_x3.mp4'
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-8", "-i", v, '-vf', f'crop=220:140:{x0}:{y0},scale=660:420:flags=neighbor',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-pix_fmt', 'yuv420p', '-an', str(out)], check=True)
    return out, box


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True); print(run(90)); print(run(52))
