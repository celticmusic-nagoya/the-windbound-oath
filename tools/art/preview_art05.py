#!/usr/bin/env python3
"""DIRECTIVE-ART-05: in-game QA of the user-adopted royal soldier (front idle). Browser-only swaps; repository files untouched.

Needs a local server at the repo root (python3 -m http.server 8765). Two swap paths are used:
  * manifest route : the real draw path - img/field/moss/manifest.json is rewritten in-flight so ^npc_slot_soldier$ points at the
                     candidate PNG (every soldier prop on the map uses it, same w/h, bottom-centre anchor);
  * DOM injection  : side-by-side line-up at identical world scale (villagers / old soldier / ART-04 trial / adopted soldier).
Output: docs/art/candidates/art-05/compare_*.png (raw captures in preview/, not committed).
"""
import argparse, json, pathlib, re, subprocess
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

R = pathlib.Path(__file__).resolve().parents[2]
OUT = R / 'docs/art/candidates/art-05'; RAW = OUT / 'preview'
C5 = 'docs/art/candidates/art-05/'
VP = {'pc': (1280, 720), 'land': (915, 412), 'port': (412, 915)}
M = json.loads((R / 'img/field/moss/manifest.json').read_text(encoding='utf-8'))
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SCALE_ADJ = .85   # ADJUST proposal: display size 56x84 -> 47.6x71.4 world (PNG unchanged)


def font(n):
    try: return ImageFont.truetype(FONT, n)
    except OSError: return ImageFont.load_default()


def art(asset):
    for r in M['node']:
        if re.search(r['match'], asset) and r.get('file'):
            im = Image.open(R / M['base'] / r['file'])
            w = r.get('w') or r['h'] * im.width / im.height; h = r.get('h') or r['w'] * im.height / im.width
            return dict(src='img/field/moss/' + r['file'], w=w, h=h)
    raise KeyError(asset)


INJECT = r'''([items, marks])=>{
  const W=document.getElementById('forestWorld');document.querySelectorAll('.art05').forEach(n=>n.remove());
  for(const it of items){const im=document.createElement('img');im.className='art05';im.src=it.src;
    Object.assign(im.style,{position:'absolute',left:(it.x-it.w/2)+'px',top:(it.y-it.h)+'px',width:it.w+'px',height:it.h+'px',zIndex:String(Math.round(it.y)),pointerEvents:'none'});W.appendChild(im);
    if(marks){const d=document.createElement('div');d.className='art05';Object.assign(d.style,{position:'absolute',left:(it.x-2)+'px',top:(it.y-1)+'px',width:'4px',height:'2px',background:'#ff2050',zIndex:'99999'});W.appendChild(d);}}
  if(marks){const l=document.createElement('div');l.className='art05';Object.assign(l.style,{position:'absolute',left:(marks[0])+'px',top:(marks[1])+'px',width:(marks[2])+'px',height:'1px',background:'rgba(255,32,80,.75)',zIndex:'99998'});W.appendChild(l);}
}'''


def label(img, text, sub=None):
    d = ImageDraw.Draw(img); d.rectangle([0, 0, img.width, 46 if sub else 30], fill=(16, 22, 18))
    d.text((10, 4), text, fill=(240, 228, 190), font=font(18))
    if sub: d.text((10, 26), sub, fill=(190, 200, 190), font=font(13))
    return img


def sheet(cells, cols, path, title):
    w = max(c.width for c in cells); rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]; hs = [max(c.height for c in r) for r in rows]
    S = Image.new('RGB', (cols * w + (cols + 1) * 12, sum(hs) + (len(rows) + 1) * 12 + 40), (10, 14, 12))
    ImageDraw.Draw(S).text((14, 8), title, fill=(240, 228, 190), font=font(20)); y = 52
    for r, h in zip(rows, hs):
        for i, c in enumerate(r): S.paste(c, (12 + i * (w + 12), y))
        y += h + 12
    S.save(path)


def page(b, v, routes=None):
    w, h = VP[v]; pg = b.new_page(viewport={'width': w, 'height': h}, is_mobile=(v != 'pc'), has_touch=(v != 'pc'))
    for pat, fn in (routes or {}).items(): pg.route(pat, fn)
    pg.goto(BASE + '/index.html?title=0'); pg.wait_for_timeout(1500); return pg


def enter(pg, stage, spawn):
    pg.evaluate(f'storyStage={stage}'); pg.evaluate(f"MossForestStory.enterMap('rilde_village','{spawn}')"); pg.wait_for_timeout(3300); pg.evaluate('closeDialogue()')


def world_off(pg):
    return pg.evaluate("(()=>{const r=document.getElementById('forestWorld').getBoundingClientRect();return [r.left,r.top]})()")


def lineup():
    adopted = dict(src=C5 + 'soldier_front_idle_112x168_candidate.png', w=56, h=84)
    adj = dict(src=C5 + 'soldier_front_idle_112x168_alphafix_candidate.png', w=56 * SCALE_ADJ, h=84 * SCALE_ADJ)
    a4 = dict(src=C5 + 'preview/art04_npc_soldier_front_idle_01.png', w=56, h=84)
    y = 600; xs = [840, 900, 960, 1020, 1080, 1140, 1200]
    names = ['商人', '農夫', '若い女性', '採用兵士(現寸56×84)', 'ADJUST案(0.85倍)', '旧兵士', 'ART-04試作']
    items = [dict(art('rv_npc_merchant'), x=xs[0], y=y), dict(art('rv_npc_farmer_male'), x=xs[1], y=y), dict(art('rv_npc_young_woman'), x=xs[2], y=y),
             dict(adopted, x=xs[3], y=y), dict(adj, x=xs[4], y=y), dict(art('npc_slot_soldier'), x=xs[5], y=y), dict(a4, x=xs[6], y=y)]
    return items, names, (xs[0] - 40, y, xs[-1] - xs[0] + 80)


def run_lineup(b):
    items, names, line = lineup(); cells = []; zooms = []
    for v in VP:
        pg = page(b, v); enter(pg, 1, 'from_inn')
        pg.evaluate(INJECT, [items, None]); pg.wait_for_timeout(900); off = world_off(pg)
        p = RAW / f'lineup_{v}.png'; pg.screenshot(path=str(p))
        pg.evaluate(INJECT, [items, list(line)]); pg.wait_for_timeout(400); pm = RAW / f'lineup_{v}_marks.png'; pg.screenshot(path=str(pm)); pg.close()
        im = Image.open(p).convert('RGB'); im.thumbnail((640, 640))
        c = Image.new('RGB', (640, im.height + 46), (10, 14, 12)); c.paste(im, ((640 - im.width) // 2, 46))
        cells.append(label(c, {'pc': 'PC 1280×720', 'land': 'Android横相当 915×412（エミュレーション）', 'port': 'Android縦相当 412×915（エミュレーション）'}[v],
                           '左から ' + '／'.join(names) + '／付近にエイダン'))
        if v == 'pc':
            x0 = int(line[0] + off[0]); y0 = int(line[1] + off[1])
            for tag, src in (('2倍', p), ('2倍＋足元anchor（赤点）・接地線', pm)):
                z = Image.open(src).convert('RGB').crop((x0 - 10, y0 - 110, x0 + line[2] + 10, y0 + 14)); z = z.resize((z.width * 2, z.height * 2), Image.NEAREST)
                cz = Image.new('RGB', (z.width, z.height + 46), (10, 14, 12)); cz.paste(z, (0, 46)); zooms.append(label(cz, 'PC ' + tag, '／'.join(names)))
    sheet(cells, 3, OUT / 'compare_soldier_viewports.png', 'ART-05 正式採用 一般兵士｜同一world縮尺の並び（平和村・実ゲーム描画、画像はブラウザ内で配置）')
    sheet(zooms, 1, OUT / 'compare_soldier_zoom2x.png', 'ART-05 2倍拡大（ニアレスト）｜頭身・顔・色調・装備・接地')


def run_realpath(b):
    """Real draw path: manifest ^npc_slot_soldier$ -> adopted PNG; ruin map stage 15 soldier p_rr_knight (1080,800) next to villagers."""
    cells = []
    for tag, fname, wh in (('現行（旧兵士）', None, None), ('採用兵士（現寸56×84）', 'soldier_front_idle_112x168_candidate.png', (56, 84)),
                           ('ADJUST案（0.85倍表示）', 'soldier_front_idle_112x168_alphafix_candidate.png', (56 * SCALE_ADJ, 84 * SCALE_ADJ))):
        def manifest(route, *, fname=fname, wh=wh):
            m = json.loads(route.fetch().text())
            if fname:
                for r in m['node']:
                    if r['match'] == '^npc_slot_soldier$': r['file'] = '../../../' + C5 + fname; r['w'], r['h'] = wh
            route.fulfill(body=json.dumps(m), content_type='application/json')
        for v in ('pc', 'port'):
            pg = page(b, v, {'**/img/field/moss/manifest.json*': manifest}); enter(pg, 15, 'from_plaza')
            pg.evaluate("(()=>{const w=document.getElementById('forestWeather');if(w)w.style.visibility='hidden'})()"); pg.wait_for_timeout(600)
            off = world_off(pg); p = RAW / f'real_{v}_{fname or "now"}.png'; pg.screenshot(path=str(p)); pg.close()
            im = Image.open(p).convert('RGB'); cx, cy = 1080 + off[0], 800 + off[1]
            z = im.crop((int(cx - 170), int(cy - 120), int(cx + 170), int(cy + 50))).resize((680, 340), Image.NEAREST)
            c = Image.new('RGB', (680, 386), (10, 14, 12)); c.paste(z, (0, 46))
            cells.append(label(c, f'{"PC" if v == "pc" else "Android縦相当"}｜{tag}', '襲撃後の村 stage15・兵士p_rr_knight(1080,800)／manifest差し替え＝実際の描画経路／煙レイヤー非表示・2倍'))
    sheet(cells, 2, OUT / 'compare_soldier_realpath.png', 'ART-05 実描画経路での差し替え（manifestをブラウザ内で書換え）')


def run_overlap(b):
    """Draw order: everything is z-sorted by feet y (forest-ent / walkers use zIndex = round(y)); check soldier in front of / behind villagers."""
    sol = dict(src=C5 + 'soldier_front_idle_112x168_candidate.png', w=56, h=84); cells = []
    for tag, items in (('兵士が後ろ（村人の足元yが大きい）', [dict(sol, x=1000, y=596), dict(art('rv_npc_young_woman'), x=1012, y=612), dict(art('rv_npc_merchant'), x=980, y=616)]),
                       ('兵士が前（兵士の足元yが大きい）', [dict(sol, x=1000, y=624), dict(art('rv_npc_young_woman'), x=1014, y=606), dict(art('rv_npc_merchant'), x=982, y=600)])):
        pg = page(b, 'pc'); enter(pg, 1, 'from_inn'); pg.evaluate(INJECT, [items, None]); pg.wait_for_timeout(900); off = world_off(pg)
        p = RAW / f'overlap_{len(cells)}.png'; pg.screenshot(path=str(p)); pg.close()
        z = Image.open(p).convert('RGB').crop((int(940 + off[0]), int(510 + off[1]), int(1070 + off[0]), int(640 + off[1]))); z = z.resize((z.width * 3, z.height * 3), Image.NEAREST)
        c = Image.new('RGB', (z.width, z.height + 46), (10, 14, 12)); c.paste(z, (0, 46)); cells.append(label(c, tag, '採用兵士(現寸)・若い女性・商人／PC 3倍'))
    sheet(cells, 2, OUT / 'compare_soldier_overlap.png', 'ART-05 NPC同士の重なり・描画順（足元y順）')


def main():
    global BASE
    ap = argparse.ArgumentParser(); ap.add_argument('--base', default='http://localhost:8765'); a = ap.parse_args(); BASE = a.base
    RAW.mkdir(parents=True, exist_ok=True)
    # ART-04 trial for reference only (lives on PR #101's branch; copied into the uncommitted preview folder)
    try:
        data = subprocess.run(['git', 'show', 'art/art-01-early-maps:docs/art/candidates/art-04/art04_npc_soldier_front_idle_01.png'], cwd=R, capture_output=True, check=True).stdout
        (RAW / 'art04_npc_soldier_front_idle_01.png').write_bytes(data)
    except subprocess.CalledProcessError:
        print('ART-04 trial not found; line-up slot left empty')
    with sync_playwright() as p:
        b = p.chromium.launch(); run_lineup(b); run_realpath(b); run_overlap(b); b.close()
    print('ok')


if __name__ == '__main__':
    main()
