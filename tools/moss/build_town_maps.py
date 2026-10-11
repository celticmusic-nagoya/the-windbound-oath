#!/usr/bin/env python3
"""Generate the foundation maps for ドゥンヴァル砦 (fort_dunvall_*) and 王都 (royal_capital_*), schema v2, same runtime as the Moss Forest.
 Each AREA is its own map (scene) connected by transitions - see docs/field/m8-fort-capital.md for why.
 Everything is placeholder-art (painted fills + coloured stand-in props): the point is structure: collision, transitions, NPC/treasure nodes.
 usage: python3 tools/moss/build_town_maps.py     (writes data/maps/*.json, validates reachability, prints a report; exit 1 on problems)"""
import json, os, sys, zlib
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'data', 'maps')
G = 32   # validation grid

# Weather per map (js/field/field-weather.js): default preset + rules (last matching rule wins), see docs/field/weather.md
_DONE = {'any': [{'quest': {'id': 'q_capital_comb', 'state': 'complete'}}, {'quest': {'id': 'q_capital_comb', 'state': 'reported'}}]}
WEATHER = {
    'royal_capital_03_residential': {'default': 'rain', 'rules': [{'when': _DONE, 'set': 'clear', 'ms': 6000}], 'note': 'drizzle over the residential quarter until the silver comb errand is done'},
    'fort_dunvall_02_ramparts': {'default': 'mist', 'rules': []},
}
class Map:
    def __init__(s, mid, ja, en, area_ja, w, h, region_ja, region_en, floor, ground='#7d8a5a', bgm='bgm_town'):
        s.id, s.ja, s.en, s.area_ja, s.w, s.h = mid, ja, en, area_ja, w, h
        s.region = (region_ja, region_en); s.rects = []; s.fills = []; s.spawns = {}; s.trans = []; s.nodes = []; s.tre = []; s.props = []; s.walkers = []; s.zones = []
        s.floor = floor; s.ground = ground; s.bgm = bgm; s.seq = 0
    def nid(s, p): s.seq += 1; return '%s_%02d' % (p, s.seq)
    def wall(s, x, y, w, h, color='#5b5561', tag='wall', pattern='brick'):
        s.rects.append((x, y, w, h, tag)); s.fills.append((color, (x, y, w, h), pattern))
    def solid(s, x, y, w, h, tag):   # collision only (art provided by a fill drawn elsewhere)
        s.rects.append((x, y, w, h, tag))
    def prop(s, asset, x, y, tags=None, z=None):   # decorative sprite, feet at (x, y)
        s.seq += 1; d = {'id': 'd_%s_%03d' % (asset.replace('town_', '').replace('furn_', '')[:10], s.seq), 'asset': asset, 'x': x, 'y': y, 'tags': tags or ['deco']}
        if z is not None: d['z'] = z
        s.props.append(d); return d
    def deco(s, asset, x, y, sw=0, sh=0, tags=None):   # sprite + a small collision box at its feet (sw x sh, centred)
        s.prop(asset, x, y, tags)
        if sw: s.rects.append((x - sw // 2, y - sh, sw, sh, 'deco'))
    def decal(s, asset, x, y): s.prop(asset, x, y, ['decal'], z=1)
    def floor_rect(s, x, y, w, h, color=None, pattern='flagstone'): s.fills.append((color or s.floor, (x, y, w, h), pattern))
    def spawn(s, name, x, y, facing='down'): s.spawns[name] = {'x': x, 'y': y, 'facing': facing}
    # NOTE: door rects sit INSIDE the 48px border blockers (never on the border itself), so walking into them is possible.
    def door(s, tid, x, y, w, h, to_map, to_spawn, note=''):
        s.trans.append({'id': tid, 'rect': {'shape': 'rect', 'x': x, 'y': y, 'w': w, 'h': h}, 'toMap': to_map, 'toSpawn': to_spawn,
                        'fade': {'out': 0.35, 'in': 0.35}, 'enabled': True, 'note': note})
    LOOK = {'f1_captain': 'captain', 'f1_quartermaster': 'merchant', 'f1_gate_guard': 'guard', 'f1_bed': 'bed', 'f2_lookout': 'soldier', 'f3_commander': 'captain', 'f3_armory': 'soldier',
            'r1_general': 'merchant', 'r1_weapon': 'merchant', 'r1_board': 'board', 'r1_rumor': 'townsman', 'r1_child': 'child', 'r1_inn': 'townswoman',
            'r2_guard': 'guard', 'r2_bard': 'bard', 'r2_herald': 'soldier', 'r3_resident': 'townswoman', 'r3_cat_man': 'elder', 'r3_elder_quest': 'questgiver'}
    def npc(s, nid, label, x, y, role='npc', shop=None, rest=False, walk=None, speed=24):
        """NPC / shop / quest-giver / bed slot. Click-only interact zone (no eventId, so walking past never fires it).
        Story binds by fields: npc -> FieldTalk table id; shop -> ShopData id (opened directly); action:'rest' -> sleeping place."""
        z = {'id': 'ev_' + nid, 'type': 'interact', 'npc': nid, 'shape': {'shape': 'circle', 'cx': x, 'cy': y, 'r': 90}, 'role': role, 'label': label}
        if shop: z['shop'] = shop
        if rest: z['action'] = 'rest'
        s.nodes.append(z)
        if walk:   # patrolling NPC: drawn by FieldWalkers (6-frame walk) instead of a static prop; path = offsets from the home point
            s.walkers.append({'id': 'w_' + nid, 'look': s.LOOK.get(nid, role), 'x': x, 'y': y, 'path': walk, 'speed': speed, 'rest': [2.0, 4.5]})
            return
        s.props.append({'id': 'p_' + nid, 'asset': 'npc_slot_' + s.LOOK.get(nid, role), 'x': x, 'y': y, 'tags': ['npc_slot']})
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
        fills = {}   # drawn in insertion order; consecutive same (colour, pattern) rects share one fill entry
        order = []
        for c, r, pt in s.fills:
            if not order or order[-1][0] != (c, pt): order.append([(c, pt), []])
            order[-1][1].append(list(r))
        first = next(iter(s.spawns))
        card = {'regionJa': s.region[0], 'regionEn': s.region[1], 'areaJa': s.area_ja, 'areaEn': s.en, 'triggerZone': 'ev_arrival'}
        zones = [{'id': 'ev_arrival', 'type': 'locationCard', 'shape': {'shape': 'rect', 'x': s.spawns[first]['x'] - 150, 'y': s.spawns[first]['y'] - 150, 'w': 300, 'h': 300}, 'once': True}] + s.nodes + s.zones
        return {'schemaVersion': 2, 'id': s.id, 'region': s.region[1].lower().replace(' ', '_'), 'areaIndex': 1,
                'displayName': {'ja': s.ja, 'en': s.en}, 'locationCard': card, 'world': {'width': float(s.w), 'height': float(s.h), 'tile': 8, 'unitScale': 2.5},
                'layers': ['GROUND', 'GROUND_DETAIL', 'LOWER_PROP', 'ACTOR', 'UPPER_FOLIAGE', 'FOREGROUND'],
                'spawns': {'default': first, 'points': s.spawns},
                'terrain': {'base': {'tiles': ['gnd_grass_sunny_01', 'gnd_grass_sunny_02'], 'surface': 'grass', 'seed': zlib.crc32(s.id.encode()) % 9000}, 'baseColor': s.ground,
                            'patches': [], 'openAreas': [], 'paths': [], 'waters': [], 'cliffs': [],
                            'fills': [dict({'id': 'fill_%d' % i, 'color': k[0], 'rects': r}, **({'pattern': k[1]} if k[1] else {})) for i, (k, r) in enumerate(order)]},
                'props': s.props, 'walkers': s.walkers, 'scatter': [], 'effects': [],
                'collision': {'bounds': {'x': 0, 'y': 0, 'w': float(s.w), 'h': float(s.h)}, 'edgeBlockers': edges, 'blockers': blockers, 'presets': {}},
                'transitions': s.trans, 'encounterZones': [], 'treasurePoints': s.tre, 'eventZones': zones, 'cameraFocus': [],
                'ambience': {'grade': {'id': 'town_day', 'tint': '#FFF2D0', 'tintStrength': 0.04, 'brightness': 1.02, 'saturation': 1.0},
                             'shadow': {'dir': [0.55, 0.83], 'alpha': 0.2}, 'wind': {'strength': 0.2, 'dirDeg': 60, 'gustPeriodSec': [6, 10], 'targets': {}}},
                'particles': [], 'audio': {'bgm': {'id': s.bgm, 'fadeInSec': 1.0}, 'layers': [], 'hooks': []},
                'taint': {'baseLevel': 0, 'maxCoverageRatio': 0.0, 'palette': {'crack': '#120A1F', 'glow': '#8A4DFF'}, 'spots': []},
                'debug': {'showCollision': False, 'showPaths': False, 'showZones': False},
                'timeOfDay': {'default': 'day'}, **({'weather': WEATHER[s.id]} if s.id in WEATHER else {}), 'story': {'placeholder': True, 'note': '基礎構造のみ（見た目は仮）。物語への接続は未実装'},
                'culling': {'chunk': 256, 'margin': 1, 'maxLiveNodes': 800, 'viewportWorst': [1920, 1080], 'scatterRender': 'chunkLayer'}}

STONE, DARK, ROOF, WOOD = '#9a968a', '#5b5561', '#8a4f3c', '#7a5a3a'
maps = []

# ---------------- ドゥンヴァル砦 ----------------------------------------------------------------------
# 1) 中庭（外門・城壁・見張り塔・主塔の扉・城壁階段）
m = Map('fort_dunvall_01_courtyard', 'ドゥンヴァル砦　中庭', 'Dunvall Fort Courtyard', '中庭', 3200, 2400, '辺境', 'Marches', STONE, '#6f8a4a')
m.floor_rect(300, 260, 2600, 1900)                                   # courtyard + road floor
m.floor_rect(1380, 2160, 440, 240, '#a79f8a', 'cobble')                        # road outside the gate
m.wall(240, 200, 2720, 120)                                          # north wall
m.wall(240, 200, 120, 1980)                                          # west wall
m.wall(2840, 200, 120, 900); m.wall(2840, 1300, 120, 880)           # east wall with a gate gap y 1100..1300
m.wall(240, 2100, 1140, 120); m.wall(1820, 2100, 1140, 120)          # south wall with the gate gap x 1380..1820
for (x, y) in ((200, 160), (2800, 160), (200, 2060), (2800, 2060)): m.wall(x, y, 200, 200, '#46414d', 'tower'); m.prop('town_tower_round', x + 100, y + 214)   # 見張り塔
m.solid(1200, 420, 800, 520, 'keep'); m.prop('town_keep_front', 1600, 948)                       # 主塔（door gap below: x 1500..1700 at y 940）
m.floor_rect(1500, 940, 200, 80, '#c9b27a', 'planks')
for x in range(380, 2840, 200): m.prop('town_battlement', x + 100, 336)                         # 北壁の胸壁
for x in range(1240, 2000, 200): m.prop('town_battlement', x + 100, 548)                        # 主塔の屋根の胸壁
m.floor_rect(1440, 960, 320, 1100, '#b9ae92', 'cobble'); m.floor_rect(420, 1960, 2360, 100, '#b9ae92', 'cobble')   # 主塔の扉から正門までの石畳の道
m.floor_rect(1440, 2000, 320, 120, '#b9ae92', 'cobble')
m.prop('town_gate_arch', 1600, 2236); m.solid(1380, 2100, 70, 130, 'pier'); m.solid(1750, 2100, 70, 130, 'pier')      # 正門
for x in (1340, 1860): m.deco('town_torch_post', x, 2250, 20, 14)
for x in (1450, 1750): m.deco('town_banner_pole_red', x, 1040, 18, 14); m.prop('town_torch_post', x + (-50 if x < 1600 else 50), 1030)
for y in (1250, 1550, 1850): m.deco('town_lamp_post', 1400, y, 14, 10); m.deco('town_lamp_post', 1800, y, 14, 10)
m.deco('town_well', 900, 1050, 60, 28)
m.prop('town_weapon_stand_out', 2300, 1150); m.rects.append((2250, 1120, 100, 30, 'deco'))
m.deco('town_training_dummy', 2150, 1000, 24, 14); m.deco('town_training_dummy', 2450, 1000, 24, 14); m.deco('town_training_dummy', 2300, 880, 24, 14)
m.deco('town_hay_stack', 2700, 1800, 120, 40); m.deco('town_hay_stack', 2120, 1780, 120, 40)
m.deco('furn_crates_stack', 1130, 1760, 60, 30); m.deco('furn_barrel', 1200, 1800, 36, 24); m.deco('furn_barrel', 1000, 1880, 36, 24); m.deco('furn_crate', 1090, 1850, 44, 26)
m.deco('furn_barrel', 700, 1780, 36, 24); m.deco('furn_crate', 480, 1780, 44, 26)
m.deco('town_cart', 2400, 1980, 110, 30)
for (x, y) in ((560, 2340), (880, 2350), (2260, 2350), (2620, 2340), (120, 1000), (120, 1500), (3080, 1700)): m.deco('town_tree_pine', x, y, 24, 14)
for (x, y) in ((420, 520), (2780, 520), (460, 1900)): m.deco('town_bush_round', x, y, 40, 20)
m.deco('town_tree_oak', 560, 640, 30, 18); m.deco('town_tree_oak', 2640, 700, 30, 18)
m.solid(600, 1500, 400, 200, 'barracks'); m.prop('town_barracks', 800, 1706); m.solid(2200, 1500, 400, 200, 'stable'); m.prop('town_stable', 2400, 1706)
m.spawn('from_road', 1600, 2300, 'up'); m.spawn('from_capital_road', 3050, 1200, 'left'); m.spawn('from_ramparts', 480, 1100, 'right'); m.spawn('from_keep', 1600, 1080, 'down')
m.door('tr_f1_to_village', 1380, 2288, 440, 64, 'lind_village', 'from_fort', '南門 -> 街道 -> リルド村（story hook onVillageExit）')
m.door('tr_f1_to_capital', 3040, 1100, 100, 200, 'royal_capital_01_market', 'from_fort_road', '東門 -> 王都への街道')
m.door('tr_f1_to_ramparts', 360, 1000, 80, 220, 'fort_dunvall_02_ramparts', 'from_courtyard', '城壁への階段')
m.door('tr_f1_to_keep', 1500, 960, 200, 60, 'fort_dunvall_03_keep', 'from_courtyard', '主塔の扉')
m.npc('f1_captain', '砦の隊長', 1600, 1300, 'quest'); m.npc('f1_quartermaster', '補給係（武具屋）', 1000, 1800, 'shop'); m.npc('f1_bed', '兵舎の仮眠所', 800, 1760, 'bed', rest=True); m.npc('f1_gate_guard', '門番', 1250, 2050, 'npc', walk=[[0, -60], [0, 0]])
m.chest('tr_f1_barracks', 640, 1760, 'common', '兵舎の脇の箱（仮）')
maps.append(m)
# 2) 城壁の上（ぐるりと一周する歩廊・見張り台）
m = Map('fort_dunvall_02_ramparts', 'ドゥンヴァル砦　城壁', 'Dunvall Fort Ramparts', '城壁の上', 2800, 1600, '辺境', 'Marches', '#a8a294', '#4a6a8a')
for c in (('#a8a294', (200, 200, 2400, 1200)),): m.floor_rect(*c[1], c[0])
m.wall(440, 420, 1920, 760, '#6f8a4a', 'drop')                        # 中庭側へ落ちる（通行不可）
for r in ((0, 0, 2800, 200), (0, 1400, 2800, 200), (2600, 200, 200, 1200), (0, 200, 200, 500), (0, 900, 200, 500)): m.solid(*r, 'void')   # outside the walkway = air
m.floor_rect(200, 200, 320, 320, '#c9b27a'); m.floor_rect(2280, 200, 320, 320, '#c9b27a')   # 見張り台（歩ける）
for x in range(200, 2600, 200): m.prop('town_battlement', x + 100, 330); m.prop('town_battlement', x + 100, 1230)      # 歩廊の内外の胸壁
for x in (420, 1000, 1600, 2200): m.deco('town_torch_post', x, 1190, 18, 12)
for x in (700, 1300, 1900): m.deco('town_banner_pole_red', x, 260, 18, 12)
m.deco('furn_barrel', 360, 1100, 36, 24); m.deco('furn_crate', 440, 1120, 44, 26); m.deco('furn_weapon_rack', 2150, 1160, 70, 24); m.deco('furn_crates_stack', 1650, 1120, 60, 30)
m.spawn('from_courtyard', 300, 800, 'right'); m.spawn('from_keep', 1400, 300, 'down')
m.door('tr_f2_down', 150, 700, 80, 200, 'fort_dunvall_01_courtyard', 'from_ramparts', '中庭への階段')
m.door('tr_f2_to_keep', 1300, 200, 300, 60, 'fort_dunvall_03_keep', 'from_wall', '主塔の上階への扉')
m.npc('f2_lookout', '見張り台の兵士', 2440, 340, 'npc', walk=[[70, 0], [0, 0]]); m.chest('tr_f2_tower', 2400, 320, 'uncommon', '見張り台の箱（仮）')
maps.append(m)
# 3) 主塔の内部（大広間・左右の部屋への通路）
m = Map('fort_dunvall_03_keep', 'ドゥンヴァル砦　主塔', 'Dunvall Fort Keep', '主塔の内部', 2400, 1800, '辺境', 'Marches', '#8c7f6a', '#2b2830', 'bgm_fort_interior')
m.floor_rect(200, 200, 2000, 1400); m.floor_rect(1000, 200, 400, 1400, '#9c2f3a', None)    # 絨毯
m.wall(200, 200, 2000, 100, DARK); m.wall(200, 1500, 800, 100, DARK); m.wall(1400, 1500, 800, 100, DARK)   # south wall: gap x 1000..1400
m.wall(200, 200, 100, 1400, DARK); m.wall(2100, 200, 100, 1400, DARK)
for (x, y) in ((620, 640), (1700, 640), (620, 1040), (1700, 1040)): m.wall(x, y, 80, 80, '#6a6470', 'pillar')
m.wall(1000, 300, 400, 160, '#7a3b2b', 'dais', 'planks')
for x in (520, 1080, 1320, 1880): m.prop('furn_tapestry', x, 290, ['deco'])
for (x, y) in ((620, 640), (1700, 640), (620, 1040), (1700, 1040)): m.prop('town_torch_post', x + 40, y + 10)
m.deco('furn_chair', 1200, 420, 40, 20); m.decal('furn_rug_red', 1200, 700)
m.deco('furn_weapon_rack', 420, 1240, 70, 24); m.deco('furn_weapon_rack', 520, 1240, 70, 24); m.deco('furn_crates_stack', 420, 560, 60, 30); m.deco('furn_barrel', 340, 640, 36, 24)
m.deco('furn_map_table', 1750, 1300, 110, 40); m.deco('furn_fireplace', 2000, 300, 140, 30)
for x in (700, 1700): m.deco('town_banner_pole_red', x, 1480, 18, 12)
m.spawn('from_courtyard', 1200, 1400, 'up'); m.spawn('from_wall', 1820, 860, 'left')
m.door('tr_f3_exit', 1000, 1560, 400, 60, 'fort_dunvall_01_courtyard', 'from_keep', '中庭へ出る')
m.door('tr_f3_to_wall', 1980, 760, 120, 200, 'fort_dunvall_02_ramparts', 'from_keep', '城壁へ上がる階段')
m.npc('f3_commander', '砦の司令官（大広間）', 1200, 560, 'quest'); m.npc('f3_armory', '武器庫番', 420, 900, 'npc'); m.chest('tr_f3_armory', 400, 400, 'uncommon', '武器庫の箱（仮）')
maps.append(m)

# ---------------- 王都 ---------------------------------------------------------------------------------
# 1) 商業区
m = Map('royal_capital_01_market', '王都　商業区', 'Royal Capital Market District', '商業区', 4800, 3200, '王都', 'Royal Capital', '#b5ad98', '#8a8f78')
m.floor_rect(200, 200, 4400, 2800)
m.floor_rect(2200, 200, 400, 2800, '#c7bda2', 'cobble')                        # 中央の大通り
stalls = [(500, 600), (900, 600), (500, 1200), (900, 1200), (3500, 600), (3900, 600), (3500, 1200), (3900, 1200)]
for i, (x, y) in enumerate(stalls): m.solid(x, y + 20, 260, 140, 'stall'); m.prop('town_stall_' + ['red', 'blue', 'green'][i % 3], x + 130, y + 166)
for (x, y, w, h) in ((200, 2320, 1500, 380), (3100, 2320, 1500, 380)):   # 商館（3軒並び）
    m.solid(x, y, w, h, 'building')
    for k in range(3): m.prop('town_house_town_' + 'abc'[(k + x // 1000) % 3], x + 250 + k * 500, y + h + 8)
for y in range(320, 2900, 340): m.deco('town_lamp_post', 2150, y, 14, 10); m.deco('town_lamp_post', 2650, y, 14, 10)
for y in (420, 1100, 1800): m.prop('town_banner_pole', 2260, y); m.prop('town_banner_pole', 2540, y)
m.deco('town_fountain', 2400, 1560, 150, 40)
m.deco('town_flowerbed', 1700, 780, 100, 26); m.deco('town_flowerbed', 3000, 780, 100, 26)
m.deco('town_well', 1500, 1760, 70, 30); m.deco('town_cart', 3400, 1440, 120, 30); m.deco('town_cart', 1300, 1480, 120, 30)
m.deco('town_bench_stone', 2050, 2100, 56, 18); m.deco('town_bench_stone', 2750, 2100, 56, 18)
for (x, y) in ((340, 340), (4500, 340), (1700, 360), (3050, 360), (340, 1000)): m.deco('town_tree_oak', x, y, 28, 16)
for (x, y) in ((1300, 800), (3300, 840)): m.deco('town_bush_round', x, y, 40, 20)
m.deco('furn_crates_stack', 560, 1000, 60, 30); m.deco('furn_barrel', 1100, 1000, 36, 24); m.deco('furn_sacks_pile', 4300, 1000, 50, 26); m.deco('furn_barrel', 3700, 1000, 36, 24)
m.spawn('from_west_gate', 360, 1500, 'right'); m.spawn('from_fort_road', 360, 1500, 'right'); m.spawn('from_plaza', 4400, 1500, 'left'); m.spawn('from_residential', 2400, 2850, 'up')
m.door('tr_r1_west_gate', 48, 1300, 64, 400, 'fort_dunvall_01_courtyard', 'from_capital_road', '王都の西門 -> 街道 -> ドゥンヴァル砦')
m.door('tr_r1_to_plaza', 4688, 1300, 64, 400, 'royal_capital_02_castle_plaza', 'from_market', '城前広場へ')
m.door('tr_r1_to_residential', 2200, 3088, 400, 64, 'royal_capital_03_residential', 'from_market', '住宅街へ')
m.npc('r1_general', '雑貨商（ショップ）', 700, 980, 'shop', shop='royal_general'); m.npc('r1_weapon', '武具商（ショップ）', 4000, 980, 'shop', shop='royal_arms')
m.npc('r1_board', '依頼掲示板', 2000, 1500, 'quest'); m.npc('r1_rumor', '噂好きの商人', 1900, 2250, 'npc', walk=[[80, 0], [0, 0]]); m.npc('r1_child', '走り回る子ども', 3200, 1500, 'npc', walk=[[120, 0], [120, 60], [0, 60]]); m.npc('r1_inn', '宿屋の呼び込み', 2800, 1500, 'npc')
m.chest('tr_r1_alley', 380, 2800, 'common', '路地裏の箱（仮）')
maps.append(m)
# 2) 城前広場
m = Map('royal_capital_02_castle_plaza', '王都　城前広場', 'Royal Capital Castle Plaza', '城前広場', 4000, 3600, '王都', 'Royal Capital', '#c4bba3', '#8a8f78')
m.floor_rect(200, 200, 3600, 3200)
m.solid(1000, 200, 2000, 900, 'castle'); m.prop('town_castle_front', 2000, 1106); m.floor_rect(1800, 1100, 400, 120, '#c9b27a')     # 城 + 城門前の階段
m.floor_rect(1840, 1100, 320, 1100, '#cdbf9c', 'cobble')                                       # 城門から噴水への参道
for y in range(1300, 2100, 200): m.deco('town_banner_pole', 1760, y, 18, 12); m.deco('town_banner_pole', 2240, y, 18, 12)
for (x0, nm) in ((200, 0), (3000, 1)):   # 城の左右の家並み（2軒ずつ）
    for k, (hx, hv) in enumerate(((x0 + 10, 'a'), (x0 + 390, 'b'))): m.solid(hx, 540, 420, 360, 'house'); m.prop('town_house_town_' + hv, hx + 210, 906)
    for x in range(x0 + 40, x0 + 800, 160): m.deco('town_tree_pine', x, 400, 24, 14)
m.solid(1850, 1900, 300, 300, 'fountain'); m.prop('town_fountain', 2000, 2192)                  # 噴水
for (x, y) in ((1500, 1900), (2500, 1900), (1500, 2500), (2500, 2500)): m.deco('town_flowerbed', x, y, 100, 26)
for (x, y) in ((1380, 2150), (2620, 2150)): m.deco('town_bench_stone', x, y, 56, 18)
for y in (1400, 2000, 2600, 3200): m.deco('town_lamp_post', 1660, y, 14, 10); m.deco('town_lamp_post', 2340, y, 14, 10)
for (x, y) in ((420, 1300), (420, 2900), (3580, 1300), (3580, 2900), (900, 3200), (3100, 3200)): m.deco('town_tree_oak', x, y, 28, 16)
m.deco('town_hedge_long', 700, 2100, 170, 24); m.deco('town_hedge_long', 3300, 2100, 170, 24)
m.spawn('from_market', 360, 1700, 'right'); m.spawn('from_residential', 2000, 3300, 'up'); m.spawn('from_castle', 2000, 1260, 'down')
m.door('tr_r2_to_market', 48, 1500, 64, 400, 'royal_capital_01_market', 'from_plaza', '商業区へ')
m.door('tr_r2_to_residential', 1800, 3488, 400, 64, 'royal_capital_03_residential', 'from_plaza', '住宅街へ')
m.door('tr_r2_castle_gate', 1800, 1100, 400, 60, 'TBD', 'TBD', '王城の中へ。接続は未実装')
m.npc('r2_guard', '城門の衛兵', 1650, 1300, 'npc', walk=[[0, 70], [0, 0]]); m.npc('r2_bard', '広場の吟遊詩人', 1500, 2400, 'npc'); m.npc('r2_herald', '触れ役', 2300, 2600, 'quest', walk=[[-70, 0], [0, 0]]); m.chest('tr_r2_garden', 3500, 3000, 'uncommon', '花壇の脇の箱（仮）')
maps.append(m)
# 3) 住宅街
m = Map('royal_capital_03_residential', '王都　住宅街', 'Royal Capital Residential Quarter', '住宅街', 3600, 3200, '王都', 'Royal Capital', '#aaa28c', '#8a8f78')
m.floor_rect(200, 200, 3200, 2800, '#bdb29a', 'cobble')
houses = [(400, 500), (1000, 500), (1600, 500), (2600, 500), (400, 1500), (1000, 1500), (2600, 1500), (400, 2400), (1000, 2400), (2600, 2400)]
for i, (x, y) in enumerate(houses):
    m.solid(x, y, 420, 360, 'house'); m.prop('town_house_town_' + 'abc'[i % 3], x + 210, y + 370); m.floor_rect(x + 160, y + 360, 100, 60, '#c9b27a')
    m.zones.append({'id': 'ev_door_%02d' % i, 'type': 'interact', 'textId': 'msg_house_locked', 'shape': {'shape': 'circle', 'cx': x + 210, 'cy': y + 400, 'r': 70}})
m.deco('town_well', 1800, 1500, 70, 30)
for (x, y) in ((1300, 1300), (2300, 1300), (1300, 1950), (2300, 1950)): m.deco('town_flowerbed', x, y, 100, 26)
for (x, y) in ((1250, 2250), (2200, 2250), (1900, 960)): m.deco('town_tree_oak', x, y, 28, 16)
for (x, y) in ((900, 1260), (2120, 1260), (1650, 2220)): m.deco('town_bush_round', x, y, 40, 20)
for (x, y) in ((1500, 330), (1500, 1250), (1500, 2250), (2400, 1250), (3050, 1250)): m.deco('town_lamp_post', x, y, 14, 10)
m.deco('town_bench_stone', 2000, 1800, 56, 18); m.deco('town_cart', 3000, 1000, 120, 30); m.deco('town_hedge_long', 3000, 2750, 170, 24)
m.deco('furn_barrel', 3100, 2400, 36, 24); m.deco('furn_crate', 3180, 2430, 44, 26)
m.spawn('from_market', 1700, 360, 'down'); m.spawn('from_plaza', 3300, 1500, 'left')
m.door('tr_r3_to_market', 1500, 48, 600, 64, 'royal_capital_01_market', 'from_residential', '商業区へ')
m.door('tr_r3_to_plaza', 3488, 1300, 64, 400, 'royal_capital_02_castle_plaza', 'from_residential', '城前広場へ')
m.npc('r3_resident', '住民', 1800, 1500, 'npc', walk=[[70, 40], [0, 0]]); m.npc('r3_cat_man', '猫に餌をやる男', 3250, 2050, 'npc', walk=[[-50, 0], [0, 0]]); m.npc('r3_elder_quest', '依頼人の老婦人', 1500, 2700, 'quest'); m.chest('tr_r3_backyard', 2400, 2900, 'common', '裏庭の箱（仮）')
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
