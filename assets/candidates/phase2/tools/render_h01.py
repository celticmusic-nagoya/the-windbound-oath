#!/usr/bin/env python3
"""In-game check of the house_01 deliveries, browser-only (repository, map and manifest files untouched).
The browser receives (1) rilde_in_house_01.json with the 13 props re-pointed to the new furn_h01_* ids and (2) manifest.json with
rules for those ids (same w/h as the current assets, files served from a temporary copy of the inbox). Positions, collision and
event zones are not modified. Aidan = live player at the default spawn; Fiona and Lou are placed beside him; collision outlined.
Usage (repo root, python3 -m http.server 8765 running): python3 /home/claude/h01/tools/render_h01.py <inbox> [tag]"""
import json, pathlib, shutil, sys
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

H01 = pathlib.Path(__file__).resolve().parents[1]; R = pathlib.Path.cwd(); SPEC = json.loads((next(p for p in (H01 / 'spec/h01_asset_spec.json', pathlib.Path(__file__).resolve().parent / 'h01_asset_spec.json') if p.exists())).read_text())
F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 15)
VP = {'pc': (1280, 720), 'land': (915, 412), 'port': (412, 915)}
SERVE = '_h01_serve/'   # temporary, deleted at the end; never committed
EXTRA = r'''(a)=>{const W=document.getElementById('forestWorld');document.querySelectorAll('.h01qa').forEach(n=>n.remove());
  for(const it of a.items){const im=document.createElement('img');im.className='h01qa';im.src=it.src;
    Object.assign(im.style,{position:'absolute',left:(it.x-it.w/2)+'px',top:(it.y-it.h)+'px',width:it.w+'px',height:it.h+'px',zIndex:String(Math.round(it.y)),pointerEvents:'none'});W.appendChild(im);}
  for(const r of a.rects){const d=document.createElement('div');d.className='h01qa';Object.assign(d.style,{position:'absolute',left:r[0]+'px',top:r[1]+'px',width:r[2]+'px',height:r[3]+'px',outline:'1px solid rgba(255,40,90,.9)',zIndex:'99999',pointerEvents:'none'});W.appendChild(d);}}'''


def main():
    inbox = pathlib.Path(sys.argv[1]); tag = sys.argv[2] if len(sys.argv) > 2 else 'delivery'; out = H01 / 'report'; out.mkdir(exist_ok=True)
    srv = R / SERVE; shutil.rmtree(srv, ignore_errors=True); srv.mkdir()
    for it in SPEC['items']:
        if (inbox / it['file']).exists(): shutil.copy(inbox / it['file'], srv / it['file'])
    by_prop = {it['prop_id']: it for it in SPEC['items'] if (srv / it['file']).exists()}

    def maproute(route):
        d = json.loads(route.fetch().text())
        for p in d['props']:
            if p['id'] in by_prop: p['asset'] = by_prop[p['id']]['new_asset_id']
        route.fulfill(body=json.dumps(d, ensure_ascii=False), content_type='application/json')

    def manroute(route):
        m = json.loads(route.fetch().text())
        m['node'][0:0] = [{'match': '^' + it['new_asset_id'] + '$', 'file': '../../../' + SERVE + it['file'], 'w': it['world'][0], 'h': it['world'][1]} for it in by_prop.values()]
        route.fulfill(body=json.dumps(m), content_type='application/json')

    mp = json.loads((R / 'data/maps/rilde_in_house_01.json').read_text()); rects = [rc for b in mp['collision']['blockers'] for rc in b['rects']]
    fiona = dict(src='img/field/moss/real/fiona/fiona_idle_down.png', w=128, h=83.2); lou = dict(src='img/field/characters/lou/lou_idle_00.png', w=73 * 52 / 120, h=52)
    shots = {}; errs_all = {}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for mode in ('now', tag):
                for v, (w, h) in VP.items():
                    pg = b.new_page(viewport={'width': w, 'height': h}, is_mobile=v != 'pc', has_touch=v != 'pc'); errs = []
                    pg.on('pageerror', lambda e: errs.append(str(e)))
                    if mode != 'now':
                        pg.route('**/data/maps/rilde_in_house_01.json*', maproute); pg.route('**/img/field/moss/manifest.json*', manroute)
                    pg.goto('http://localhost:8765/index.html?title=0'); pg.wait_for_timeout(1500); pg.evaluate('storyStage=1')
                    pg.evaluate("MossForestStory.enterMap('rilde_in_house_01','default')"); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
                    ft = pg.evaluate("(()=>{const f=MossForest.feet;return [f.x,f.y]})()")
                    pg.evaluate(EXTRA, dict(items=[dict(fiona, x=ft[0] + 60, y=ft[1] + 6), dict(lou, x=ft[0] - 40, y=ft[1] - 18)], rects=rects)); pg.wait_for_timeout(900)
                    loaded = pg.evaluate("[...document.querySelectorAll('img.forest-ent')].filter(i=>/furn_h01_/.test(i.dataset.asset||'')).map(i=>[i.dataset.asset,i.complete&&i.naturalWidth>0])")
                    f = out / f'_{mode}_{v}.png'; pg.screenshot(path=str(f)); pg.close(); shots[(mode, v)] = f; errs_all[f'{mode}_{v}'] = dict(pageErrors=errs, h01_loaded=loaded)
            b.close()
    finally:
        shutil.rmtree(srv, ignore_errors=True)
    vl = {'pc': 'PC 1280×720', 'land': 'Android横相当 915×412', 'port': 'Android縦相当 412×915'}
    for v in VP:
        ims = []
        for mode in ('now', tag):
            im = Image.open(shots[(mode, v)]).convert('RGB'); im.thumbnail((720, 720)); c = Image.new('RGB', (720, im.height + 30), (10, 14, 12)); c.paste(im, (0, 30))
            ImageDraw.Draw(c).text((8, 5), f'{vl[v]}｜{"現行" if mode == "now" else tag}', fill=(240, 228, 190), font=F); ims.append(c)
        S = Image.new('RGB', (2 * 732 + 12, max(i.height for i in ims) + 50), (10, 14, 12)); ImageDraw.Draw(S).text((12, 10), 'rilde_in_house_01｜赤枠＝既存の当たり判定（変更なし）。エイダン（操作中）・フィオナ・ルーと比較。Androidはエミュレーション', fill=(240, 228, 190), font=F)
        for i, c in enumerate(ims): S.paste(c, (12 + i * 732, 40))
        S.save(out / f'render_{tag}_{v}.png')
    zs = []   # PC 2x zoom of the room (centred 860x640 world at zoom 1 -> screen x 210..1070, y 40..680)
    for mode in ('now', tag):
        z = Image.open(shots[(mode, 'pc')]).convert('RGB').crop((210, 40, 1070, 680)); z = z.resize((z.width * 2, z.height * 2), Image.NEAREST)
        c = Image.new('RGB', (z.width, z.height + 34), (10, 14, 12)); c.paste(z, (0, 34)); ImageDraw.Draw(c).text((8, 6), f'PC 2倍｜{"現行" if mode == "now" else tag}（赤枠＝当たり判定）', fill=(240, 228, 190), font=F); zs.append(c)
    S = Image.new('RGB', (zs[0].width * 2 + 12, zs[0].height), (10, 14, 12)); S.paste(zs[0], (0, 0)); S.paste(zs[1], (zs[0].width + 12, 0)); S.save(out / f'render_{tag}_pc_zoom2x.png')
    for f in shots.values(): f.unlink()
    (out / f'render_{tag}.json').write_text(json.dumps(errs_all, ensure_ascii=False, indent=1) + '\n'); print(json.dumps({k: (len(v['h01_loaded']), v['pageErrors'][:1]) for k, v in errs_all.items()}))


if __name__ == '__main__':
    main()
