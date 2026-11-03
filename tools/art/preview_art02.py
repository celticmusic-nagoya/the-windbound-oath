#!/usr/bin/env python3
"""DIRECTIVE-ART-02 previews (visual review only; nothing here is adopted or referenced by the game).

Runs the real game on a local server (default http://localhost:8765, start with `python3 -m http.server 8765`)
and changes only what the *browser* receives for the preview session:
  * house   : intercepts forest-layer.js / rilde_in_aidan.json / manifest.json in-flight so the ART-01 candidate tiles are drawn
              (prototype of Codex K1/K2). Repository files are untouched.
  * casting : stage-15 ruin map, hides the post-prologue NPCs (p_rr_*) and places existing NPC PNGs at the ART-01 draft coordinates.
  * derived : downscaled copies of the formal battle goblin idles, written as *_preview.png (field-symbol size study).
  * sanctum : A3 dead-tree placeholder vs. reuse of the existing veg_thorn_L_02.
  * scenes  : Lou intro / altar with the text capsules swapped for existing field PNGs (prototype of Codex K5/K6).
Output: docs/art/candidates/art-02/
"""
import argparse, json, pathlib, re
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

R = pathlib.Path(__file__).resolve().parents[2]
OUT = R / 'docs/art/candidates/art-02'
VP = {'pc': (1280, 720), 'port': (412, 915), 'land': (915, 412)}
C1 = 'docs/art/candidates/art-01/'
FONT = None
for f in ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
          '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc'):
    if pathlib.Path(f).exists(): FONT = f; break


def font(n):
    return ImageFont.truetype(FONT, n) if FONT else ImageFont.load_default()


# ---------------------------------------------------------------- derived goblin field-size studies
GOBLIN_H = 60  # world px visible height (Aidan field = 69, see aidan-field-assets.js bounds*scale)


def derived():
    out = OUT / 'derived'; out.mkdir(parents=True, exist_ok=True); res = {}
    for key, src in (('goblin', 'img/battle/enemies/goblin/goblin_battle_idle.png'),
                     ('tainted_goblin', 'img/battle/enemies/tainted_goblin/goblin_battle_idle.png')):
        im = Image.open(R / src).convert('RGBA')
        bb = im.getchannel('A').point(lambda v: 255 if v > 16 else 0).getbbox(); im = im.crop(bb)
        h = GOBLIN_H * 2; w = round(im.width * h / im.height)
        sm = im.resize((w, h), Image.LANCZOS)
        name = f'{key}_field_idle_derived_preview.png'; sm.save(out / name)
        res[key] = dict(file='derived/' + name, src=src, px=[w, h], world=[w / 2, h / 2])
    return res


# ---------------------------------------------------------------- shared helpers
def page(b, v, routes=None, init=None):
    w, h = VP[v]
    pg = b.new_page(viewport={'width': w, 'height': h}, is_mobile=(v != 'pc'), has_touch=(v != 'pc'))
    if init: pg.add_init_script(init)
    for pat, fn in (routes or {}).items(): pg.route(pat, fn)
    return pg


def boot(pg, base):
    pg.goto(base + '/index.html?title=0'); pg.wait_for_timeout(1500)


INJECT = r'''(items)=>{
  const W=document.getElementById('forestWorld');
  document.querySelectorAll('.art02-preview').forEach(n=>n.remove());
  for(const it of items){const im=document.createElement('img');im.className='art02-preview';im.src=it.src;
    Object.assign(im.style,{position:'absolute',left:(it.x-it.w/2)+'px',top:(it.y-it.h)+'px',width:it.w+'px',height:it.h+'px',
      zIndex:String(Math.round(it.y)),pointerEvents:'none',imageRendering:'auto',transform:it.flip?'scaleX(-1)':''});W.appendChild(im);}
}'''


def label(img, text, sub=None):
    d = ImageDraw.Draw(img); d.rectangle([0, 0, img.width, 44 if sub else 30], fill=(16, 22, 18))
    d.text((10, 4), text, fill=(240, 228, 190), font=font(18))
    if sub: d.text((10, 25), sub, fill=(190, 200, 190), font=font(13))
    return img


def sheet(cells, cols, path, title):
    w = max(c.width for c in cells); rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    hs = [max(c.height for c in r) for r in rows]
    S = Image.new('RGB', (cols * w + (cols + 1) * 12, sum(hs) + (len(rows) + 1) * 12 + 40), (10, 14, 12))
    ImageDraw.Draw(S).text((14, 8), title, fill=(240, 228, 190), font=font(20)); y = 52
    for r, h in zip(rows, hs):
        for i, c in enumerate(r): S.paste(c, (12 + i * (w + 12), y))
        y += h + 12
    S.save(path); return path


# ---------------------------------------------------------------- house (in-game, candidate tiles)
PATCH_FIND = 'if(f.pattern&&hit.length)for(const r of hit)paint(ctx,f.pattern,r,ox,oy,chunk);'
PATCH_ADD = ("if(f.texture&&hit.length&&window.__ART02_TEX&&window.__ART02_TEX[f.texture]){const im=window.__ART02_TEX[f.texture];"
             "const pt=ctx.createPattern(im,'repeat');ctx.imageSmoothingEnabled=false;for(const r of hit){pt.setTransform(new DOMMatrix().translate(r[0],r[1]).scale(.5));"
             "ctx.save();ctx.beginPath();ctx.rect(r[0],r[1],r[2],r[3]);ctx.clip();ctx.fillStyle=pt;ctx.fillRect(r[0],r[1],r[2],r[3]);ctx.restore();}}")
TEX = {k: C1 + f'art01_{k}.png' for k in ('int_floor_planks_01', 'int_wall_planks_01', 'int_baseboard_01', 'int_wallcap_left_01', 'int_wallcap_right_01',
                                           'int_wallcap_bottom_01', 'int_wallcap_corner_sw_01', 'int_wallcap_corner_se_01', 'int_door_threshold_01')}


def house_routes(base):
    def layer(route):
        body = route.fetch().text(); assert PATCH_FIND in body, 'forest-layer.js changed; update PATCH_FIND'
        route.fulfill(body=body.replace(PATCH_FIND, PATCH_FIND + PATCH_ADD), content_type='application/javascript')

    def mapjson(route):
        d = json.loads(route.fetch().text()); dark = '#17110d'
        d['terrain']['fills'] = [
            {'id': 'fill_0', 'color': dark, 'rects': [[0, 0, 960, 720]]},
            {'id': 'wall', 'color': '#76654f', 'texture': 'int_wall_planks_01', 'rects': [[48, 48, 864, 150]]},
            {'id': 'floor', 'color': '#a98b5c', 'texture': 'int_floor_planks_01', 'rects': [[48, 198, 864, 474]]},
            {'id': 'base', 'color': '#3a2c20', 'texture': 'int_baseboard_01', 'rects': [[48, 188, 864, 12]]},
            {'id': 'capL', 'color': dark, 'texture': 'int_wallcap_left_01', 'rects': [[0, 0, 48, 672]]},
            {'id': 'capR', 'color': dark, 'texture': 'int_wallcap_right_01', 'rects': [[912, 0, 48, 672]]},
            {'id': 'capB', 'color': dark, 'texture': 'int_wallcap_bottom_01', 'rects': [[48, 672, 864, 48]]},
            {'id': 'capSW', 'color': dark, 'texture': 'int_wallcap_corner_sw_01', 'rects': [[0, 672, 48, 48]]},
            {'id': 'capSE', 'color': dark, 'texture': 'int_wallcap_corner_se_01', 'rects': [[912, 672, 48, 48]]},
            {'id': 'door', 'color': dark, 'texture': 'int_door_threshold_01', 'rects': [[410, 672, 140, 48]]}]
        route.fulfill(body=json.dumps(d, ensure_ascii=False), content_type='application/json')

    def manifest(route):
        m = json.loads(route.fetch().text())
        for r in m['node']:
            if r['match'] == '^furn_doormat$': r['file'] = '../../../' + C1 + 'art01_furn_doormat_woven_01.png'
        route.fulfill(body=json.dumps(m), content_type='application/json')

    init = 'window.__ART02_TEX={};' + ''.join(
        f"(()=>{{const i=new Image();i.src='{base}/{p}';window.__ART02_TEX['{k}']=i}})();" for k, p in TEX.items())
    return {'**/js/field/forest-layer.js*': layer, '**/data/maps/rilde_in_aidan.json*': mapjson, '**/img/field/moss/manifest.json*': manifest}, init


def house(b, base):
    out = OUT / 'house'; out.mkdir(parents=True, exist_ok=True); files = {}
    for v in VP:
        for tag in ('before', 'after'):
            routes, init = house_routes(base) if tag == 'after' else ({}, None)
            pg = page(b, v, routes, init); boot(pg, base)
            pg.evaluate('RildeVillage.startOpening()'); pg.wait_for_timeout(2600); pg.evaluate('closeDialogue()'); pg.wait_for_timeout(1200)
            p = out / f'house_{v}_{tag}.png'; pg.screenshot(path=str(p)); pg.close(); files[(v, tag)] = p
    for tag in ('before', 'after'):   # entrance close-up: x2 crop of the PC capture around tr_exit (room is centred: offset x=160)
        im = Image.open(files[('pc', tag)]); c = im.crop((160 + 330, 520, 160 + 630, 720)).resize((600, 400), Image.NEAREST)
        p = out / f'house_entrance_{tag}.png'; c.save(p); files[('door', tag)] = p
    cells = []
    for v, nm in (('pc', 'PC 1280×720'), ('land', 'Android横相当 915×412'), ('port', 'Android縦相当 412×915'), ('door', '入口付近 2倍拡大')):
        for tag, jp in (('before', '現在'), ('after', '候補')):
            im = Image.open(files[(v, tag)]).convert('RGB'); im.thumbnail((640, 640))
            c = Image.new('RGB', (640, im.height + 30), (10, 14, 12)); c.paste(im, ((640 - im.width) // 2, 30)); cells.append(label(c, f'{nm}｜{jp}'))
    return sheet(cells, 2, OUT / 'compare_house_viewports.png', 'ART-02 エイダンの自宅｜現在 vs 候補（実ゲーム描画・候補はブラウザ内差し替えのみ）')


# ---------------------------------------------------------------- casting on the ruin map
M = json.loads((R / 'img/field/moss/manifest.json').read_text(encoding='utf-8'))


def art(asset):
    for r in M['node']:
        if re.search(r['match'], asset) and r.get('file'):
            im = Image.open(R / M['base'] / r['file'])
            w = r.get('w') or r['h'] * im.width / im.height; h = r.get('h') or r['w'] * im.height / im.width
            return dict(src='img/field/moss/' + r['file'], w=w, h=h)
    raise KeyError(asset)


HIDE = r'''()=>{document.querySelectorAll('.forest-ent').forEach(n=>{if(/^(rv_npc_|npc_slot_)/.test(n.dataset.asset||''))n.style.visibility='hidden'})}'''


def ruin_shot(b, base, spawn, items, path):
    """Returns (full screenshot with the real smoke/fire, x2 crop around the placed actors with the smoke layer hidden)."""
    pg = page(b, 'pc'); boot(pg, base)
    pg.evaluate('storyStage=15'); pg.evaluate(f"MossForestStory.enterMap('rilde_village','{spawn}')"); pg.wait_for_timeout(3200)
    pg.evaluate('closeDialogue()'); pg.evaluate(HIDE); pg.evaluate(INJECT, items); pg.wait_for_timeout(900)
    pg.screenshot(path=str(path))
    off = pg.evaluate("(()=>{const r=document.getElementById('forestWorld').getBoundingClientRect();return [r.left,r.top]})()")
    pg.evaluate("(()=>{const w=document.getElementById('forestWeather');if(w)w.style.visibility='hidden'})()"); pg.wait_for_timeout(300)
    clear = path.with_name(path.stem + '_clear.png'); pg.screenshot(path=str(clear)); pg.close()
    xs = [i['x'] for i in items]; ys = [i['y'] for i in items]
    cx = (min(xs) + max(xs)) / 2 + off[0]; cy = (min(ys) + max(ys)) / 2 - 30 + off[1]
    box = (int(cx - 180), int(cy - 120), int(cx + 180), int(cy + 120))
    zoom = Image.open(clear).convert('RGB').crop(box).resize((720, 480), Image.NEAREST)
    full = Image.open(path).convert('RGB').resize((720, 405))
    return full, zoom


MO, CH, G1 = (1105, 1150), (1160, 1145), (1040, 1125)   # ART-01 draft (1106,1181) stood on the fence line -> moved north of the fence
NG1, NG2 = (868, 252), (800, 236)   # ART-01 draft (930,360)/(999,372) sat inside the ruin fire FX -> moved onto the north path


def casting(b, base, gob):
    out = OUT / 'casting'; out.mkdir(parents=True, exist_ok=True)
    g = lambda k, x, y: dict(src=gob[k]['file'] and 'docs/art/candidates/art-02/' + gob[k]['file'], w=gob[k]['world'][0], h=gob[k]['world'][1], x=x, y=y)
    girl = art('rv_npc_girl'); cells = []
    for tag, asset, jp in (('A', 'rv_npc_young_woman', '母A＝若い女性 young_woman'), ('B', 'rv_npc_farmer_female', '母B＝農婦 farmer_female')):
        a = art(asset)
        items = [dict(a, x=MO[0], y=MO[1]), dict(girl, x=CH[0], y=CH[1]), g('goblin', G1[0], G1[1])]
        full, zoom = ruin_shot(b, base, 'from_barn', items, out / f'mother_{tag}.png')
        cells += [label(full, jp + '｜実表示（煙・炎あり）'), label(zoom, jp + '｜2倍・煙レイヤー非表示', f'母{MO}／子=girl{CH}／ゴブリン=派生プレビュー{G1}')]
    sheet(cells, 2, OUT / 'compare_mother.png', 'ART-02 襲撃後マップ｜母親の配役比較（stage15の村人NPCは非表示にして撮影）')
    cells = []
    for tag, asset, jp in (('A', 'npc_slot_soldier', '騎士A＝一般兵士 npc_soldier'), ('B', 'npc_slot_captain', '騎士B＝隊長 npc_captain')):
        a = art(asset)
        items = [dict(a, x=830, y=330), g('tainted_goblin', NG1[0], NG1[1]), g('tainted_goblin', NG2[0], NG2[1])]
        full, zoom = ruin_shot(b, base, 'from_moss_forest', items, out / f'knight_{tag}.png')
        cells += [label(full, jp + '｜実表示（煙・炎あり）'), label(zoom, jp + '｜2倍・煙レイヤー非表示', f'騎士(830,330)／異形=派生プレビュー{NG1}{NG2}')]
    sheet(cells, 2, OUT / 'compare_knight.png', 'ART-02 襲撃後マップ｜王国騎士の配役比較')
    # standalone reference strip (same world scale, x2)
    strip = Image.new('RGB', (980, 230), (52, 44, 38)); d = ImageDraw.Draw(strip); x = 10
    for nm, asset in (('young_woman', 'rv_npc_young_woman'), ('farmer_female', 'rv_npc_farmer_female'), ('soldier', 'npc_slot_soldier'),
                      ('captain', 'npc_slot_captain'), ('guard', 'npc_slot_guard'), ('girl', 'rv_npc_girl')):
        a = art(asset); im = Image.open(R / a['src']).convert('RGBA').resize((round(a['w'] * 2), round(a['h'] * 2)), Image.LANCZOS)
        strip.paste(im, (x, 200 - im.height), im); d.text((x, 205), nm, fill=(230, 220, 200), font=font(13)); x += max(im.width, 120) + 30
    ai = Image.open(R / 'img/field/characters/aidan/aidan_idle_down.png').convert('RGBA').crop((550, 126, 1380, 1230)); ai = ai.resize((round(ai.width * 69 * 2 / ai.height), 138), Image.LANCZOS)
    strip.paste(ai, (x, 200 - ai.height), ai); d.text((x, 205), 'Aidan(基準)', fill=(230, 220, 200), font=font(13))
    strip.save(OUT / 'casting_reference_scale.png')


# ---------------------------------------------------------------- sanctuary dead tree
def sanctum(b, base):
    out = OUT / 'sanctum'; out.mkdir(parents=True, exist_ok=True); thorn = art('veg_thorn_L_02'); cells = []
    for tag, jp in (('now', '現在：緑の矩形プレースホルダー'), ('reuse', '流用案：既存 veg_thorn_L_02 を割当')):
        pg = page(b, 'pc'); boot(pg, base); pg.evaluate('devJump("barrierAfter")'); pg.wait_for_timeout(4500); pg.evaluate('closeDialogue()')
        pg.evaluate("document.getElementById('forestWorld').style.transition='none'")
        if tag == 'reuse':
            pg.evaluate(r'''(t)=>{document.querySelectorAll('.forest-ent[data-asset="tree_dead_taint_M_01"]').forEach(n=>{const r=n.getBoundingClientRect();
              const im=document.createElement('img');im.src=t.src;const x=parseFloat(n.style.left)+parseFloat(n.style.width)/2,y=parseFloat(n.style.top)+parseFloat(n.style.height);
              Object.assign(im.style,{position:'absolute',left:(x-t.w/2)+'px',top:(y-t.h)+'px',width:t.w+'px',height:t.h+'px',zIndex:n.style.zIndex,pointerEvents:'none'});n.replaceWith(im);})}''', thorn)
        pg.wait_for_timeout(700); p = out / f'deadtree_{tag}.png'; pg.screenshot(path=str(p)); pg.close()
        im = Image.open(p).convert('RGB').crop((760, 60, 1280, 420)).resize((780, 540)); cells.append(label(im, jp))
    sheet(cells, 2, OUT / 'compare_deadtree.png', 'ART-02 A3聖域 tree_dead_taint_M_01（画面右上の一部）')


# ---------------------------------------------------------------- Lou intro / altar scenes
def scenes(b, base, gob):
    out = OUT / 'scenes'; out.mkdir(parents=True, exist_ok=True); cells = []
    lou = 'img/field/characters/lou/lou_idle_00.png'; seal = 'img/field/moss/art/a3_seal_opening.png'
    crops = {}
    for k, src in (('aidan', 'img/field/characters/aidan/aidan_idle_up.png'), ('fiona', 'img/field/moss/real/fiona/fiona_idle_up.png')):
        im = Image.open(R / src).convert('RGBA'); im = im.crop(im.getchannel('A').point(lambda v: 255 if v > 16 else 0).getbbox())
        name = f'derived/{k}_idle_up_trim_preview.png'; im.save(OUT / name); crops[k] = 'docs/art/candidates/art-02/' + name   # trimmed copy for the DOM box only
    aid, fio = crops['aidan'], crops['fiona']
    tg = 'docs/art/candidates/art-02/' + gob['tainted_goblin']['file']
    for v in ('pc', 'port'):
        for tag in ('now', 'swap'):
            pg = page(b, v); boot(pg, base); pg.evaluate('devJump("lou")'); pg.wait_for_timeout(4200)
            if tag == 'swap':
                pg.evaluate(r'''(a)=>{const L=document.getElementById('louIntroLou');L.textContent='';Object.assign(L.style,{background:'transparent',border:'0',boxShadow:'none',width:'44px',height:'72px'});
                  const i=new Image();i.src=a.lou;Object.assign(i.style,{width:'100%',height:'100%',objectFit:'contain',filter:'drop-shadow(0 0 12px #a9ffff)'});L.append(i);
                  const R=document.getElementById('louIntroRing');Object.assign(R.style,{border:'0',boxShadow:'none',background:'url('+a.seal+') center/contain no-repeat'});
                  document.getElementById('louIntroMoon').style.display='none';}''', dict(lou=lou, seal=seal))
            pg.wait_for_timeout(900); p = out / f'lou_{v}_{tag}.png'; pg.screenshot(path=str(p)); pg.close()
            pg = page(b, v); boot(pg, base); pg.evaluate('devJump("altar")'); pg.wait_for_timeout(5200)
            if tag == 'swap':
                pg.evaluate(r'''(a)=>{const put=(id,src,w,h,glow)=>{const e=document.getElementById(id);e.textContent='';Object.assign(e.style,{background:'transparent',border:'0',boxShadow:'none',borderRadius:'0',width:w+'px',height:h+'px'});
                    const i=new Image();i.src=src;Object.assign(i.style,{width:'100%',height:'100%',objectFit:'contain',filter:glow||''});e.append(i);};
                  put('altarAidan',a.aid,46,70);put('altarFiona',a.fio,46,68);put('altarLou',a.lou,34,56,'drop-shadow(0 0 10px #a9ffff)');
                  for(const id of ['ag1','ag2','ag3','ag4'])put(id,a.tg,64,66);
                  for(const id of ['ag1','ag3'])document.querySelector('#'+id+' img').style.transform='scaleX(-1)';}''', dict(aid=aid, fio=fio, lou=lou, tg=tg))
            pg.wait_for_timeout(1500); p = out / f'altar_{v}_{tag}.png'; pg.screenshot(path=str(p)); pg.close()
    for v, nm in (('pc', 'PC'), ('port', 'Android縦相当')):
        for sc, sj in (('lou', 'ルー登場（1行目）'), ('altar', '祭壇（1行目）')):
            for tag, jp in (('now', '現在'), ('swap', '既存PNG差し替え試作')):
                im = Image.open(out / f'{sc}_{v}_{tag}.png').convert('RGB'); im.thumbnail((620, 620))
                c = Image.new('RGB', (620, im.height + 30), (10, 14, 12)); c.paste(im, ((620 - im.width) // 2, 30)); cells.append(label(c, f'{nm}｜{sj}｜{jp}'))
    sheet(cells, 4, OUT / 'compare_lou_altar.png', 'ART-02 ルー登場・祭壇｜文字/丸/リングの仮表示 → 既存PNGでの置換試作（ブラウザ内のみ）')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--base', default='http://localhost:8765'); ap.add_argument('--only', nargs='*')
    a = ap.parse_args(); OUT.mkdir(parents=True, exist_ok=True)
    gob = derived(); (OUT / 'derived/derived.json').write_text(json.dumps(gob, indent=1) + '\n')
    want = set(a.only or ['house', 'casting', 'sanctum', 'scenes'])
    with sync_playwright() as p:
        b = p.chromium.launch()
        if 'house' in want: house(b, a.base)
        if 'casting' in want: casting(b, a.base, gob)
        if 'sanctum' in want: sanctum(b, a.base)
        if 'scenes' in want: scenes(b, a.base, gob)
        b.close()
    print('ok', OUT)


if __name__ == '__main__':
    main()
