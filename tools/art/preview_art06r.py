#!/usr/bin/env python3
"""DIRECTIVE-ART-06R comparison: walk_01 / walk_04 candidates vs the adopted idle (static sheet) and an in-game walker check
(browser-only manifest swap: the soldier walk cycle temporarily = [walk_01, walk_04]). Needs python3 -m http.server 8765."""
import json, pathlib, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

R = pathlib.Path(__file__).resolve().parents[2]; D = R / 'docs/art/candidates/art-06r'; TMP = D / 'preview'
F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 14); FS = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 12)
IDLE = R / 'img/field/moss/props/npc_soldier_idle_v2.png'; W01 = D / 'soldier_walk_01_candidate.png'; W04 = D / 'soldier_walk_04_candidate.png'


def static_sheet():
    K = 4; cells = [('採用 正面idle（正本）', IDLE), ('walk_01 右足（画面左）前・接地', W01), ('walk_04 左足（画面右）前・接地', W04)]
    S = Image.new('RGB', (3 * (112 * K + 20) + 20, 168 * K + 70), (20, 24, 22)); d = ImageDraw.Draw(S)
    for i, (t, p) in enumerate(cells):
        B = Image.new('RGBA', (112, 168), (72, 84, 66, 255)); B.alpha_composite(Image.open(p).convert('RGBA')); B = B.resize((112 * K, 168 * K), Image.NEAREST)
        dd = ImageDraw.Draw(B); dd.line([(0, 165 * K + K), (112 * K, 165 * K + K)], fill=(255, 40, 80), width=2); dd.line([(56 * K, 0), (56 * K, 168 * K)], fill=(255, 255, 255), width=1)
        x = 20 + i * (112 * K + 20); S.paste(B.convert('RGB'), (x, 40)); d.text((x, 12), t, fill=(240, 228, 190), font=F)
    d.text((20, 168 * K + 46), '赤線＝接地線（靴底 y=165 の下端）／白線＝中心 x=56。後ろ足は持ち上げて奥へ（少し暗く短く）、前足は接地線のまま。上半身・槍・盾は画素単位でidleと同一（1px沈み込みのみ）', fill=(200, 210, 200), font=FS)
    S.save(D / 'compare_walk01_walk04_x4.png')
    # legs close-up x8 + difference map
    K2 = 8; crops = []
    for t, p in cells:
        B = Image.new('RGBA', (112, 168), (72, 84, 66, 255)); B.alpha_composite(Image.open(p).convert('RGBA')); crops.append((t, B.crop((20, 120, 100, 168)).resize((80 * K2, 48 * K2), Image.NEAREST)))
    S2 = Image.new('RGB', (80 * K2 + 40, 3 * (48 * K2 + 36) + 20), (20, 24, 22)); d2 = ImageDraw.Draw(S2)
    for i, (t, c) in enumerate(crops):
        y = 20 + i * (48 * K2 + 36); d2.text((20, y), t + '（脚まわり 8倍）', fill=(240, 228, 190), font=F); S2.paste(c.convert('RGB'), (20, y + 24))
        d2.line([(20, y + 24 + 46 * K2), (20 + 80 * K2, y + 24 + 46 * K2)], fill=(255, 40, 80), width=2)
    S2.save(D / 'compare_legs_x8.png')


def ingame():
    TMP.mkdir(exist_ok=True); shutil.copy(W01, TMP / 'tmp_walk_01.png'); shutil.copy(W04, TMP / 'tmp_walk_02.png')
    def manifest(route):
        m = json.loads(route.fetch().text())
        for r in m['node']:
            if r['match'] == '^npc_slot_soldier$': r['walk'] = {'file': '../../../docs/art/candidates/art-06r/preview/tmp_walk_{n}.png', 'frames': 2}
        route.fulfill(body=json.dumps(m), content_type='application/json')
    cells = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for v, (w, h) in (('pc', (1280, 720)), ('port', (412, 915))):
            pg = b.new_page(viewport={'width': w, 'height': h}, is_mobile=v != 'pc', has_touch=v != 'pc'); pg.route('**/img/field/moss/manifest.json*', manifest)
            pg.goto('http://localhost:8765/index.html?title=0'); pg.wait_for_timeout(1500); pg.evaluate('storyStage=15')
            pg.evaluate("enterWorldMap('fort')"); pg.wait_for_timeout(1200)
            pg.evaluate("(a)=>MossForest.enter({map:a,spawn:null})", 'royal_capital_02_castle_plaza'); pg.wait_for_timeout(1500)
            pg.evaluate("([x,y])=>MossForest.goFeet(x,y)", [2265, 2800]); pg.wait_for_timeout(3500); pg.evaluate('closeDialogue()')
            got = []
            for i in range(600):
                st = pg.evaluate("(()=>{const w=FieldWalkers.list.find(r=>r.id==='w_r2_herald');return [w.state,w.x,w.y,(w.el.dataset.src||'').split('/').pop(),w.dir]})()")
                key = (st[0], st[3], st[4])
                if not got or got[-1][0] != key:
                    off = pg.evaluate("(()=>{const r=document.getElementById('forestWorld').getBoundingClientRect();return [r.left,r.top]})()")
                    f = TMP / f'g_{v}_{len(got)}.png'; pg.screenshot(path=str(f)); got.append((key, st, off, f))
                    if len(got) >= 8: break
                pg.wait_for_timeout(25)
            pg.close()
            for key, st, off, f in got:
                im = Image.open(f).convert('RGB'); cx, cy = st[1] + off[0], st[2] + off[1]
                z = im.crop((int(cx - 40), int(cy - 80), int(cx + 40), int(cy + 8))).resize((240, 264), Image.NEAREST)
                c = Image.new('RGB', (240, 300), (10, 14, 12)); c.paste(z, (0, 36)); dd = ImageDraw.Draw(c)
                name = {'tmp_walk_01.png': 'walk_01', 'tmp_walk_02.png': 'walk_04', 'npc_soldier_idle_v2.png': 'idle'}.get(st[3], st[3])
                dd.text((6, 4), f'{"PC" if v == "pc" else "縦相当"} {name} {"←" if st[4] < 0 else "→"}', fill=(240, 228, 190), font=F)
                cells.append(c)
        b.close()
    cols = 8; rows = (len(cells) + cols - 1) // cols
    S = Image.new('RGB', (cols * 252 + 12, rows * 312 + 52), (10, 14, 12)); ImageDraw.Draw(S).text((12, 12), '実ゲーム（王都 城前広場の巡回兵）: 歩行を一時的に walk_01⇄walk_04 の2コマにして撮影・3倍（ブラウザ内のみ）', fill=(240, 228, 190), font=F)
    for i, c in enumerate(cells): S.paste(c, (12 + (i % cols) * 252, 48 + (i // cols) * 312))
    S.save(D / 'compare_ingame_walker_x3.png')


if __name__ == '__main__':
    static_sheet(); ingame(); print('ok')
