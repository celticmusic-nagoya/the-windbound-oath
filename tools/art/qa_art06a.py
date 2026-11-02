#!/usr/bin/env python3
"""DIRECTIVE-ART-05D visual QA of the implemented soldier (no swaps: the committed manifest/PNG are what the game loads).
Needs python3 -m http.server 8765 at the repo root. Output: docs/art/qa/art-06a/*.png + results.json (raw captures not kept)."""
import json, pathlib
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

R = pathlib.Path(__file__).resolve().parents[2]; OUT = R / 'docs/art/qa/art-06a'; TMP = pathlib.Path('/tmp/art06a'); BASE = 'http://localhost:8765'
VP = {'pc': (1280, 720), 'land': (915, 412), 'port': (412, 915)}
F = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SCENES = [  # (key, title, map, spawn-or-None, feet to stand at, soldier feet, stage)
    ('ruin', '襲撃後の村 p_rr_knight（固定NPC）', 'rilde_village_01_ruin', 'from_plaza', None, (1080, 800), 15),
    ('keep', '砦 主塔 p_f3_armory（固定NPC）', 'fort_dunvall_03_keep', None, (420, 990), (420, 900), 15),
    ('plaza', '王都 城前広場 w_r2_herald（巡回＝歩行は旧コマ）', 'royal_capital_02_castle_plaza', None, (2300, 2700), (2300, 2600), 15),
]


def font(n):
    try: return ImageFont.truetype(F, n)
    except OSError: return ImageFont.load_default()


def label(im, t, s=None):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, im.width, 46 if s else 30], fill=(16, 22, 18)); d.text((10, 4), t, fill=(240, 228, 190), font=font(18))
    if s: d.text((10, 26), s, fill=(190, 200, 190), font=font(13))
    return im


def sheet(cells, cols, path, title):
    w = max(c.width for c in cells); rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]; hs = [max(c.height for c in r) for r in rows]
    S = Image.new('RGB', (cols * w + (cols + 1) * 12, sum(hs) + (len(rows) + 1) * 12 + 40), (10, 14, 12)); ImageDraw.Draw(S).text((14, 8), title, fill=(240, 228, 190), font=font(20)); y = 52
    for r, h in zip(rows, hs):
        for i, c in enumerate(r): S.paste(c, (12 + i * (w + 12), y))
        y += h + 12
    S.save(path)


PROBE = r'''()=>{
  const out={props:[],walkers:[]};
  for(const n of document.querySelectorAll('.forest-ent[data-asset="npc_slot_soldier"]')){const r=n.getBoundingClientRect();
    out.props.push({src:n.getAttribute('src'),w:parseFloat(n.style.width),h:parseFloat(n.style.height),left:parseFloat(n.style.left),top:parseFloat(n.style.top),loaded:n.complete&&n.naturalWidth>0,nat:[n.naturalWidth,n.naturalHeight]});}
  for(const n of document.querySelectorAll('.forest-walker')){if(!/npc_soldier/.test(n.getAttribute('src')||''))continue;
    out.walkers.push({src:n.getAttribute('src'),w:parseFloat(n.style.width),h:parseFloat(n.style.height),loaded:n.complete&&n.naturalWidth>0});}
  return out;}'''


def main():
    OUT.mkdir(parents=True, exist_ok=True); TMP.mkdir(exist_ok=True); res = {}; cells = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for key, title, mid, spawn, stand, feet, stage in SCENES:
            for v, (w, h) in VP.items():
                pg = b.new_page(viewport={'width': w, 'height': h}, is_mobile=(v != 'pc'), has_touch=(v != 'pc'))
                errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.goto(BASE + '/index.html?title=0'); pg.wait_for_timeout(1500); pg.evaluate(f'storyStage={stage}')
                if mid.startswith('rilde'): pg.evaluate(f"MossForestStory.enterMap('rilde_village','{spawn}')")
                else:
                    pg.evaluate("enterWorldMap('fort')"); pg.wait_for_timeout(1200)
                    pg.evaluate("(a)=>MossForest.enter({map:a,spawn:null})", mid); pg.wait_for_timeout(1500)
                    pg.evaluate("([x,y])=>MossForest.goFeet(x,y)", list(stand))
                pg.wait_for_timeout(3000); pg.evaluate('closeDialogue()')
                pg.evaluate("(()=>{const w=document.getElementById('forestWeather');if(w)w.style.visibility='hidden'})()"); pg.wait_for_timeout(700)
                frames = []
                for k in range(3):  # walkers cycle frames: capture a few moments
                    f = TMP / f'{key}_{v}_{k}.png'; pg.screenshot(path=str(f)); frames.append(f); pg.wait_for_timeout(260)
                info = pg.evaluate(PROBE); info['mapId'] = pg.evaluate('MossForest.mapId'); info['pageErrors'] = errs
                off = pg.evaluate("(()=>{const r=document.getElementById('forestWorld').getBoundingClientRect();return [r.left,r.top]})()")
                res[f'{key}_{v}'] = info; pg.close()
                if v == 'pc' or key == 'ruin':
                    cx, cy = feet[0] + off[0], feet[1] + off[1]
                    for k, f in enumerate(frames if key == 'plaza' and v == 'pc' else frames[:1]):
                        im = Image.open(f).convert('RGB')
                        z = im.crop((int(cx - 150), int(cy - 110), int(cx + 150), int(cy + 40))).resize((600, 300), Image.NEAREST)
                        c = Image.new('RGB', (600, 346), (10, 14, 12)); c.paste(z, (0, 46))
                        cells.append(label(c, f'{title}', f'{ {"pc":"PC","land":"Android横相当","port":"Android縦相当"}[v] }・2倍' + (f'・時刻{k}' if key == 'plaza' and v == 'pc' else '') + '・煙レイヤー非表示'))
                full = Image.open(frames[0]).convert('RGB'); full.thumbnail((640, 640))
                (TMP / f'thumb_{key}_{v}.png').write_bytes(b'')
                full.save(TMP / f'thumb_{key}_{v}.png')
        b.close()
    sheet(cells, 3, OUT / 'qa_soldier_zoom2x.png', 'ART-06A マージ後(main 85fa777)の一般兵士（コミット済みmanifest/PNGをそのまま読み込み）')
    th = []
    for key, title, *_ in SCENES:
        for v in VP:
            im = Image.open(TMP / f'thumb_{key}_{v}.png'); c = Image.new('RGB', (640, im.height + 30), (10, 14, 12)); c.paste(im, ((640 - im.width) // 2, 30))
            th.append(label(c, f'{title}｜{ {"pc":"PC","land":"Android横相当","port":"Android縦相当"}[v] }'))
    sheet(th, 3, OUT / 'qa_soldier_viewports.png', 'ART-06A PC／Android横・縦相当（エミュレーション、実機QAではない）')
    (OUT / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for k, v in res.items(): print(k, v['mapId'], [(x['w'], x['h'], x['loaded'], x['src'][-28:]) for x in v['props']], [(x['w'], x['h'], x['loaded']) for x in v['walkers']], v['pageErrors'][:1])


if __name__ == '__main__':
    main()
