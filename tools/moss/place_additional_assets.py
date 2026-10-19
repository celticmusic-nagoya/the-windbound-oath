#!/usr/bin/env python3
"""Deterministic, idempotent placement of the 2026-10-19 moss additional assets into the runtime maps (data/maps/moss_forest_0{1,2,3}_*.json).
Only ADDS: props tagged 'add20261019' and decor blockers 'cb_add_*' (scatterIgnore). Existing props/blockers/events/scatter are untouched.
Keeps clear of: spawns, transitions, event zones, treasure points, story symbols, monsters, path corridors (tall sprites), water, cliff bands, existing solids,
existing props and the (deterministic) scatter nodes. Re-running first removes its own previous output.
usage: place_additional_assets.py [--dry]"""
import json, math, random, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; TAG = 'add20261019'
REP = json.load(open(ROOT / 'docs/art/delivered/moss_additional_20261019/quality/report.json'))
MAN = json.load(open(ROOT / 'img/field/moss/manifest.json'))
def size(i): w, h = REP[i]['world_px']; return w, h
# asset -> (blocks, footprint half-width factor)
BLOCK = {'bush_forest_01': .34, 'bush_forest_02': .34, 'bush_forest_03': .34, 'rock_moss_01': .36, 'rock_moss_02': .36, 'rock_moss_03': .36,
         'stump_rot_01': .34, 'stump_rot_02': .34, 'ruins_stone_01': .33, 'ruins_stone_02': .33}
PLAN = {
 'moss_forest_01_sunlit_path': {'fern_cluster_01': 6, 'fern_cluster_02': 4, 'fern_cluster_03': 4, 'bush_forest_01': 4, 'bush_forest_02': 3, 'bush_forest_03': 3,
                                 'mushroom_cluster_01': 4, 'mushroom_cluster_02': 4, 'rock_moss_01': 3, 'rock_moss_03': 3},
 'moss_forest_02_mossy_ravine': {'rock_moss_01': 4, 'rock_moss_02': 3, 'rock_moss_03': 3, 'root_exposed_01': 3, 'root_exposed_02': 3, 'stump_rot_01': 3, 'stump_rot_02': 3,
                                  'fern_cluster_01': 3, 'fern_cluster_02': 3, 'fern_cluster_03': 2, 'mushroom_cluster_01': 2, 'mushroom_cluster_02': 2},
 'moss_forest_03_ancient_grove': {'ruins_stone_01': 4, 'ruins_stone_02': 4, 'stump_rot_01': 1, 'stump_rot_02': 1, 'mushroom_cluster_01': 2, 'mushroom_cluster_02': 2,
                                   'fern_cluster_01': 2, 'fern_cluster_02': 2, 'fern_cluster_03': 2, 'root_exposed_01': 2},
}
def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; l2 = dx * dx + dy * dy; t = 0 if not l2 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2)); return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
def line_dist(p, pts): return min(seg_dist(p, pts[i], pts[i + 1]) for i in range(len(pts) - 1))
def in_poly(p, poly):
    c = False; j = len(poly) - 1
    for i in range(len(poly)):
        a, b = poly[i], poly[j]
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]: c = not c
        j = i
    return c
def rect_hit(r1, r2, m=0): return not (r1[0] + r1[2] + m <= r2[0] or r2[0] + r2[2] + m <= r1[0] or r1[1] + r1[3] + m <= r2[1] or r2[1] + r2[3] + m <= r1[1])
def node_size(asset):
    for r in MAN['node']:
        if re.search(r['match'], asset) and r.get('file'): return r['w'], r['h']
    return 90, 90
def collect(m, scat):
    pts = []   # (x, y, radius) protected points
    rects = []  # protected rects
    for s in m['spawns']['points'].values(): pts.append((s['x'], s['y'], 150))
    for t in m['transitions']:
        r = t['rect']; rects.append([r['x'] - 120, r['y'] - 120, r['w'] + 240, r['h'] + 240])
    for e in m['eventZones']:
        sh = e.get('shape')
        if not sh: continue
        if 'cx' in sh: pts.append((sh['cx'], sh['cy'], sh['r'] + 120))
        elif 'x' in sh: rects.append([sh['x'] - 120, sh['y'] - 120, sh['w'] + 240, sh['h'] + 240])
    for t in m.get('treasurePoints', []): pts.append((t['x'], t['y'], 170))
    for mo in m.get('monsters', []): pts.append((mo['x'], mo['y'], 110))
    def walk(o):
        if isinstance(o, dict):
            if 'x' in o and 'y' in o and isinstance(o['x'], (int, float)) and ('hp' in o or 'interactRadius' in o): pts.append((o['x'], o['y'], 230))
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(m.get('story', {}))
    for c in m.get('cameraFocus', []): pass
    solids = []
    for b in m['collision']['blockers']:
        if b['id'].startswith('cb_add_'): continue
        for r in b['rects']: solids.append(r)
    for b in m['collision'].get('edgeBlockers', []):
        for r in ([[b['x'], b['y'], b['w'], b['h']]] if b['shape'] == 'rect' else b['rects']): solids.append(r)
    obst = []
    for p in m['props']:
        if TAG in p.get('tags', []): continue
        w, h = node_size(p['asset']); obst.append((p['x'], p['y'], w, h))
    for e in scat:
        if e['r'] == 'node':
            w, h = node_size(e['a']); obst.append((e['x'], e['y'], w, h))
    for rr in (m['collision'].get('carves') or []): rects.append([rr['x'] - 40, rr['y'] - 40, rr['w'] + 80, rr['h'] + 80])
    return pts, rects, solids, obst
def bands(m):
    out = []
    for c in m['terrain'].get('cliffs') or []:
        for s in c['segments']: out.append([s[0] - 40, s[1] - 260, s[2] + 80, s[3] + 260 + 120])   # face + lip + margin (sprites also extend upward from the feet)
    return out
def place(mapid):
    f = ROOT / 'data/maps' / (mapid + '.json'); m = json.load(open(f))
    m['props'] = [p for p in m['props'] if TAG not in p.get('tags', [])]
    m['collision']['blockers'] = [b for b in m['collision']['blockers'] if not b['id'].startswith('cb_add_')]
    import tempfile; tmp = Path(tempfile.gettempdir()) / '_moss_scat_in.json'; json.dump(m, open(tmp, 'w'))
    scat = json.loads(subprocess.check_output(['node', str(ROOT / 'tools/moss/scatter_dump.js'), str(tmp)]))
    pts, rects, solids, obst = collect(m, scat); cl = bands(m); W, H = m['world']['width'], m['world']['height']
    paths = m['terrain']['paths']; waters = m['terrain']['waters']
    rnd = random.Random(sum(map(ord, mapid))); placed = []; n = 0; report = {}
    order = sorted(PLAN[mapid].items(), key=lambda kv: -size(kv[0])[0] * size(kv[0])[1])   # big first
    for asset, cnt in order:
        w, h = size(asset); got = 0; tries = 0; blocks = asset in BLOCK; fw = BLOCK.get(asset, 0)
        tall = h > 70
        while got < cnt and tries < 60000:
            tries += 1
            x = round(rnd.uniform(260, W - 260), 1); y = round(rnd.uniform(h + 120, H - 200), 1)
            spr = [x - w / 2, y - h, w, h]; foot = [x - w * (fw or .3), y - 16, w * 2 * (fw or .3), 16]
            if any(math.hypot(x - px, y - py) < rad + w * .5 for px, py, rad in pts): continue
            if any(rect_hit(spr, r) for r in rects): continue
            if any(rect_hit(foot, [s[0], s[1], s[2], s[3]], 24) for s in solids): continue
            if any(rect_hit(spr, [b[0], b[1], b[2], b[3]]) for b in cl): continue
            if any((line_dist((x, y), p['points']) < p['width'] / 2 + (w * .5 + 40 if tall else w * .25 + 12)) for p in paths): continue
            bad = False
            for wt in waters:
                if wt.get('points') and line_dist((x, y), wt['points']) < (wt.get('width') or 0) / 2 + w * .5 + 40: bad = True
                if wt.get('polygon') and (in_poly((x, y), wt['polygon']) or any(math.hypot(x - q[0], y - q[1]) < w * .5 + 60 for q in wt['polygon'])): bad = True
            if bad: continue
            if any(abs(x - ox) < (w + ow) * .42 and abs(y - oy) < max(26, min(h, oh) * .35) for ox, oy, ow, oh in obst): continue
            if any(abs(x - px) < (w + pw) * .55 and abs(y - py) < max(30, min(h, ph) * .4) for px, py, pw, ph, _ in placed): continue
            placed.append((x, y, w, h, asset)); got += 1
        report[asset] = got
        assert got == cnt, (mapid, asset, got, cnt)
    for x, y, w, h, asset in sorted(placed, key=lambda t: (t[1], t[0])):
        n += 1; pid = 'p_add_%02d_%s' % (n, asset.replace('_', '')[:14])
        prop = {'id': pid, 'asset': asset, 'x': x, 'y': y, 'tags': ['decor', TAG], 'flip': rnd.random() < .5}
        if asset in BLOCK:
            fw = BLOCK[asset]; fh = min(14, h * .11); hw = w * fw
            m['collision']['blockers'].append({'id': 'cb_add_' + pid, 'tag': 'decor', 'shape': 'rects', 'rects': [[round(x - hw, 1), round(y - fh, 1), round(hw * 2, 1), round(fh, 1)]], 'scatterIgnore': True})
            prop['noCollision'] = True
        else: prop['noCollision'] = True
        m['props'].append(prop)
    if '--dry' not in sys.argv: json.dump(m, open(f, 'w'), ensure_ascii=False, separators=(',', ':'))
    return report, len(placed)
if __name__ == '__main__':
    for mid in PLAN: print(mid, place(mid))
