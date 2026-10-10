#!/usr/bin/env python3
"""Generate the foundation maps for ドゥンヴァル砦 (fort_dunvall_*) and 王都 (royal_capital_*), schema v2, same runtime as the Moss Forest.
 Each AREA is its own map (scene) connected by transitions - see docs/field/m8-fort-capital.md for why.
 Everything is placeholder-art (painted fills + coloured stand-in props): the point is structure: collision, transitions, NPC/treasure nodes.
 usage: python3 tools/moss/build_town_maps.py     (writes data/maps/*.json, validates reachability, prints a report; exit 1 on problems)"""
import json, os, sys, zlib
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'data', 'maps')
G = 32   # validation grid

class Map:
    def __init__(s, mid, ja, en, area_ja, w, h, region_ja, region_en, floor, ground='#7d8a5a', bgm='bgm_town'):
        s.id, s.ja, s.en, s.area_ja, s.w, s.h = mid, ja, en, area_ja, w, h
        s.region = (region_ja, region_en); s.rects = []; s.fills = []; s.spawns = {}; s.trans = []; s.nodes = []; s.tre = []; s.props = []; s.zones = []
        s.floor = floor; s.ground = ground; s.bgm = bgm; s.seq = 0
    def nid(s, p): s.seq += 1; return '%s_%02d' % (p, s.seq)
    def wall(s, x, y, w, h, color='#5b5561', tag='wall'):
        s.rects.append((x, y, w, h, tag)); s.fills.append((color, (x, y, w, h)))
    def solid(s, x, y, w, h, tag):   # collision only (art provided by a fill drawn elsewhere)
        s.rects.append((x, y, w, h, tag))
    def floor_rect(s, x, y, w, h, color=None): s.fills.append((color or s.floor, (x, y, w, h)))
    def spawn(s, name, x, y, facing='down'): s.spawns[name] = {'x': x, 'y': y, 'facing': facing}
    # NOTE: door rects sit INSIDE the 48px border blockers (never on the border itself), so walking into them is possible.
    def door(s, tid, x, y, w, h, to_map, to_spawn, note=''):
        s.trans.append({'id': tid, 'rect': {'shape': 'rect', 'x': x, 'y': y, 'w': w, 'h': h}, 'toMap': to_map, 'toSpawn': to_spawn,
                        'fade': {'out': 0.35, 'in': 0.35}, 'enabled': True, 'note': note})
    def npc(s, nid, label, x, y, role='npc', shop=None, rest=False):
        """NPC / shop / quest-giver / bed slot. Click-only interact zone (no eventId, so walking past never fires it).
        Story binds by fields: npc -> FieldTalk table id; shop -> ShopData id (opened directly); action:'rest' -> sleeping place."""
        z = {'id': 'ev_' + nid, 'type': 'interact', 'npc': nid, 'shape': {'shape': 'circle', 'cx': x, 'cy': y, 'r': 90}, 'role': role, 'label': label}
        if shop: z['shop'] = shop
        if rest: z['action'] = 'rest'
        s.nodes.append(z)
        s.props.append({'id': 'p_' + nid, 'asset': 'npc_slot_' + role, 'x': x, 'y': y, 'tags': ['npc_slot']})
    def chest(s, tid, x, y, tier='common', note=''):
        s.tre.append({'id': tid, 'x': x, 'y': y, 'tier': tier, 'route': None, 'hint': 'fx_treasure_glint', 'contents': None, 'note': note})

    def doc(s):
        edge = 48
        edges = [{'shape': 'rect', 'x': 0, 'y': 0, 'w': s.w, 'h': edge}, {'shape': 'rect', 'x': 0, 'y': s.h - edge, 'w': s.w, 'h': edge},
                 {'shape': 'rect', 'x': 0, 'y': 0, 'w': edge, 'h': s.h}, {'shape': 'rect', 'x': s.w - edge, 'y': 0, 'w': edge, 'h': s.h}]
        # open the edge where a transition sits on the map border (so its rect is reachable)
        def cut(e):
            for t in s.trans:
                r = t['rect']
                if r['x'] <= 0 or r['y'] <= 0 or r['x'] + r['w'] >= s.w or r['y'] + r['h'] >= s.h: pass
            return e
        blockers = [{'id': 'cb_%s_%d' % (s.id[:6], i), 'tag': t, 'shape': 'rects', 'rects': [[x, y, w, h]]} for i, (x, y, w, h, t) in enumerate(s.rects)]
        fills = {}
        for c, r in s.fills: fills.setdefault(c, []).append(list(r))
        first = next(iter(s.spawns))
        card = {'regionJa': s.region[0], 'regionEn': s.region[1], 'areaJa': s.area_ja, 'areaEn': s.en, 'triggerZone': 'ev_arrival'}
        zones = [{'id': 'ev_arrival', 'type': 'locationCard', 'shape': {'shape': 'rect', 'x': s.spawns[first]['x'] - 150, 'y': s.spawns[first]['y'] - 150, 'w': 300, 'h': 300}, 'once': True}] + s.nodes + s.zones
        return {'schemaVersion': 2, 'id': s.id, 'region': s.region[1].lower().replace(' ', '_'), 'areaIndex': 1,
                'displayName': {'ja': s.ja, 'en': s.en}, 'locationCard': card, 'world': {'width': float(s.w), 'height': float(s.h), 'tile': 8, 'unitScale': 2.5},
                'layers': ['GROUND', 'GROUND_DETAIL', 'LOWER_PROP', 'ACTOR', 'UPPER_FOLIAGE', 'FOREGROUND'],
                'spawns': {'default': first, 'points': s.spawns},
                'terrain': {'base': {'tiles': ['gnd_grass_sunny_01', 'gnd_grass_sunny_02'], 'surface': 'grass', 'seed': zlib.crc32(s.id.encode()) % 9000}, 'baseColor': s.ground,
                            'patches': [], 'openAreas': [], 'paths': [], 'waters': [], 'cliffs': [],
                            'fills': [{'id': 'fill_%d' % i, 'color': c, 'rects': r} for i, (c, r) in enumerate(fills.items())]},
                'props': s.props, 'scatter': [], 'effects': [],
                'collision': {'bounds': {'x': 0, 'y': 0, 'w': float(s.w), 'h': float(s.h)}, 'edgeBlockers': edges, 'blockers': blockers, 'presets': {}},
                'transitions': s.trans, 'encounterZones': [], 'treasurePoints': s.tre, 'eventZones': zones, 'cameraFocus': [],
                'ambience': {'grade': {'id': 'town_day', 'tint': '#FFF2D0', 'tintStrength': 0.04, 'brightness': 1.02, 'saturation': 1.0},
                             'shadow': {'dir': [0.55, 0.83], 'alpha': 0.2}, 'wind': {'strength': 0.2, 'dirDeg': 60, 'gustPeriodSec': [6, 10], 'targets': {}}},
                'particles': [], 'audio': {'bgm': {'id': s.bgm, 'fadeInSec': 1.0}, 'layers': [], 'hooks': []},
                'taint': {'baseLevel': 0, 'maxCoverageRatio': 0.0, 'palette': {'crack': '#120A1F', 'glow': '#8A4DFF'}, 'spots': []},
                'debug': {'showCollision': False, 'showPaths': False, 'showZones': False},
                'timeOfDay': {'default': 'day'}, 'story': {'placeholder': True, 'note': '基礎構造のみ（見た目は仮）。物語への接続は未実装'},
                'culling': {'chunk': 256, 'margin': 1, 'maxLiveNodes': 800, 'viewportWorst': [1920, 1080], 'scatterRender': 'chunkLayer'}}

STONE, DARK, ROOF, WOOD = '#9a968a', '#5b5561', '#8a4f3c', '#7a5a3a'
maps = []

# ---------------- ドゥンヴァル砦 ----------------------------------------------------------------------
# 1) 中庭（外門・城壁・見張り塔・主塔の扉・城壁階段）
m = Map('fort_dunvall_01_courtyard', 'ドゥンヴァル砦　中庭', 'Dunvall Fort Courtyard', '中庭', 3200, 2400, '辺境', 'Marches', STONE, '#6f8a4a')
m.floor_rect(300, 260, 2600, 1900)                                   # courtyard + road floor
m.floor_rect(1380, 2160, 440, 240, '#a79f8a')                        # road outside the gate
m.wall(240, 200, 2720, 120)                                          # north wall
m.wall(240, 200, 120, 1980)                                          # west wall
m.wall(2840, 200, 120, 900); m.wall(2840, 1300, 120, 880)           # east wall with a gate gap y 1100..1300
m.wall(240, 2100, 1140, 120); m.wall(1820, 2100, 1140, 120)          # south wall with the gate gap x 1380..1820
for (x, y) in ((200, 160), (2800, 160), (200, 2060), (2800, 2060)): m.wall(x, y, 200, 200, '#46414d', 'tower')   # 見張り塔
m.wall(1200, 420, 800, 520, '#6a5f70', 'keep')                       # 主塔（door gap below: x 1500..1700 at y 940）
m.floor_rect(1500, 940, 200, 80, '#c9b27a')
m.wall(600, 1500, 400, 200, WOOD, 'barracks'); m.wall(2200, 1500, 400, 200, WOOD, 'stable')
m.spawn('from_road', 1600, 2300, 'up'); m.spawn('from_capital_road', 3050, 1200, 'left'); m.spawn('from_ramparts', 480, 1100, 'right'); m.spawn('from_keep', 1600, 1080, 'down')
m.door('tr_f1_to_village', 1380, 2288, 440, 64, 'lind_village', 'from_fort', '南門 -> 街道 -> リルド村（story hook onVillageExit）')
m.door('tr_f1_to_capital', 3040, 1100, 100, 200, 'royal_capital_01_market', 'from_fort_road', '東門 -> 王都への街道')
m.door('tr_f1_to_ramparts', 360, 1000, 80, 220, 'fort_dunvall_02_ramparts', 'from_courtyard', '城壁への階段')
m.door('tr_f1_to_keep', 1500, 960, 200, 60, 'fort_dunvall_03_keep', 'from_courtyard', '主塔の扉')
m.npc('f1_captain', '砦の隊長', 1600, 1300, 'quest'); m.npc('f1_quartermaster', '補給係（武具屋）', 1000, 1800, 'shop'); m.npc('f1_bed', '兵舎の仮眠所', 800, 1760, 'bed', rest=True); m.npc('f1_gate_guard', '門番', 1250, 2050, 'npc')
m.chest('tr_f1_barracks', 640, 1760, 'common', '兵舎の脇の箱（仮）')
maps.append(m)
# 2) 城壁の上（ぐるりと一周する歩廊・見張り台）
m = Map('fort_dunvall_02_ramparts', 'ドゥンヴァル砦　城壁', 'Dunvall Fort Ramparts', '城壁の上', 2800, 1600, '辺境', 'Marches', '#a8a294', '#4a6a8a')
for c in (('#a8a294', (200, 200, 2400, 1200)),): m.floor_rect(*c[1], c[0])
m.wall(440, 420, 1920, 760, '#6f8a4a', 'drop')                        # 中庭側へ落ちる（通行不可）
for r in ((0, 0, 2800, 200), (0, 1400, 2800, 200), (2600, 200, 200, 1200), (0, 200, 200, 500), (0, 900, 200, 500)): m.solid(*r, 'void')   # outside the walkway = air
m.floor_rect(200, 200, 320, 320, '#c9b27a'); m.floor_rect(2280, 200, 320, 320, '#c9b27a')   # 見張り台（歩ける）
m.spawn('from_courtyard', 300, 800, 'right'); m.spawn('from_keep', 1400, 300, 'down')
m.door('tr_f2_down', 150, 700, 80, 200, 'fort_dunvall_01_courtyard', 'from_ramparts', '中庭への階段')
m.door('tr_f2_to_keep', 1300, 200, 300, 60, 'fort_dunvall_03_keep', 'from_wall', '主塔の上階への扉')
m.npc('f2_lookout', '見張り台の兵士', 2440, 340, 'npc'); m.chest('tr_f2_tower', 2400, 320, 'uncommon', '見張り台の箱（仮）')
maps.append(m)
# 3) 主塔の内部（大広間・左右の部屋への通路）
m = Map('fort_dunvall_03_keep', 'ドゥンヴァル砦　主塔', 'Dunvall Fort Keep', '主塔の内部', 2400, 1800, '辺境', 'Marches', '#8c7f6a', '#2b2830', 'bgm_fort_interior')
m.floor_rect(200, 200, 2000, 1400); m.floor_rect(1000, 200, 400, 1400, '#9c2f3a')    # 絨毯
m.wall(200, 200, 2000, 100, DARK); m.wall(200, 1500, 800, 100, DARK); m.wall(1400, 1500, 800, 100, DARK)   # south wall: gap x 1000..1400
m.wall(200, 200, 100, 1400, DARK); m.wall(2100, 200, 100, 1400, DARK)
for (x, y) in ((620, 640), (1700, 640), (620, 1040), (1700, 1040)): m.wall(x, y, 80, 80, '#6a6470', 'pillar')
m.wall(1000, 300, 400, 160, '#7a3b2b', 'dais')
m.spawn('from_courtyard', 1200, 1400, 'up'); m.spawn('from_wall', 1820, 860, 'left')
m.door('tr_f3_exit', 1000, 1560, 400, 60, 'fort_dunvall_01_courtyard', 'from_keep', '中庭へ出る')
m.door('tr_f3_to_wall', 1980, 760, 120, 200, 'fort_dunvall_02_ramparts', 'from_keep', '城壁へ上がる階段')
m.npc('f3_commander', '砦の司令官（大広間）', 1200, 560, 'quest'); m.npc('f3_armory', '武器庫番', 420, 900, 'npc'); m.chest('tr_f3_armory', 400, 400, 'uncommon', '武器庫の箱（仮）')
maps.append(m)

# ---------------- 王都 ---------------------------------------------------------------------------------
# 1) 商業区
m = Map('royal_capital_01_market', '王都　商業区', 'Royal Capital Market District', '商業区', 4800, 3200, '王都', 'Royal Capital', '#b5ad98', '#8a8f78')
m.floor_rect(200, 200, 4400, 2800)
m.floor_rect(2200, 200, 400, 2800, '#c7bda2')                        # 中央の大通り
stalls = [(500, 600), (900, 600), (500, 1200), (900, 1200), (3500, 600), (3900, 600), (3500, 1200), (3900, 1200)]
for (x, y) in stalls: m.wall(x, y, 260, 160, '#b4553b', 'stall')
for (x, y, w, h) in ((200, 1900, 1500, 800), (3100, 1900, 1500, 800)): m.wall(x, y, w, h, '#7d6f62', 'building')   # 商館
m.spawn('from_west_gate', 360, 1500, 'right'); m.spawn('from_fort_road', 360, 1500, 'right'); m.spawn('from_plaza', 4400, 1500, 'left'); m.spawn('from_residential', 2400, 2850, 'up')
m.door('tr_r1_west_gate', 48, 1300, 64, 400, 'fort_dunvall_01_courtyard', 'from_capital_road', '王都の西門 -> 街道 -> ドゥンヴァル砦')
m.door('tr_r1_to_plaza', 4688, 1300, 64, 400, 'royal_capital_02_castle_plaza', 'from_market', '城前広場へ')
m.door('tr_r1_to_residential', 2200, 3088, 400, 64, 'royal_capital_03_residential', 'from_market', '住宅街へ')
m.npc('r1_general', '雑貨商（ショップ）', 700, 980, 'shop', shop='royal_general'); m.npc('r1_weapon', '武具商（ショップ）', 4000, 980, 'shop', shop='royal_arms')
m.npc('r1_board', '依頼掲示板', 2000, 1500, 'quest'); m.npc('r1_rumor', '噂好きの商人', 1900, 2250, 'npc'); m.npc('r1_child', '走り回る子ども', 3200, 1500, 'npc'); m.npc('r1_inn', '宿屋の呼び込み', 2800, 1500, 'npc')
m.chest('tr_r1_alley', 380, 2800, 'common', '路地裏の箱（仮）')
maps.append(m)
# 2) 城前広場
m = Map('royal_capital_02_castle_plaza', '王都　城前広場', 'Royal Capital Castle Plaza', '城前広場', 4000, 3600, '王都', 'Royal Capital', '#c4bba3', '#8a8f78')
m.floor_rect(200, 200, 3600, 3200)
m.wall(1000, 200, 2000, 900, '#6a5f70', 'castle'); m.floor_rect(1800, 1100, 400, 120, '#c9b27a')     # 城 + 城門前の階段
m.wall(200, 200, 800, 700, '#7d6f62', 'building'); m.wall(3000, 200, 800, 700, '#7d6f62', 'building')
m.wall(1850, 1900, 300, 300, '#6fa6b8', 'fountain')                  # 噴水
m.spawn('from_market', 360, 1700, 'right'); m.spawn('from_residential', 2000, 3300, 'up'); m.spawn('from_castle', 2000, 1260, 'down')
m.door('tr_r2_to_market', 48, 1500, 64, 400, 'royal_capital_01_market', 'from_plaza', '商業区へ')
m.door('tr_r2_to_residential', 1800, 3488, 400, 64, 'royal_capital_03_residential', 'from_plaza', '住宅街へ')
m.door('tr_r2_castle_gate', 1800, 1100, 400, 60, 'TBD', 'TBD', '王城の中へ。接続は未実装')
m.npc('r2_guard', '城門の衛兵', 1650, 1300, 'npc'); m.npc('r2_bard', '広場の吟遊詩人', 1500, 2400, 'npc'); m.npc('r2_herald', '触れ役', 2300, 2600, 'quest'); m.chest('tr_r2_garden', 3500, 3000, 'uncommon', '花壇の脇の箱（仮）')
maps.append(m)
# 3) 住宅街
m = Map('royal_capital_03_residential', '王都　住宅街', 'Royal Capital Residential Quarter', '住宅街', 3600, 3200, '王都', 'Royal Capital', '#aaa28c', '#8a8f78')
m.floor_rect(200, 200, 3200, 2800, '#bdb29a')
houses = [(400, 500), (1000, 500), (1600, 500), (2600, 500), (400, 1500), (1000, 1500), (2600, 1500), (400, 2400), (1000, 2400), (2600, 2400)]
for i, (x, y) in enumerate(houses):
    m.wall(x, y, 420, 360, ROOF, 'house'); m.floor_rect(x + 160, y + 360, 100, 60, '#c9b27a')
    m.zones.append({'id': 'ev_door_%02d' % i, 'type': 'interact', 'textId': 'msg_house_locked', 'shape': {'shape': 'circle', 'cx': x + 210, 'cy': y + 400, 'r': 70}})
m.spawn('from_market', 1700, 360, 'down'); m.spawn('from_plaza', 3300, 1500, 'left')
m.door('tr_r3_to_market', 1500, 48, 600, 64, 'royal_capital_01_market', 'from_residential', '商業区へ')
m.door('tr_r3_to_plaza', 3488, 1300, 64, 400, 'royal_capital_02_castle_plaza', 'from_residential', '城前広場へ')
m.npc('r3_resident', '住民', 1800, 1500, 'npc'); m.npc('r3_cat_man', '猫に餌をやる男', 3250, 2050, 'npc'); m.npc('r3_elder_quest', '依頼人の老婦人', 1500, 2700, 'quest'); m.chest('tr_r3_backyard', 2400, 2900, 'common', '裏庭の箱（仮）')
maps.append(m)

# ---------------- validation ---------------------------------------------------------------------------
def validate(mp, doc):
    errs = []
    W, H = mp.w, mp.h
    solid = [(x, y, w, h) for (x, y, w, h, t) in mp.rects if t != 'drop' or True]
    edges = [(0, 0, W, 48), (0, H - 48, W, 48), (0, 0, 48, H), (W - 48, 0, 48, H)]
    def blocked(x, y):
        for (a, b, c, d) in solid + edges:
            if a <= x < a + c and b <= y < b + d: return True
        return not (0 <= x < W and 0 <= y < H)
    # transitions that sit on the map border: carve the edge so they are touchable (edge blockers are 48 px; the zone is 64 px deep)
    cols, rows = W // G, H // G
    def free(i, j): return not blocked(i * G + G / 2, j * G + G / 2)
    def cell(x, y): return int(x // G), int(y // G)
    start = cell(*[mp.spawns[next(iter(mp.spawns))][k] for k in ('x', 'y')])
    seen = {start}; q = [start]
    while q:
        i, j = q.pop()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (i + di, j + dj)
            if n in seen or not (0 <= n[0] < cols and 0 <= n[1] < rows) or not free(*n): continue
            seen.add(n); q.append(n)
    def reach(x, y, pad=64):   # any free reachable cell within pad px
        ci, cj = cell(x, y); r = pad // G + 1
        return any((ci + a, cj + b) in seen for a in range(-r, r + 1) for b in range(-r, r + 1))
    for n, p in mp.spawns.items():
        if not reach(p['x'], p['y'], 0) and not (cell(p['x'], p['y']) in seen): errs.append('spawn %s not reachable from default spawn' % n)
        if blocked(p['x'], p['y']): errs.append('spawn %s is inside a wall' % n)
    for t in mp.trans:
        r = t['rect']
        inside = any((i, j) in seen and r['x'] <= i * G + G / 2 < r['x'] + r['w'] and r['y'] <= j * G + G / 2 < r['y'] + r['h'] for i in range(int(r['x'] // G), int((r['x'] + r['w']) // G) + 1) for j in range(int(r['y'] // G), int((r['y'] + r['h']) // G) + 1))
        if not inside: errs.append('transition %s: no reachable free ground INSIDE its rect (is it on/under a border blocker?)' % t['id'])
    for z in mp.nodes + mp.tre:
        x, y = (z['shape']['cx'], z['shape']['cy']) if 'shape' in z else (z['x'], z['y'])
        if not reach(x, y, 96): errs.append('node %s unreachable' % z['id'])
    # transition targets exist
    for t in mp.trans:
        if t['toMap'] not in ('TBD', 'lind_village'):
            tgt = next((o for o in maps if o.id == t['toMap']), None)
            if not tgt: errs.append('%s -> unknown map %s' % (t['id'], t['toMap']))
            elif t['toSpawn'] not in tgt.spawns: errs.append('%s -> %s has no spawn %s' % (t['id'], t['toMap'], t['toSpawn']))
    return errs, len(seen) * G * G / (W * H)

bad = 0
for mp in maps:
    d = mp.doc(); errs, cov = validate(mp, d)
    json.dump(d, open(os.path.join(OUT, mp.id + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('%-34s %5dx%-5d walls=%-3d npc=%d chest=%d trans=%d walkable-reachable=%2.0f%% %s' % (mp.id, mp.w, mp.h, len(mp.rects), len([n for n in mp.nodes]), len(mp.tre), len(mp.trans), cov * 100, 'OK' if not errs else 'PROBLEMS'))
    for e in errs: print('   ', e); bad += 1
sys.exit(1 if bad else 0)
