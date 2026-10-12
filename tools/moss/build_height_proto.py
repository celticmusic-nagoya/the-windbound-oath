#!/usr/bin/env python3
"""Builds data/maps/dev_height_proto.json - the DEV-only height-level prototype map (Phase 1). Deterministic.
Base schema is copied from dev_monster_arena.json; nothing else under data/maps is touched.

Layout (world 2400x1600, collision "feet basis", level height H=56):
  river (water, level-0 blocker) y 600..720 across the map
  bridge deck  level 1  x 1500..1620, y 480..1120 over the river AND over the south bank (a walkable path under it at level 0)
  bridge ramps north [1500,360,120,120]  south [1500,1120,120,120]
  plateau      level 1  x 1750..2250, y 120..420 (cliff front at y 420; level-0 actors cannot enter or stand behind it)
  stairs       south face [1900,420,120,120]      slope (west)  [1630,220,120,100]
  foreground tree at (2100, 470) whose canopy covers the plateau's front edge
"""
import json, os
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
H = 56
base = json.load(open(os.path.join(ROOT, 'data/maps/dev_monster_arena.json')))
W, HT = 2400, 1600
m = json.loads(json.dumps(base))
m['id'] = 'dev_height_proto'
m['displayName'] = {'ja': 'DEV　高さプロトタイプ', 'en': 'DEV Height Prototype'}
m['locationCard'] = {'regionJa': '開発用', 'regionEn': 'DEV', 'areaJa': '高さプロトタイプ', 'areaEn': 'DEV Height Prototype', 'triggerZone': 'ev_arrival'}
m['world'] = {'width': float(W), 'height': float(HT), 'tile': 8, 'unitScale': 2.5}
m['spawns'] = {'default': 'start', 'points': {
    'start': {'x': 300, 'y': 1250, 'facing': 'right'},
    'deck': {'x': 1560, 'y': 600, 'facing': 'down'},
    'plateau': {'x': 2000, 'y': 250, 'facing': 'down'},
    'under': {'x': 1560, 'y': 900, 'facing': 'right'}}}
m['eventZones'] = [{'id': 'ev_arrival', 'type': 'locationCard', 'shape': {'shape': 'rect', 'x': 150, 'y': 1100, 'w': 300, 'h': 300}, 'once': True}]
m['terrain']['baseColor'] = '#7d9a58'
m['story'] = {'placeholder': True, 'note': 'Phase 1 高さプロトタイプ専用(DEV)。本編のマップ・進行には接続しない'}
m['ambience']['grade']['tintStrength'] = 0.0
m['collision'] = {'bounds': {'x': 0, 'y': 0, 'w': float(W), 'h': float(HT)},
    'edgeBlockers': [{'shape': 'rect', 'x': 0, 'y': 0, 'w': W, 'h': 48}, {'shape': 'rect', 'x': 0, 'y': HT - 48, 'w': W, 'h': 48},
                     {'shape': 'rect', 'x': 0, 'y': 0, 'w': 48, 'h': HT}, {'shape': 'rect', 'x': W - 48, 'y': 0, 'w': 48, 'h': HT}],
    'blockers': [
        {'id': 'cb_river', 'tag': 'water_deep', 'shape': 'rect', 'x': 0, 'y': 600, 'w': W, 'h': 120, 'levels': [0]},
        {'id': 'cb_plateau_cliff', 'tag': 'cliff', 'shape': 'rect', 'x': 1750, 'y': 120 - H, 'w': 500, 'h': 300 + H, 'levels': [0]},
        {'id': 'cb_pier_w', 'tag': 'prop', 'shape': 'rect', 'x': 1500, 'y': 940, 'w': 16, 'h': 20, 'levels': [0]},
        {'id': 'cb_pier_e', 'tag': 'prop', 'shape': 'rect', 'x': 1604, 'y': 940, 'w': 16, 'h': 20, 'levels': [0]},
        {'id': 'cb_tree', 'tag': 'prop', 'shape': 'rect', 'x': 2090, 'y': 458, 'w': 20, 'h': 14}]}

DECK_Z = 440  # below an actor that has just stepped onto the deck (north ramp hi zone starts at y~454)
height = {
    'levelHeight': H,
    'levels': {'1': {'walk': [[1500, 480, 120, 640], [1750, 120, 500, 300]]}},
    'connectors': [
        {'id': 'ramp_bridge_n', 'rect': [1500, 360, 120, 120], 'axis': 'y', 'fromEnd': 'min', 'from': 0, 'to': 1, 'zone': .22},
        {'id': 'ramp_bridge_s', 'rect': [1500, 1120, 120, 120], 'axis': 'y', 'fromEnd': 'max', 'from': 0, 'to': 1, 'zone': .22},
        {'id': 'stairs_plateau', 'rect': [1900, 420, 120, 120], 'axis': 'y', 'fromEnd': 'max', 'from': 0, 'to': 1, 'zone': .22},
        {'id': 'slope_plateau_w', 'rect': [1630, 220, 120, 100], 'axis': 'x', 'fromEnd': 'min', 'from': 0, 'to': 1, 'zone': .22}],
    'overpasses': [{'id': 'bridge_deck', 'level': 1, 'rect': [1500, 480, 120, 640], 'z': DECK_Z, 'fade': 'deck'}],
}
V = []
def rect(i, r, color, z, **kw): V.append({'id': i, 'kind': 'rect', 'rect': r, 'color': color, 'z': z, **kw})
def poly(i, pts, color, z, **kw): V.append({'id': i, 'kind': 'poly', 'pts': pts, 'color': color, 'z': z, **kw})
# ground-class floors (z below every sprite)
rect('river', [0, 600, W, 120], '#4d86bd', 1, label='川 (level 0 通行不可)')
rect('lbl_low', [200, 1150, 260, 40], 'rgba(0,0,0,0)', 4, label='低地 level 0')
rect('plateau_top', [1750, 120 - H, 500, 300], '#9fbf6a', 5)
rect('lbl_plateau', [1900, 120 - H + 20, 200, 30], 'rgba(0,0,0,0)', 7, label='高台 level 1')
poly('slope_w', [[1630, 220], [1750, 220 - H], [1750, 320 - H], [1630, 320]], '#d8b87a', 6, label='坂')
poly('stairs_s', [[1900, 420 - H], [2020, 420 - H], [2020, 540], [1900, 540]], '#b9b2a0', 7, stripes=0)
poly('ramp_n', [[1500, 360], [1620, 360], [1620, 480 - H], [1500, 480 - H]], '#d8b87a', 6)
poly('ramp_s', [[1500, 1120 - H], [1620, 1120 - H], [1620, 1240], [1500, 1240]], '#d8b87a', 6)
rect('under_path', [1380, 780, 360, 90], '#8a7650', 3, label='橋の下 level 0', opacity=.8)
# cliff face (sprite class: foot y = 420)
rect('cliff_face', [1750, 420 - H, 500, H], '#6b5740', 420)
# bridge deck: floor + rails split in 80px segments so each has its own foot y
rect('deck_floor', [1500, 480 - H, 120, 640], '#c8955a', DECK_Z, fade='deck', stripes=90, label='橋 level 1')
y = 480
while y < 1120:
    b = min(y + 80, 1120)
    for side, x in (('w', 1500), ('e', 1610)):
        rect('rail_%s_%d' % (side, y), [x, y - H - 22, 10, (b - y) + 22], '#7a4f27', b, fade='deck')
    y = b
rect('pier_w', [1500, 940 - H, 16, 56 + 20], '#6d6a62', 960, fade='deck')
rect('pier_e', [1604, 940 - H, 16, 56 + 20], '#6d6a62', 960, fade='deck')
# foreground tree: trunk + canopy, foot y 470, covers the plateau's front edge
rect('tree_trunk', [2092, 420, 16, 52], '#5b3b1d', 470)
rect('tree_canopy', [2030, 320, 140, 120], '#2f7a35', 470, round='50%')
m['height'] = {**height, 'visuals': V}
out = os.path.join(ROOT, 'data/maps/dev_height_proto.json')
json.dump(m, open(out, 'w'), ensure_ascii=False, indent=1)
print('wrote', out, len(V), 'visuals')
