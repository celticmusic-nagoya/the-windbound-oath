#!/usr/bin/env python3
"""DIRECTIVE-ART-04 previews: the real game on a local server with ART-04 candidates swapped in *inside the browser only*
(same mechanism as preview_art02.py; repository files are untouched).
  house   : rilde_in_aidan with ART-04 tiles + the 4 remade furniture (bed / cupboard / fireplace / window), vs current and vs ART-01.
  soldier : the soldier candidate next to the current soldier, a villager and Aidan, in the peaceful village and on the ruin map.
Output: docs/art/candidates/art-04/compare_*.png (raw captures under preview/, not committed).
"""
import argparse, json, pathlib
from PIL import Image
from playwright.sync_api import sync_playwright
import preview_art02 as P

R = P.R; OUT = R / 'docs/art/candidates/art-04'; RAW = OUT / 'preview'
C4 = 'docs/art/candidates/art-04/'
TEX4 = {k: C4 + f'art04_{k}.png' for k in ('int_floor_planks_01', 'int_wall_timber_01', 'int_baseboard_01', 'int_wallcap_left_01', 'int_wallcap_right_01',
                                           'int_wallcap_bottom_01', 'int_wallcap_corner_sw_01', 'int_wallcap_corner_se_01', 'int_doorway_01')}
FURN4 = {'^furn_bed$': 'art04_furn_bed_01.png', '^furn_cupboard$': 'art04_furn_cupboard_01.png',
         '^furn_fireplace$': 'art04_furn_fireplace_01.png', '^furn_window_wall$': 'art04_furn_window_wall_01.png'}


def routes4(base):
    def layer(route):
        body = route.fetch().text(); assert P.PATCH_FIND in body
        route.fulfill(body=body.replace(P.PATCH_FIND, P.PATCH_FIND + P.PATCH_ADD), content_type='application/javascript')

    def mapjson(route):
        d = json.loads(route.fetch().text()); dark = '#17110d'
        d['terrain']['fills'] = [
            {'id': 'fill_0', 'color': dark, 'rects': [[0, 0, 960, 720]]},
            {'id': 'wall', 'color': '#76654f', 'texture': 'int_wall_timber_01', 'rects': [[48, 48, 864, 150]]},
            {'id': 'floor', 'color': '#a98b5c', 'texture': 'int_floor_planks_01', 'rects': [[48, 198, 864, 474]]},
            {'id': 'base', 'color': '#3a2c20', 'texture': 'int_baseboard_01', 'rects': [[48, 188, 864, 12]]},
            {'id': 'capL', 'color': dark, 'texture': 'int_wallcap_left_01', 'rects': [[0, 0, 48, 672]]},
            {'id': 'capR', 'color': dark, 'texture': 'int_wallcap_right_01', 'rects': [[912, 0, 48, 672]]},
            {'id': 'capB', 'color': dark, 'texture': 'int_wallcap_bottom_01', 'rects': [[48, 672, 864, 48]]},
            {'id': 'capSW', 'color': dark, 'texture': 'int_wallcap_corner_sw_01', 'rects': [[0, 672, 48, 48]]},
            {'id': 'capSE', 'color': dark, 'texture': 'int_wallcap_corner_se_01', 'rects': [[912, 672, 48, 48]]},
            {'id': 'door', 'color': dark, 'texture': 'int_doorway_01', 'rects': [[410, 672, 140, 48]]}]
        route.fulfill(body=json.dumps(d, ensure_ascii=False), content_type='application/json')

    def manifest(route):
        m = json.loads(route.fetch().text())
        for r in m['node']:
            if r['match'] in FURN4: r['file'] = '../../../' + C4 + FURN4[r['match']]
        route.fulfill(body=json.dumps(m), content_type='application/json')

    init = 'window.__ART02_TEX={};' + ''.join(f"(()=>{{const i=new Image();i.src='{base}/{p}';window.__ART02_TEX['{k}']=i}})();" for k, p in TEX4.items())
    return {'**/js/field/forest-layer.js*': layer, '**/data/maps/rilde_in_aidan.json*': mapjson, '**/img/field/moss/manifest.json*': manifest}, init


def shoot_house(b, base, v, tag):
    if tag == 'art04': routes, init = routes4(base)
    elif tag == 'art01': routes, init = P.house_routes(base)
    else: routes, init = {}, None
    pg = P.page(b, v, routes, init); P.boot(pg, base)
    pg.evaluate('RildeVillage.startOpening()'); pg.wait_for_timeout(2600); pg.evaluate('closeDialogue()'); pg.wait_for_timeout(1300)
    p = RAW / f'house_{v}_{tag}.png'; pg.screenshot(path=str(p)); pg.close(); return p


def house(b, base):
    files = {(v, t): shoot_house(b, base, v, t) for v in P.VP for t in ('now', 'art01', 'art04')}
    cells = []
    for v, nm in (('pc', 'PC 1280×720'), ('land', 'Android横相当 915×412'), ('port', 'Android縦相当 412×915')):
        for t, jp in (('now', '現在'), ('art01', 'ART-01候補'), ('art04', 'ART-04試作')):
            im = Image.open(files[(v, t)]).convert('RGB'); im.thumbnail((620, 620))
            c = Image.new('RGB', (620, im.height + 30), (10, 14, 12)); c.paste(im, ((620 - im.width) // 2, 30)); cells.append(P.label(c, f'{nm}｜{jp}'))
    P.sheet(cells, 3, OUT / 'compare_house_art04.png', 'ART-04B エイダンの自宅｜現在 / ART-01 / ART-04（実ゲーム描画・ブラウザ内差し替え）')
    # 2x detail crops from the PC capture (room is centred: world x = screen x - 160)
    zc = []
    for nm, box in (('暖炉・本棚まわり', (160 + 560, 60, 160 + 900, 300)), ('ベッド・タンス・窓', (160 + 70, 60, 160 + 450, 330)), ('入口', (160 + 330, 520, 160 + 630, 720))):
        for t, jp in (('now', '現在'), ('art04', 'ART-04')):
            im = Image.open(files[('pc', t)]).convert('RGB').crop(box); im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
            c = Image.new('RGB', (im.width, im.height + 30), (10, 14, 12)); c.paste(im, (0, 30)); zc.append(P.label(c, f'{nm} 2倍｜{jp}'))
    P.sheet(zc, 2, OUT / 'compare_house_art04_detail.png', 'ART-04B 自宅の細部（PC表示を2倍・ニアレスト拡大）')


def soldier(b, base):
    new = dict(src=C4 + 'art04_npc_soldier_front_idle_01.png', w=56, h=84)
    old = P.art('npc_slot_soldier'); vill = P.art('rv_npc_young_woman'); elder = P.art('rv_npc_elder_man')
    cells = []
    for v in ('pc', 'port'):
        for mapname, spawn, stage, pts in (('peace', 'from_inn', 1, [(1035, 600), (915, 600), (1095, 600), (855, 600)]),
                                           ('ruin', 'from_moss_forest', 15, [(830, 330), (770, 330), (890, 330), (710, 330)])):
            pg = P.page(b, v); P.boot(pg, base)
            pg.evaluate(f'storyStage={stage}'); pg.evaluate(f"MossForestStory.enterMap('rilde_village','{spawn}')"); pg.wait_for_timeout(3300)
            pg.evaluate('closeDialogue()'); pg.evaluate(P.HIDE)
            items = [dict(new, x=pts[0][0], y=pts[0][1]), dict(old, x=pts[1][0], y=pts[1][1]), dict(vill, x=pts[2][0], y=pts[2][1]), dict(elder, x=pts[3][0], y=pts[3][1])]
            pg.evaluate(P.INJECT, items); pg.wait_for_timeout(900)
            off = pg.evaluate("(()=>{const r=document.getElementById('forestWorld').getBoundingClientRect();return [r.left,r.top]})()")
            pg.evaluate("(()=>{const w=document.getElementById('forestWeather');if(w)w.style.visibility='hidden'})()"); pg.wait_for_timeout(300)
            p = RAW / f'soldier_{mapname}_{v}.png'; pg.screenshot(path=str(p)); pg.close()
            im = Image.open(p).convert('RGB')
            cx = pts[0][0] + off[0] - 60; cy = pts[0][1] + off[1] - 50
            crop = im.crop((int(cx - 220), int(cy - 110), int(cx + 220), int(cy + 90))).resize((880, 400), Image.NEAREST)
            c = Image.new('RGB', (880, 430), (10, 14, 12)); c.paste(crop, (0, 30))
            cells.append(P.label(c, f'{"平和村" if mapname == "peace" else "襲撃後(北側)"}｜{"PC" if v == "pc" else "Android縦相当"}｜2倍', '左から 老人(既存)・旧兵士・新兵士(試作)・若い女性(既存)／中央付近にエイダン'))
    P.sheet(cells, 2, OUT / 'compare_soldier_art04.png', 'ART-04C 一般兵士 正面idle｜既存NPC・エイダンと同じ画面（煙レイヤーのみ非表示）')
    # standalone scale strip, 3x nearest
    strip = Image.new('RGBA', (5 * 140, 200), (62, 74, 56, 255))
    ai = Image.open(R / 'img/field/characters/aidan/aidan_idle_down.png').convert('RGBA').crop((550, 126, 1380, 1230)); ai = ai.resize((round(ai.width * 138 / ai.height), 138), Image.LANCZOS)
    for i, im in enumerate([Image.open(R / old['src']).convert('RGBA'), Image.open(R / new['src']).convert('RGBA'),
                            Image.open(R / vill['src']).convert('RGBA').resize((round(vill['w'] * 2), round(vill['h'] * 2)), Image.LANCZOS),
                            Image.open(R / elder['src']).convert('RGBA').resize((round(elder['w'] * 2), round(elder['h'] * 2)), Image.LANCZOS), ai]):
        strip.alpha_composite(im, (i * 140 + (140 - im.width) // 2, 190 - im.height))
    strip = strip.resize((strip.width * 2, strip.height * 2), Image.NEAREST).convert('RGB')
    P.label(strip, '同一world縮尺（@2x→さらに2倍）: 旧兵士 / 新兵士 / 若い女性 / 老人 / エイダン').save(OUT / 'compare_soldier_scale.png')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--base', default='http://localhost:8765'); ap.add_argument('--only', nargs='*'); a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True); want = set(a.only or ['house', 'soldier'])
    with sync_playwright() as p:
        b = p.chromium.launch()
        if 'house' in want: house(b, a.base)
        if 'soldier' in want: soldier(b, a.base)
        b.close()
    print('ok')


if __name__ == '__main__':
    main()
