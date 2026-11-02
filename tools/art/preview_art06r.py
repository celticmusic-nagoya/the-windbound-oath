#!/usr/bin/env python3
"""DIRECTIVE-ART-06R previews for the 6 walk candidates (browser-only swaps; repository files untouched).
  sheet   : idle + walk_01..06 side by side (x3, ground line / centre line) and legs x6
  loop    : 7 fps loop GIF of the sprite alone - normal / mirrored (walking left) / resumed from walk_03, each with idle<->walk switches
  ingame  : the castle-plaza patrol soldier with the manifest walk cycle temporarily = the 6 candidates; per-frame captures and
            an MP4 recording for PC 1280x720, Android landscape 915x412 and portrait 412x915 (emulation, not a device)
Needs python3 -m http.server 8765 at the repo root. Output: docs/art/candidates/art-06r/ (raw captures in preview/, not committed)."""
import json, pathlib, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

R = pathlib.Path(__file__).resolve().parents[2]; D = R / 'docs/art/candidates/art-06r'; TMP = D / 'preview'
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; F = ImageFont.truetype(FONT, 14); FS = ImageFont.truetype(FONT, 12)
IDLE = R / 'img/field/moss/props/npc_soldier_idle_v2.png'
WALK = [D / f'soldier_walk_{i:02d}_candidate.png' for i in range(1, 7)]
NOTES = ['01 右足前・接地（左足は後ろ）', '02 右足に体重・左足通過', '03 左足を前へ', '04 左足前・接地（右足は後ろ）', '05 左足に体重・右足通過', '06 右足を前へ']
BG = (72, 84, 66, 255)


def on_bg(p, k):
    B = Image.new('RGBA', (112, 168), BG); B.alpha_composite(Image.open(p).convert('RGBA')); return B.resize((112 * k, 168 * k), Image.NEAREST)


def sheet():
    K = 3; cells = [('idle（正本）', IDLE)] + list(zip(NOTES, WALK))
    S = Image.new('RGB', (len(cells) * (112 * K + 12) + 12, 168 * K + 64), (20, 24, 22)); d = ImageDraw.Draw(S)
    for i, (t, p) in enumerate(cells):
        B = on_bg(p, K); dd = ImageDraw.Draw(B); dd.line([(0, 166 * K), (112 * K, 166 * K)], fill=(255, 40, 80), width=2); dd.line([(56 * K, 0), (56 * K, 168 * K)], fill=(255, 255, 255), width=1)
        x = 12 + i * (112 * K + 12); S.paste(B.convert('RGB'), (x, 36)); d.text((x, 10), t, fill=(240, 228, 190), font=FS)
    d.text((12, 168 * K + 42), '赤線＝接地線（y=165の下端）・白線＝中心x=56。足の高さ（px）: 接地0 → 後ろ4 → 通過7 → 前へ3 → 接地0。接地コマ（01・04）のみ上半身1px沈み込み。上半身・槍・盾はidleと画素一致', fill=(200, 210, 200), font=FS)
    S.save(D / 'compare_walk6_x3.png')
    K2 = 6; cells2 = [('idle', IDLE)] + [(f'walk_{i:02d}', p) for i, p in enumerate(WALK, 1)]
    S2 = Image.new('RGB', (len(cells2) * (70 * K2 + 10) + 10, 40 * K2 + 40), (20, 24, 22)); d2 = ImageDraw.Draw(S2)
    for i, (t, p) in enumerate(cells2):
        B = on_bg(p, 1).crop((26, 128, 96, 168)).resize((70 * K2, 40 * K2), Image.NEAREST); dd = ImageDraw.Draw(B); dd.line([(0, 38 * K2), (70 * K2, 38 * K2)], fill=(255, 40, 80), width=2)
        x = 10 + i * (70 * K2 + 10); S2.paste(B.convert('RGB'), (x, 32)); d2.text((x, 8), t + '（脚 6倍）', fill=(240, 228, 190), font=F)
    S2.save(D / 'compare_walk6_legs_x6.png')


def loop_gif():
    """3 panels at 7 fps (143 ms): A normal, B mirrored (walking left), C resumed mid-cycle from walk_03; idle holds between walks."""
    K = 2; idle = on_bg(IDLE, K); walks = [on_bg(p, K) for p in WALK]
    def seq(start):
        s = [idle] * 5; i = start
        for _ in range(14): s.append(walks[i % 6]); i += 1
        s += [idle] * 5
        for _ in range(10): s.append(walks[i % 6]); i += 1   # resumes where it stopped (walker clock is not reset)
        return s
    A, B, C = seq(0), [im.transpose(Image.FLIP_LEFT_RIGHT) for im in seq(0)], seq(2)
    frames = []
    for a, b, c in zip(A, B, C):
        S = Image.new('RGB', (3 * 112 * K + 40, 168 * K + 40), (20, 24, 22)); d = ImageDraw.Draw(S)
        for j, (im, t) in enumerate(((a, 'A 右へ歩く'), (b, 'B 左へ歩く（反転）'), (c, 'C walk_03から再開'))):
            S.paste(im.convert('RGB'), (10 + j * (112 * K + 10), 30)); d.text((10 + j * (112 * K + 10), 6), t, fill=(240, 228, 190), font=F)
        frames.append(S.convert('P', palette=Image.ADAPTIVE, colors=255))
    frames[0].save(D / 'loop_walk6_7fps.gif', save_all=True, append_images=frames[1:], duration=143, loop=0, disposal=1)


def ingame():
    TMP.mkdir(exist_ok=True)
    for i, p in enumerate(WALK, 1): shutil.copy(p, TMP / f'tmp_walk_{i:02d}.png')
    def manifest(route):
        m = json.loads(route.fetch().text())
        for r in m['node']:
            if r['match'] == '^npc_slot_soldier$': r['walk'] = {'file': '../../../docs/art/candidates/art-06r/preview/tmp_walk_{n}.png', 'frames': 6}
        route.fulfill(body=json.dumps(m), content_type='application/json')
    cells = []; vids = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for v, (w, h) in (('pc', (1280, 720)), ('land', (915, 412)), ('port', (412, 915))):
            vd = TMP / f'video_{v}'; shutil.rmtree(vd, ignore_errors=True)
            ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=v != 'pc', has_touch=v != 'pc', record_video_dir=str(vd), record_video_size={'width': w, 'height': h})
            pg = ctx.new_page(); pg.route('**/img/field/moss/manifest.json*', manifest)
            pg.goto('http://localhost:8765/index.html?title=0'); pg.wait_for_timeout(1500); pg.evaluate('storyStage=15')
            pg.evaluate("enterWorldMap('fort')"); pg.wait_for_timeout(1200)
            pg.evaluate("(a)=>MossForest.enter({map:a,spawn:null})", 'royal_capital_02_castle_plaza'); pg.wait_for_timeout(1500)
            pg.evaluate("([x,y])=>MossForest.goFeet(x,y)", [2265, 2690]); pg.wait_for_timeout(3500); pg.evaluate('closeDialogue()')
            got = []; seen = set()
            for i in range(900):
                st = pg.evaluate("(()=>{const w=FieldWalkers.list.find(r=>r.id==='w_r2_herald');return [w.state,w.x,w.y,(w.el.dataset.src||'').split('/').pop(),w.dir]})()")
                key = (st[3], st[4])
                if v == 'pc' and key not in seen:
                    seen.add(key); off = pg.evaluate("(()=>{const r=document.getElementById('forestWorld').getBoundingClientRect();return [r.left,r.top]})()")
                    f = TMP / f'g_{len(got)}.png'; pg.screenshot(path=str(f)); got.append((st, off, f))
                if (v == 'pc' and len(seen) >= 14) or (v != 'pc' and i > 300): break
                pg.wait_for_timeout(25)
            pg.wait_for_timeout(500); vpath = pg.video.path(); ctx.close(); vids.append((v, vpath))
            for st, off, f in got:
                im = Image.open(f).convert('RGB'); cx, cy = st[1] + off[0], st[2] + off[1]
                z = im.crop((int(cx - 40), int(cy - 80), int(cx + 40), int(cy + 8))).resize((240, 264), Image.NEAREST)
                c = Image.new('RGB', (240, 300), (10, 14, 12)); c.paste(z, (0, 36))
                name = st[3].replace('tmp_', '').replace('.png', '').replace('npc_soldier_idle_v2', 'idle')
                ImageDraw.Draw(c).text((6, 4), f'{name} {"←" if st[4] < 0 else "→"}', fill=(240, 228, 190), font=F); cells.append((st[4], st[3], c))
        b.close()
    cells.sort(key=lambda t: (-t[0], t[1])); cols = 7; rows = (len(cells) + cols - 1) // cols
    S = Image.new('RGB', (cols * 252 + 12, rows * 312 + 52), (10, 14, 12)); ImageDraw.Draw(S).text((12, 12), '実ゲーム（王都 城前広場の巡回兵・PC）: 歩行6コマ候補をブラウザ内で差し替え、右向き／左向き（反転）の全コマを撮影・3倍', fill=(240, 228, 190), font=F)
    for i, (_, _, c) in enumerate(cells): S.paste(c, (12 + (i % cols) * 252, 48 + (i // cols) * 312))
    S.save(D / 'compare_walk6_ingame_x3.png')
    for v, vp in vids:  # crop the recording around the soldier is not stable (camera); keep full frame, H.264
        out = TMP / f'ingame_walk6_{v}.mp4'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vp, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p', '-an', str(out)], check=True)
    return [TMP / f'ingame_walk6_{v}.mp4' for v, _ in vids]


if __name__ == '__main__':
    sheet(); loop_gif(); print('videos', ingame())
