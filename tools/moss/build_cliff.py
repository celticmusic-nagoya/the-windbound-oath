#!/usr/bin/env python3
"""Generate data/maps/cliff_moher_01_spiral_ascent.json (schema v2, same runtime format as the Moss Forest maps).

A coastal headland seen from above: the path enters from the west (Rilde Village), winds ~265 degrees
counter-clockwise up a green knoll (south -> east -> north), climbs a ramp through the rock wall and ends on the
summit meadow whose north lip overlooks the sea. Everything non-walkable is derived from ONE mask, so collision and
art can never disagree:   walkable = path corridor U summit meadow.   Blocked cells are painted as
  face    cliff rock wall (a walkable cell lies just above)      slope  green hillside / knoll
  foam / shallow / deep   sea bands by distance from the shore.
usage: python3 tools/moss/build_cliff.py            (writes the map JSON, prints a validation report)"""
import json, math, os, sys
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'data', 'maps', 'cliff_moher_01_spiral_ascent.json')
W, H, G = 4800, 4800, 8       # G = mask cell (collision/art are derived from this mask)
COLS, ROWS = W // G, H // G
C = (2400.0, 3450.0)           # knoll centre
HALF = 130.0                   # corridor half width (walkable 260 px)
ENTRY_Y = C[1] + 1200 * math.sin(math.radians(170))

PX0, PX1, PY1 = 780.0, 4080.0, 2300.0
# ---------- path: lead-in + counter-clockwise spiral + ramp north --------------------------------------------
def spiral(n=72):
    pts = []
    for i in range(n + 1):
        t = i / n
        th = math.radians(170 - 265 * t)           # 170 deg (west) -> -95 deg (north)
        r = 1200 - 380 * t
        pts.append((C[0] + r * math.cos(th), C[1] + r * math.sin(th)))
    return pts
SP = spiral()
START, END = SP[0], SP[-1]
LEAD = [(0.0, ENTRY_Y), (START[0] * .5, ENTRY_Y + (START[1] - ENTRY_Y) * .0), START]
RAMP = [END, (END[0], PY1 - 120.0), (END[0], PY1 - 420.0)]
PATH_PTS = [list(map(lambda v: round(v, 1), p)) for p in LEAD[:-1] + SP + RAMP[1:]]

def seg_dist(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = max(0, min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / l2)) if l2 else 0
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)
def line_dist(px, py, pts):
    return min(seg_dist(px, py, pts[i], pts[i + 1]) for i in range(len(pts) - 1))

# ---------- summit meadow --------------------------------------------------------------------------------------
def edge(x):   # north coastline (lip) y
    return 880 + 55 * math.sin(x / 260.0) + 38 * math.sin(x / 97.0 + 1.0)
def in_plateau(x, y): return PX0 <= x <= PX1 and edge(x) + 24 <= y <= PY1

# ---------- mask (vectorised) -----------------------------------------------------------------------------------
cx = (np.arange(COLS) + .5) * G
cy = (np.arange(ROWS) + .5) * G
X, Y = np.meshgrid(cx, cy)
def seg_dist_v(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; l2 = dx * dx + dy * dy
    tt = np.clip(((X - a[0]) * dx + (Y - a[1]) * dy) / l2, 0, 1) if l2 else 0
    return np.hypot(X - a[0] - tt * dx, Y - a[1] - tt * dy)
dpath = np.full((ROWS, COLS), 1e9)
for k in range(len(PATH_PTS) - 1): dpath = np.minimum(dpath, seg_dist_v(PATH_PTS[k], PATH_PTS[k + 1]))
EDGE = np.vectorize(edge)(cx)[None, :]
plateau = (X >= PX0) & (X <= PX1) & (Y >= EDGE + 24) & (Y <= PY1)
walk = (dpath <= HALF) | plateau
dist_c = np.hypot(X - C[0], Y - C[1])

def chamfer(src):
    d = np.where(src, 0.0, 1e9)
    for _ in range(40):
        n = d.copy()
        for dj, di, c in [(-1, 0, G), (1, 0, G), (0, -1, G), (0, 1, G), (-1, -1, G * 1.4), (-1, 1, G * 1.4), (1, -1, G * 1.4), (1, 1, G * 1.4)]:
            sh = np.full_like(d, 1e9)
            js = slice(max(dj, 0), ROWS + min(dj, 0)); jd = slice(max(-dj, 0), ROWS + min(-dj, 0))
            is_ = slice(max(di, 0), COLS + min(di, 0)); id_ = slice(max(-di, 0), COLS + min(-di, 0))
            sh[jd, id_] = d[js, is_] + c
            n = np.minimum(n, sh)
        if (n == d).all(): break
        d = n
    return d

# classes of the blocked cells
above = np.zeros_like(walk)
for k in range(1, 96 // G + 1):   # a walkable cell within ~96 px straight above -> visible rock face
    sh = np.zeros_like(walk); sh[k:, :] = walk[:-k, :]; above |= sh
klass = np.full((ROWS, COLS), '', dtype=object)
slope = (dpath <= 260) | (dist_c < 1480) | ((X < 1050) & (Y > 2350) & (Y < 3350))   # + far lowland where the village is seen
land = walk | (~walk & slope & ~above)
try:
    from scipy.ndimage import distance_transform_edt
    d2land = distance_transform_edt(~land) * G           # exact Euclidean (scipy present)
except ImportError:
    d2land = chamfer(land)                               # fallback: octagonal metric, slightly stepped bands
d2land = d2land + 16 * np.sin(X / 83.0) * np.cos(Y / 61.0) + 9 * np.sin(X / 37.0 + Y / 53.0)   # organic shoreline
for cls, m in (('deep', d2land > 288), ('shallow', d2land <= 288), ('foam', d2land <= 80), ('slope', slope), ('face', above)):
    klass[~walk & m] = cls            # later entries win
klass[walk] = ''

def rects_of(mask):
    """greedy rectangles: horizontal runs, merged with identical runs on the next row"""
    open_, out = {}, []
    for j in range(ROWS + 1):
        runs = []
        if j < ROWS:
            i = 0
            while i < COLS:
                if mask[j, i]:
                    k = i
                    while k < COLS and mask[j, k]: k += 1
                    runs.append((i, k)); i = k
                else: i += 1
        nxt = {}
        for r in runs:
            if r in open_: nxt[r] = open_.pop(r)
            else: nxt[r] = [j, j]
            nxt[r][1] = j
        for r, (j0, j1) in open_.items(): out.append([r[0] * G, j0 * G, (r[1] - r[0]) * G, (j1 - j0 + 1) * G])
        open_ = nxt
    return out

blocked = ~walk
# the west edge stays open at the lead-in (transition), everything else is blocked by the mask
rects_block = rects_of(blocked)
fills = []
for name, color in [('sea_deep', '#2f6f9f'), ('sea_shallow', '#4f9bd0'), ('sea_foam', '#a9d8ec'), ('hill_slope', '#3d6b2e')]:
    key = {'sea_deep': 'deep', 'sea_shallow': 'shallow', 'sea_foam': 'foam', 'hill_slope': 'slope'}[name]
    f = {'id': name, 'color': color, 'rects': rects_of(klass == key)}
    if key == 'slope': f['alpha'] = 0.62                      # the grass texture shows through
    if key in ('deep', 'shallow'): f['waves'] = True
    fills.append(f)
face_rects = rects_of(klass == 'face')

# ---------- patches (scatter regions): strips along the corridor + the meadow ----------------------------------
def strip(pts, hw):
    left, right = [], []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; l = math.hypot(dx, dy) or 1
        nx, ny = -dy / l, dx / l
        left.append([round(p[0] + nx * hw, 1), round(p[1] + ny * hw, 1)]); right.append([round(p[0] - nx * hw, 1), round(p[1] - ny * hw, 1)])
    return left + right[::-1]
patches = []
seg = 9
for k in range(seg):
    a, b = k * (len(SP) - 1) // seg, (k + 1) * (len(SP) - 1) // seg
    patches.append({'id': 'patch_slope_%d' % k, 'texture': 'gnd_grass_sunny', 'tint': '#E8F2B8', 'surface': 'grass', 'feather': 40, 'polygon': strip(SP[a:b + 1], HALF - 14)})
meadow = [[PX0 + 20, edge(PX0 + 20) + 50]] + [[x, edge(x) + 50] for x in range(int(PX0) + 120, int(PX1), 160)] + [[PX1 - 20, edge(PX1 - 20) + 50], [PX1 - 20, PY1 - 30], [PX0 + 20, PY1 - 30]]
patches.append({'id': 'patch_meadow_summit', 'texture': 'gnd_grass_sunny', 'tint': '#F4F7C8', 'surface': 'grass', 'feather': 48, 'polygon': [[round(a, 1), round(b, 1)] for a, b in meadow]})
patches.append({'id': 'patch_lead_in', 'texture': 'gnd_grass_sunny', 'tint': '#E8F2B8', 'surface': 'grass', 'feather': 40, 'polygon': strip([LEAD[0], LEAD[1], START], HALF - 14)})
patches.append({'id': 'patch_ramp', 'texture': 'gnd_grass_sunny', 'tint': '#E8F2B8', 'surface': 'grass', 'feather': 40, 'polygon': strip(RAMP, HALF - 14)})

# ---------- helper: point on corridor at spiral parameter (deg) with offset toward the outer side ---------------
def on_spiral(deg, off=0.0):
    t = (170 - deg) / 265.0
    th = math.radians(deg); r = 1200 - 380 * t + off
    return [round(C[0] + r * math.cos(th), 1), round(C[1] + r * math.sin(th), 1)]

props, pid = [], 0
def prop(asset, x, y, tags=None, flip=False):
    global pid
    pid += 1
    p = {'id': 'p_c1_%03d' % pid, 'asset': asset, 'x': round(x, 1), 'y': round(y, 1)}
    if tags: p['tags'] = tags
    if flip: p['flip'] = True
    props.append(p); return p
def ok_world(x, y):
    i, j = int(x // G), int(y // G)
    return 0 <= i < COLS and 0 <= j < ROWS and walk[j, i]
# entrance signpost, lip fence + rocks, summit stones, knoll landmarks
sign = prop('prop_marker_signpost_01', 360, ENTRY_Y - 120, ['sign'])
for x in range(900, 4000, 150):
    y = edge(x) + 62
    if (x // 150) % 7 not in (3,): prop('prop_post_boundary_wood_01', x, y, ['fence'])
bench = prop('prop_bench_view_01', 2400, edge(2400) + 70, ['viewpoint'])
prop('anc_boundary_stone_01', 2250, edge(2250) + 90, ['landmark'])
prop('anc_boundary_stone_02', 2560, edge(2560) + 92, ['landmark'], True)
for i, (x, y) in enumerate([(1500, 1300), (3300, 1250), (3750, 1900), (1050, 2050), (2900, 2050), (1850, 2150), (3500, 1650), (1300, 1750)]):
    prop('rock_moss_M_0%d' % (1 + i % 2), x, y)
for i, (x, y) in enumerate([(1350, 1050), (3600, 1000), (2000, 1550), (3000, 1450), (3400, 2100), (1500, 2200)]):
    prop('veg_shrub_M_01', x, y)
for i, (x, y) in enumerate([(1200, 1450), (3500, 1550), (1900, 1180), (1000, 1900), (3800, 1800)]):
    prop('tree_birch_M_0%d' % (1 + i % 2), x, y)
for deg in (150, 118, 62, 20, -35, -70):                       # rocks / shrubs hugging the corridor sides
    for side, nm in ((-HALF + 30, 'rock_moss_S_01'), (HALF - 30, 'veg_shrub_S_01')):
        x, y = on_spiral(deg, side)
        if ok_world(x, y): prop(nm if side < 0 else nm, x, y)
for i, (dx, dy, nm) in enumerate([(-260, -150, 'anc_standing_L_01'), (0, -330, 'tree_oak_L_01'), (240, -120, 'anc_standing_L_02'), (-120, 140, 'rock_moss_L_01'), (180, 220, 'tree_birch_M_01')]):
    prop(nm, C[0] + dx, C[1] + dy, ['landmark', 'knoll'])          # on the knoll (decor only, not walkable)

# hillside decor (blocked cells only, so purely visual): deterministic lattice with jitter
import random
rr = random.Random(7301)
for gx in range(120, W - 100, 170):
    for gy in range(int(PY1) + 120, H - 60, 170):
        x, y = gx + rr.uniform(-60, 60), gy + rr.uniform(-60, 60)
        i, j = int(x // G), int(y // G)
        if not (0 <= i < COLS and 0 <= j < ROWS) or klass[j, i] != 'slope' or dpath[j, i] < 170: continue
        k = rr.random()
        prop('tree_oak_M_0%d' % (1 + rr.randint(0, 1)) if k < .3 else 'tree_birch_M_01' if k < .45 else 'veg_shrub_M_01' if k < .7 else 'rock_moss_M_0%d' % (1 + rr.randint(0, 1)), x, y, ['hillside'])

# ---------- treasure / herb gathering points (Inventory table: data/item-data.js) --------------------------------
def inside(x, y, push=0):
    return ok_world(x, y)
herbs = [('tr_c1_herb_slope_a', on_spiral(125, HALF - 55), '坂道の草むら'), ('tr_c1_herb_slope_b', on_spiral(20, -HALF + 55), '岩陰の草むら'),
         ('tr_c1_herb_ramp', [END[0] + 70, PY1 + 110.0], 'ランプ脇の草むら'), ('tr_c1_herb_lip', [3020.0, edge(3020) + 110], '崖際の草むら')]
treasure = []
for tid, (x, y), note in herbs:
    assert ok_world(x, y), (tid, x, y)
    treasure.append({'id': tid, 'x': x, 'y': y, 'kind': 'herb', 'tier': 'common', 'hint': 'fx_treasure_glint', 'contents': None, 'note': note})
chest = [1180.0, edge(1180) + 120]
assert ok_world(*chest)
treasure.append({'id': 'tr_c1_cairn', 'x': chest[0], 'y': chest[1], 'tier': 'uncommon', 'hint': 'fx_treasure_glint', 'contents': None, 'note': '西の岩場'})

# ---------- events / spawns / transitions -----------------------------------------------------------------------
view = [2400.0, edge(2400) + 130]
spawns = {'default': 'from_lind', 'points': {
    'from_lind': {'x': 150.0, 'y': ENTRY_Y, 'facing': 'right'},
    'summit': {'x': view[0] - 120, 'y': view[1] + 220, 'facing': 'up'}}}
transitions = [{'id': 'tr_c1_to_lind', 'rect': {'shape': 'rect', 'x': 0.0, 'y': ENTRY_Y - 110, 'w': 64.0, 'h': 220.0}, 'toMap': 'lind_village', 'toSpawn': 'from_cliff',
                'fade': {'out': 0.35, 'in': 0.35}, 'enabled': True, 'note': 'リルド村南門へ戻る。可否は story hook(onVillageExit)が判断'}]
events = [
    {'id': 'ev_c1_arrival', 'type': 'locationCard', 'shape': {'shape': 'rect', 'x': 90.0, 'y': ENTRY_Y - 130, 'w': 300.0, 'h': 260.0}, 'once': True},
    {'id': 'ev_c1_sign', 'type': 'interact', 'ref': sign['id'], 'textId': 'msg_c1_sign'},
    {'id': 'ev_c1_summit', 'type': 'trigger', 'eventId': 'prologue_sunset_hill', 'shape': {'shape': 'rect', 'x': view[0] - 190, 'y': view[1] - 90, 'w': 380.0, 'h': 220.0}},
    {'id': 'ev_c1_view_bench', 'type': 'interact', 'hook': 'cliff_time_cycle', 'shape': {'shape': 'rect', 'x': 2400.0 - 70, 'y': bench['y'] - 50, 'w': 140.0, 'h': 60.0}},
]
edge_blockers = [
    {'shape': 'rect', 'x': 0, 'y': 0, 'w': W, 'h': 48}, {'shape': 'rect', 'x': 0, 'y': H - 48, 'w': W, 'h': 48},
    {'shape': 'rect', 'x': W - 48, 'y': 0, 'w': 48, 'h': H},
    {'shape': 'rect', 'x': 0, 'y': 0, 'w': 48, 'h': ENTRY_Y - 130}, {'shape': 'rect', 'x': 0, 'y': ENTRY_Y + 130, 'w': 48, 'h': H - ENTRY_Y - 130}]
# the lead-in must stay open across x=0..48: edge blockers above/below leave the corridor free
scatter = [
    {'id': 'sc_c1_grass', 'pool': ['veg_grass_tuft_01', 'veg_grass_tuft_02', 'veg_grass_tuft_03', 'veg_grass_tuft_04'], 'count': 900, 'region': {'shape': 'patch', 'ref': 'patch_meadow_summit'}, 'minDist': 44, 'avoid': ['path_core'], 'seed': 71, 'render': 'layer'},
    {'id': 'sc_c1_flowers', 'pool': ['veg_flower_white_01', 'veg_flower_white_02', 'veg_flower_blue_01', 'veg_flower_yellow_01'], 'count': 150, 'region': {'shape': 'patch', 'ref': 'patch_meadow_summit'}, 'minDist': 60, 'avoid': ['path_core'], 'seed': 72, 'render': 'layer'},
    {'id': 'sc_c1_slope_grass', 'pool': ['veg_grass_tuft_01', 'veg_grass_tuft_02', 'veg_grass_tuft_03'], 'count': 700, 'region': {'regions': [{'shape': 'patch', 'ref': 'patch_slope_%d' % k} for k in range(seg)] + [{'shape': 'patch', 'ref': 'patch_lead_in'}, {'shape': 'patch', 'ref': 'patch_ramp'}]}, 'minDist': 48, 'avoid': ['path_core'], 'seed': 73, 'render': 'layer'},
    {'id': 'sc_c1_slope_flowers', 'pool': ['veg_flower_white_01', 'veg_flower_yellow_01', 'veg_flower_blue_01'], 'count': 90, 'region': {'regions': [{'shape': 'patch', 'ref': 'patch_slope_%d' % k} for k in range(seg)]}, 'minDist': 70, 'avoid': ['path_core'], 'seed': 74, 'render': 'layer'}]

m = {
    'schemaVersion': 2, 'id': 'cliff_moher_01_spiral_ascent', 'region': 'rilde_heights', 'areaIndex': 1,
    'displayName': {'ja': '風見の断崖', 'en': 'Windward Cliffs'},
    'locationCard': {'regionJa': 'リルド郊外', 'regionEn': 'Rilde Heights', 'areaJa': '風見の断崖', 'areaEn': 'Windward Cliffs', 'triggerZone': 'ev_c1_arrival'},
    'world': {'width': float(W), 'height': float(H), 'tile': G, 'unitScale': 2.5},
    'layers': ['GROUND', 'GROUND_DETAIL', 'LOWER_PROP', 'ACTOR', 'UPPER_FOLIAGE', 'FOREGROUND'],
    'spawns': spawns,
    'terrain': {'base': {'tiles': ['gnd_grass_sunny_01', 'gnd_grass_sunny_02', 'gnd_grass_sunny_03', 'gnd_grass_sunny_04'], 'surface': 'grass', 'seed': 7101},
                'baseColor': '#6aa24a', 'patches': patches, 'openAreas': [{'id': 'open_summit', 'x': PX0, 'y': 900.0, 'w': PX1 - PX0, 'h': PY1 - 900.0}],
                'paths': [{'id': 'path_spiral', 'routeType': 'main', 'stamp': 'path_dirt_stamp', 'surface': 'dirt', 'width': 150, 'widthJitter': 10, 'edge': 'path_edge_grass', 'points': PATH_PTS},
                          {'id': 'path_summit_walk', 'routeType': 'main', 'stamp': 'path_dirt_stamp', 'surface': 'dirt', 'width': 120, 'widthJitter': 10, 'edge': 'path_edge_grass',
                           'points': [[END[0], 1880.0], [2400.0, 1500.0], [2400.0, round(view[1], 1)]]}],
                'waters': [],
                'fills': fills,
                'cliffs': [{'id': 'cliff_rock_faces', 'type': 'face_visible', 'segments': face_rects, 'faceHeight': 64, 'wobble': 0, 'seed': 7201}]},
    'props': props, 'scatter': scatter, 'effects': [],
    'collision': {'bounds': {'x': 0, 'y': 0, 'w': float(W), 'h': float(H)}, 'edgeBlockers': edge_blockers,
                  'blockers': [{'id': 'cb_c1_terrain', 'tag': 'cliff_sea', 'shape': 'rects', 'rects': rects_block}],
                  'presets': {'prop_post_boundary_wood': [[-8, -8, 16, 8]], 'prop_marker_signpost': [[-12, -10, 24, 10]], 'rock_moss_M': [[-30, -10, 60, 10]], 'rock_moss_S': [[-18, -14, 36, 14]], 'prop_bench_view': [[-40, -10, 80, 10]]}},
    'transitions': transitions, 'encounterZones': [], 'treasurePoints': treasure, 'eventZones': events,
    'cameraFocus': [{'id': 'cf_c1_summit', 'x': view[0], 'y': view[1] - 160, 'radius': 400, 'zoom': 1.0, 'priority': 3, 'mode': 'bias', 'maxBiasPx': 120, 'tags': ['vista']}],
    'ambience': {'grade': {'id': 'c1_day', 'tint': '#FFF2D0', 'tintStrength': 0.06, 'brightness': 1.04, 'saturation': 1.08}, 'shadow': {'dir': [0.55, 0.83], 'alpha': 0.25},
                 'wind': {'strength': 0.6, 'dirDeg': 60, 'gustPeriodSec': [5, 9], 'targets': {'vegetation': {'ampPx': 2.4, 'speed': 1.3}}}},
    'vista': [{'id': 'village_fire', 'kind': 'village_fire', 'x': 250.0, 'y': 2640.0, 'w': 620.0, 'h': 380.0, 'seed': 5, 'note': 'リルド村の遠景。story hook が FieldVista.set で点火'}],
    'timeOfDay': {'default': 'day', 'sunDir': [0.0, -1.0], 'note': '夕暮れ/夜は FieldTimeOfDay(js/field/field-timeofday.js) が重ねる。ストーリーは story hook が set()'},
    'particles': [{'id': 'pt_c1_motes', 'type': 'light_motes', 'region': {'shape': 'rect', 'x': 1800.0, 'y': 1000.0, 'w': 1200.0, 'h': 700.0}, 'count': 14, 'layer': 'FOREGROUND'}],
    'audio': {'bgm': {'id': 'bgm_cliff_windward', 'fadeInSec': 1.5}, 'layers': [{'id': 'amb_sea_surf', 'volume': 0.5}, {'id': 'amb_wind_soft', 'volume': 0.4}], 'hooks': []},
    'taint': {'baseLevel': 0, 'maxCoverageRatio': 0.0, 'palette': {'crack': '#120A1F', 'glow': '#8A4DFF'}, 'spots': []},
    'debug': {'showCollision': False, 'showPaths': False, 'showZones': False},
    'story': {'prologue': {'stages': [3], 'followers': [{'id': 'fiona', 'lag': 0.08, 'dx': -48, 'dy': 18, 'placeholder': True}]}},
    'culling': {'chunk': 256, 'margin': 1, 'maxLiveNodes': 800, 'viewportWorst': [1920, 1080], 'scatterRender': 'chunkLayer'}}

with open(OUT, 'w') as f: json.dump(m, f, ensure_ascii=False, separators=(',', ':'))

# ---------- validation ------------------------------------------------------------------------------------------
def reach():
    sx, sy = int(150 // G), int(ENTRY_Y // G)
    seen = np.zeros_like(walk); q = [(sx, sy)]; seen[sy, sx] = True
    for (i, j) in q:
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < COLS and 0 <= b < ROWS and walk[b, a] and not seen[b, a]: seen[b, a] = True; q.append((a, b))
    return seen
seen = reach()
vi, vj = int(view[0] // G), int(view[1] // G)
bad = 0
print('walkable cells %d, reachable %d, summit reachable %s' % (walk.sum(), seen.sum(), bool(seen[vj, vi])))
if seen.sum() != walk.sum(): print('WARN: %d walkable cells are unreachable (island)' % (walk.sum() - seen.sum()))
for t in treasure:
    ok = bool(seen[int(t['y'] // G), int(t['x'] // G)]); print(('ok   ' if ok else 'FAIL ') + t['id'] + ' reachable'); bad += (not ok)
# no shortcut: cells of the meadow must be reachable ONLY through the ramp -> block the ramp and re-flood
ramp_cells = [(i, j) for j in range(int((PY1 + 30) // G), int((PY1 + 200) // G)) for i in range(COLS) if walk[j, i] and abs(cx[i] - END[0]) <= HALF]
w2 = walk.copy()
for (i, j) in ramp_cells: w2[j, i] = False
s2 = np.zeros_like(w2); q = [(int(150 // G), int(ENTRY_Y // G))]; s2[q[0][1], q[0][0]] = True
for (i, j) in q:
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a, b = i + di, j + dj
        if 0 <= a < COLS and 0 <= b < ROWS and w2[b, a] and not s2[b, a]: s2[b, a] = True; q.append((a, b))
shortcut = bool(s2[vj, vi]); print(('FAIL ' if shortcut else 'ok   ') + 'summit is reachable only through the spiral ramp'); bad += shortcut
print('blocked rects %d, face rects %d, props %d, size %d KB' % (len(rects_block), len(face_rects), len(props), os.path.getsize(OUT) // 1024))
sys.exit(1 if bad else 0)
