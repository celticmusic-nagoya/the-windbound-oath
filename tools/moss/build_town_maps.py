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
        s.region = (region_ja, region_en); s.rects = []; s.fills = []; s.spawns = {}; s.trans = []; s.nodes = []; s.tre = []; s.props = []; s.walkers = []; s.zones = []; s.paths = []
        s.floor = floor; s.ground = ground; s.bgm = bgm; s.seq = 0; s.wind = 0.2; s.card_area = None
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
            'r2_guard': 'guard', 'r2_bard': 'bard', 'r2_herald': 'soldier', 'r3_resident': 'townswoman', 'f4_liam': 'liam', 'f4_dwarf': 'dwarf_drunk', 'g_gate_guard': 'guard', 'g_merchant': 'merchant', 'g_pilgrim': 'townswoman', 'g_adv': 'townsman', 'g_reception': 'townswoman', 'g_barkeep': 'barkeep', 'g_patron1': 'townsman', 'g_patron2': 'townswoman', 'g_bard': 'bard', 'in_bed': 'bed', 'in_guest': 'townsman', 'f4_barkeep': 'barkeep', 'f4_patron1': 'townsman', 'f4_patron2': 'townswoman', 'f4_bard': 'bard', 'rd_traveler': 'merchant', 'rd_patrol': 'soldier', 'r3_cat_man': 'elder', 'r3_elder_quest': 'questgiver'}
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
        card = {'regionJa': s.region[0], 'regionEn': s.region[1], 'areaJa': s.card_area or s.area_ja, 'areaEn': s.en, 'triggerZone': 'ev_arrival'}
        zones = [{'id': 'ev_arrival', 'type': 'locationCard', 'shape': {'shape': 'rect', 'x': s.spawns[first]['x'] - 150, 'y': s.spawns[first]['y'] - 150, 'w': 300, 'h': 300}, 'once': True}] + s.nodes + s.zones
        return {'schemaVersion': 2, 'id': s.id, 'region': s.region[1].lower().replace(' ', '_'), 'areaIndex': 1,
                'displayName': {'ja': s.ja, 'en': s.en}, 'locationCard': card, 'world': {'width': float(s.w), 'height': float(s.h), 'tile': 8, 'unitScale': 2.5},
                'layers': ['GROUND', 'GROUND_DETAIL', 'LOWER_PROP', 'ACTOR', 'UPPER_FOLIAGE', 'FOREGROUND'],
                'spawns': {'default': first, 'points': s.spawns},
                'terrain': {'base': {'tiles': ['gnd_grass_sunny_01', 'gnd_grass_sunny_02'], 'surface': 'grass', 'seed': zlib.crc32(s.id.encode()) % 9000}, 'baseColor': s.ground,
                            'patches': [], 'openAreas': [], 'paths': s.paths, 'waters': [], 'cliffs': [],
                            'fills': [dict({'id': 'fill_%d' % i, 'color': k[0], 'rects': r}, **({'pattern': k[1]} if k[1] else {})) for i, (k, r) in enumerate(order)]},
                'props': s.props, 'walkers': s.walkers, 'scatter': [], 'effects': [],
                'collision': {'bounds': {'x': 0, 'y': 0, 'w': float(s.w), 'h': float(s.h)}, 'edgeBlockers': edges, 'blockers': blockers, 'presets': {}},
                'transitions': s.trans, 'encounterZones': [], 'treasurePoints': s.tre, 'eventZones': zones, 'cameraFocus': [],
                'ambience': {'grade': {'id': 'town_day', 'tint': '#FFF2D0', 'tintStrength': 0.04, 'brightness': 1.02, 'saturation': 1.0},
                             'shadow': {'dir': [0.55, 0.83], 'alpha': 0.2}, 'wind': {'strength': s.wind, 'dirDeg': 60, 'gustPeriodSec': [6, 10], 'targets': {}}},
                'particles': [], 'audio': {'bgm': {'id': s.bgm, 'fadeInSec': 1.0}, 'layers': [], 'hooks': []},
                'taint': {'baseLevel': 0, 'maxCoverageRatio': 0.0, 'palette': {'crack': '#120A1F', 'glow': '#8A4DFF'}, 'spots': []},
                'debug': {'showCollision': False, 'showPaths': False, 'showZones': False},
                'timeOfDay': {'default': 'day'}, **({'weather': WEATHER[s.id]} if s.id in WEATHER else {}), 'story': {'placeholder': True, 'note': '基礎構造のみ（見た目は仮）。物語への接続は未実装'},
                'culling': {'chunk': 256, 'margin': 1, 'maxLiveNodes': 800, 'viewportWorst': [1920, 1080], 'scatterRender': 'chunkLayer'}}

STONE, DARK, ROOF, WOOD = '#9a968a', '#5b5561', '#8a4f3c', '#7a5a3a'
maps = []

# ---------------- ドゥンヴァル砦 ----------------------------------------------------------------------
# 1) 中庭（外門・城壁・見張り塔・主塔の扉・城壁階段）
m = Map('fort_dunvall_01_courtyard', 'ドゥンヴァル砦　中庭', 'Dunvar Fortress Courtyard', '中庭', 3200, 2400, 'ドゥンヴァル砦', 'DUNVAR FORTRESS', STONE, '#6f8a4a')
m.prop('town_fort_ridge', 1600, 215, ['deco'], z=0)                                # 山岳と滝（城壁の向こう）
m.wind = 0.3
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
m.deco('town_tree_oak', 2640, 700, 30, 18)
m.solid(600, 1500, 400, 200, 'barracks'); m.prop('town_barracks', 800, 1706); m.solid(2200, 1500, 400, 200, 'stable'); m.prop('town_stable', 2400, 1706)
m.solid(480, 560, 460, 340, 'tavern'); m.prop('town_tavern_front', 710, 906); m.spawn('from_tavern', 710, 990, 'down'); m.spawn('from_road', 1600, 2300, 'up'); m.spawn('from_capital_road', 3050, 1200, 'left'); m.spawn('from_ramparts', 480, 1100, 'right'); m.spawn('from_keep', 1600, 1080, 'down')
m.door('tr_f1_to_village', 1380, 2288, 440, 64, 'lind_village', 'from_fort', '南門 -> 街道 -> リルド村（story hook onVillageExit）')
m.door('tr_f1_to_capital', 3040, 1100, 100, 200, 'road_dunvall_capital_01', 'from_fort', '東門 -> 街道 -> 王都')
m.door('tr_f1_to_ramparts', 360, 1000, 80, 220, 'fort_dunvall_02_ramparts', 'from_courtyard', '城壁への階段')
m.door('tr_f1_to_keep', 1500, 960, 200, 60, 'fort_dunvall_03_keep', 'from_courtyard', '主塔の扉'); m.door('tr_f1_to_tavern', 650, 906, 120, 70, 'fort_in_tavern', 'from_courtyard', '酒場「錆びた角笛」の扉')
m.npc('f1_captain', '砦の隊長', 1600, 1300, 'quest'); m.npc('f1_quartermaster', '補給係（武具屋）', 1000, 1800, 'shop'); m.npc('f1_bed', '兵舎の仮眠所', 800, 1760, 'bed', rest=True); m.npc('f1_gate_guard', '門番', 1250, 2050, 'npc', walk=[[0, -60], [0, 0]])
m.chest('tr_f1_barracks', 640, 1760, 'common', '兵舎の脇の箱（仮）')
maps.append(m)
# 2) 城壁の上（ぐるりと一周する歩廊・見張り台）
m = Map('fort_dunvall_02_ramparts', 'ドゥンヴァル砦　城壁', 'Dunvar Fortress Ramparts', '城壁の上', 2800, 1600, 'ドゥンヴァル砦', 'DUNVAR FORTRESS', '#a8a294', '#4a6a8a')
m.prop('town_fort_ridge', 1400, 200, ['deco'], z=0); m.wind = 0.35
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
m = Map('fort_dunvall_03_keep', 'ドゥンヴァル砦　主塔', 'Dunvar Fortress Keep', '主塔の内部', 2400, 1800, 'ドゥンヴァル砦', 'DUNVAR FORTRESS', '#8c7f6a', '#2b2830', 'bgm_fort_interior')
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
m = Map('royal_capital_01_market', '王都　商業区', 'Royal Capital Market District', '商業区', 4800, 3200, '王都カエルディン', 'CAERDYN', '#b5ad98', '#8a8f78')
m.wind = 0.06; m.floor_rect(200, 200, 4400, 2800)
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
m.spawn('from_gate', 2400, 2850, 'up'); m.spawn('from_plaza', 2400, 360, 'down'); m.spawn('from_residential', 360, 1500, 'right'); m.spawn('from_craft', 4400, 1500, 'left')   # from_craft: 職人地区から戻る位置
m.door('tr_r1_to_gate', 2200, 3088, 400, 64, 'royal_capital_00_gate', 'from_market', '南へ: 旅人街 -> 南大城門')
m.door('tr_r1_to_plaza', 2200, 48, 400, 64, 'royal_capital_02_castle_plaza', 'from_market', '北へ: 中央広場（王城への軸）')
m.door('tr_r1_to_residential', 48, 1300, 64, 400, 'royal_capital_03_residential', 'from_market', '西へ: 住宅地区')
m.door('tr_r1_to_craft', 4688, 1300, 64, 400, 'TBD', 'TBD', '東へ: 職人地区（ブラムの工房）。接続は未実装')
m.npc('r1_general', '雑貨商（ショップ）', 700, 980, 'shop', shop='royal_general'); m.npc('r1_weapon', '武具商（ショップ）', 4000, 980, 'shop', shop='royal_arms')
m.npc('r1_rumor', '噂好きの商人', 1900, 2250, 'npc', walk=[[80, 0], [0, 0]]); m.npc('r1_child', '走り回る子ども', 3200, 1500, 'npc', walk=[[120, 0], [120, 60], [0, 60]])
m.chest('tr_r1_alley', 380, 2800, 'common', '路地裏の箱（仮）')
maps.append(m)
# 2) 城前広場
m = Map('royal_capital_02_castle_plaza', '王都　城前広場', 'Royal Capital Castle Plaza', '城前広場', 4000, 3600, '王都カエルディン', 'CAERDYN', '#c4bba3', '#8a8f78')
m.wind = 0.12; m.floor_rect(200, 200, 3600, 3200)
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
m.deco('town_monument', 1480, 1720, 36, 18); m.deco('town_monument', 2520, 1720, 36, 18)   # 建国記念碑（参道の両脇に）
m.deco('town_hedge_long', 700, 2100, 170, 24); m.deco('town_hedge_long', 3300, 2100, 170, 24)
m.spawn('from_market', 2000, 3300, 'up'); m.spawn('from_residential', 360, 1700, 'right'); m.spawn('from_castle', 2000, 1260, 'down'); m.spawn('from_east', 3640, 1700, 'left')   # from_east: 騎士団/大聖堂/学術地区から戻る位置
m.door('tr_r2_to_residential', 48, 1500, 64, 400, 'royal_capital_03_residential', 'from_plaza', '西へ: 住宅地区')
m.door('tr_r2_to_market', 1800, 3488, 400, 64, 'royal_capital_01_market', 'from_plaza', '南へ: 商業・市場地区')
m.door('tr_r2_to_east', 3888, 1500, 64, 400, 'TBD', 'TBD', '東へ: 騎士団地区・大聖堂地区・魔法学術地区（王立魔法研究院）。接続は未実装')
m.door('tr_r2_castle_gate', 1800, 1100, 400, 60, 'TBD', 'TBD', '王城の中へ。接続は未実装')
m.npc('r2_guard', '城門の衛兵', 1650, 1300, 'npc', walk=[[0, 70], [0, 0]]); m.npc('r2_bard', '広場の吟遊詩人', 1500, 2400, 'npc'); m.npc('r2_herald', '触れ役', 2300, 2600, 'quest', walk=[[-70, 0], [0, 0]]); m.chest('tr_r2_garden', 3500, 3000, 'uncommon', '花壇の脇の箱（仮）')
maps.append(m)
# 3) 住宅街
m = Map('royal_capital_03_residential', '王都　住宅街', 'Royal Capital Residential Quarter', '住宅街', 3600, 3200, '王都カエルディン', 'CAERDYN', '#aaa28c', '#8a8f78')
m.wind = 0.05; m.floor_rect(200, 200, 3200, 2800, '#bdb29a', 'cobble')
houses = [(400, 500), (1000, 500), (1600, 500), (2600, 500), (400, 1500), (1000, 1500), (2600, 1500), (400, 2400), (1000, 2400), (2600, 2400)]
for i, (x, y) in enumerate(houses):
    m.solid(x, y, 420, 360, 'house'); m.prop('town_house_town_' + 'abc'[i % 3], x + 210, y + 370); m.floor_rect(x + 160, y + 360, 100, 60, '#c9b27a')
    m.zones.append({'id': 'ev_door_%02d' % i, 'type': 'interact', 'textId': 'msg_house_locked', 'shape': {'shape': 'circle', 'cx': x + 210, 'cy': y + 400, 'r': 70}})
m.deco('town_well', 1800, 1750, 70, 30)
for (x, y) in ((1300, 1300), (2300, 1300), (1300, 1950), (2300, 1950)): m.deco('town_flowerbed', x, y, 100, 26)
for (x, y) in ((1250, 2250), (2200, 2250), (1900, 960)): m.deco('town_tree_oak', x, y, 28, 16)
for (x, y) in ((900, 1260), (2120, 1260), (1650, 2220)): m.deco('town_bush_round', x, y, 40, 20)
for (x, y) in ((1500, 330), (1500, 1250), (1500, 2250), (2400, 1250), (3050, 1250)): m.deco('town_lamp_post', x, y, 14, 10)
m.deco('town_bench_stone', 2000, 1800, 56, 18); m.deco('town_cart', 3000, 1000, 120, 30); m.deco('town_hedge_long', 3000, 2750, 170, 24)
m.deco('furn_barrel', 3100, 2400, 36, 24); m.deco('furn_crate', 3180, 2430, 44, 26)
m.spawn('from_market', 360, 1200, 'right'); m.spawn('from_plaza', 3300, 1500, 'left')
m.door('tr_r3_to_market', 48, 1000, 64, 400, 'royal_capital_01_market', 'from_residential', '東へ: 商業・市場地区')
m.door('tr_r3_to_plaza', 3488, 1300, 64, 400, 'royal_capital_02_castle_plaza', 'from_residential', '城前広場へ')
m.npc('r3_resident', '住民', 1800, 1500, 'npc', walk=[[70, 40], [0, 0]]); m.npc('r3_cat_man', '猫に餌をやる男', 3250, 2050, 'npc', walk=[[-50, 0], [0, 0]]); m.npc('r3_elder_quest', '依頼人の老婦人', 1500, 2700, 'quest'); m.chest('tr_r3_backyard', 2400, 2900, 'common', '裏庭の箱（仮）')
maps.append(m)

# ---------------- 街道（ドゥンヴァル砦 ↔ 王都）・砦の酒場 --------------------------------------------------
import math, random
# 1) 街道: 西（砦の東門）から東（王都の西門）へ。終盤の丘（高台）に着くと谷の向こうの王都が一望できる。
m = Map('road_dunvall_capital_01', '街道　砦と王都のあいだ', 'Road to Caerdyn', '街道', 5600, 2600, '辺境', 'Marches', '#b7a888', '#7d9a58', 'bgm_town')
ROAD = [(120, 1900), (900, 1850), (1500, 2000), (2200, 1900), (2800, 1500), (3300, 1250), (3560, 1000), (3800, 880), (4260, 900), (4700, 1400), (5100, 1750), (5480, 1800)]
m.paths.append({'id': 'dunvall-road', 'points': [list(p) for p in ROAD], 'width': 150})
def near_road(x, y, pad=150):
    for (a, b) in zip(ROAD, ROAD[1:]):
        ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L2)); px, py = ax + t * dx, ay + t * dy
        if math.hypot(x - px, y - py) < pad: return True
    return False
rnd = random.Random(7)
m.solid(48, 48, 3852, 512, 'forest'); m.solid(3900, 48, 1652, 640, 'valley')                      # 北の森 / 谷と川（王都は対岸）
m.floor_rect(3900, 520, 1652, 170, '#4a86a6', None)                                                # 川
m.floor_rect(3450, 700, 780, 340, '#93aa66', None)                                                 # 丘の頂（高台）
m.solid(3640, 1030, 600, 44, 'cliff'); m.solid(4230, 700, 36, 150, 'cliff'); m.solid(4230, 950, 36, 90, 'cliff')   # 丘の崖（西側と東の出口は開いている）
m.floor_rect(3640, 1030, 600, 44, '#7c7a6e', 'brick'); m.floor_rect(4230, 700, 36, 150, '#7c7a6e', 'brick'); m.floor_rect(4230, 950, 36, 90, '#7c7a6e', 'brick')
m.solid(48, 2300, 5504, 252, 'forest')                                                              # 南の森
m.prop('town_capital_far', 4750, 506, ['deco'], z=2)                                                # 対岸の王都（遠景）
for x in range(60, 3880, 118):                                                                      # 北の森の木々（コリジョンは森ブロック）
    for k, y in enumerate((300, 430, 540)): m.prop('town_tree_pine' if (x // 118 + k) % 2 else 'town_tree_oak', x + rnd.randint(-20, 20) + k * 40, y + rnd.randint(-14, 14))
for x in range(60, 5500, 118):
    for k, y in enumerate((2380, 2500)): m.prop('town_tree_pine' if (x // 118 + k) % 3 else 'town_tree_oak', x + rnd.randint(-20, 20) + k * 40, y + rnd.randint(-14, 14))
for _ in range(90):                                                                                 # 道ばたの木・茂み
    x, y = rnd.randint(120, 5400), rnd.randint(620, 2260)
    if near_road(x, y, 190) or (3400 < x < 4300 and 650 < y < 1100) or m.__dict__.get('_dummy'): continue
    if any(r[0] - 30 <= x <= r[0] + r[2] + 30 and r[1] - 30 <= y <= r[1] + r[3] + 30 for r in m.rects): continue
    m.deco(rnd.choice(['town_tree_oak', 'town_tree_pine', 'town_bush_round', 'town_bush_round']), x, y, 28, 16)
m.spawn('from_fort', 200, 1900, 'right'); m.spawn('from_capital', 5400, 1800, 'left'); m.spawn('overlook', 3800, 900, 'right')
m.door('tr_rd_to_fort', 48, 1750, 64, 300, 'fort_dunvall_01_courtyard', 'from_capital_road', '街道の西端 -> ドゥンヴァル砦の東門')
m.door('tr_rd_to_capital', 5488, 1650, 64, 300, 'royal_capital_00_gate', 'from_road', '街道の東端 -> 王都の南大城門')
m.prop('prop_marker_signpost', 330, 1800); m.rects.append((312, 1786, 36, 14, 'sign')); m.prop('prop_marker_signpost', 5240, 1700); m.rects.append((5222, 1686, 36, 14, 'sign'))
m.deco('prop_bench_view', 3960, 860, 70, 18); m.deco('town_lamp_post', 3560, 840, 14, 10); m.deco('town_banner_pole', 3700, 780, 18, 12); m.deco('town_banner_pole', 3980, 760, 18, 12)
m.deco('town_cart', 1900, 1740, 120, 30); m.deco('town_hay_stack', 2500, 2050, 120, 40); m.deco('town_flowerbed', 4400, 1500, 100, 26)
m.zones.append({'id': 'ev_overlook', 'type': 'trigger', 'hook': 'road_overlook', 'shape': {'shape': 'rect', 'x': 3700, 'y': 780, 'w': 320, 'h': 230}, 'once': True})
m.zones.append({'id': 'ev_overlook_view', 'type': 'interact', 'hook': 'road_overlook_again', 'label': '谷の向こうの王都', 'shape': {'shape': 'circle', 'cx': 3960, 'cy': 830, 'r': 90}})
m.npc('rd_gate_guard', '王都の門衛', 5330, 1700, 'npc'); m.npc('rd_traveler', '旅の商人', 2150, 1980, 'npc', walk=[[90, 0], [0, 0]]); m.npc('rd_patrol', '巡回の兵士', 800, 1780, 'npc')
maps.append(m)
# 2) 砦の酒場「錆びた角笛」: リアム加入イベント
m = Map('fort_in_tavern', 'ドゥンヴァル砦　酒場「錆びた角笛」', 'Dunvar Fortress Tavern', '酒場', 1400, 1000, 'ドゥンヴァル砦', 'DUNVAR FORTRESS', '#a98b5c', '#17110d', 'bgm_fort_interior')
m.floor_rect(0, 0, 1400, 1000, '#17110d', None); m.floor_rect(48, 248, 1304, 704, '#a98b5c', 'planks'); m.wall(48, 48, 1304, 200, '#76654f', 'wall', 'planks')
m.floor_rect(560, 880, 280, 72, '#b89a68', 'planks')
m.spawn('from_courtyard', 700, 830, 'up')
m.door('tr_in_tavern_exit', 630, 880, 140, 64, 'fort_dunvall_01_courtyard', 'from_tavern', '外へ出る')
m.decal('furn_doormat', 700, 920); m.decal('furn_rug_red', 520, 640)
m.deco('furn_fireplace', 330, 252, 140, 40); m.prop('furn_window_wall', 560, 252, ['deco']); m.prop('furn_tapestry', 820, 252, ['deco'])
for x in (980, 1180): m.deco('furn_counter_inn', x, 470, 224, 56)                                    # カウンター
for x in (1010, 1160): m.deco('furn_shelf_pots', x, 268, 90, 20)
m.deco('furn_barrel', 1290, 330, 40, 24); m.deco('furn_barrel', 1290, 400, 40, 24); m.deco('furn_crates_stack', 100, 400, 60, 30)
for (x, y) in ((420, 720), (780, 740), (640, 520)): m.deco('furn_table_round', x, y, 110, 40); m.deco('furn_stool', x - 80, y + 14, 28, 14); m.deco('furn_stool', x + 80, y + 14, 28, 14)
m.deco('furn_table_small', 150, 560, 90, 36); m.deco('furn_chair', 150, 640, 36, 18); m.deco('furn_candle_stand', 230, 520, 24, 12)
m.deco('furn_bench', 1100, 760, 110, 24); m.deco('furn_map_table', 1000, 640, 110, 40)
m.npc('f4_liam', 'リアム', 170, 560, 'npc'); m.nodes[-1]['requires'] = {'flag': 'liam_joined', 'is': False}; m.props[-1]['hideIf'] = 'liam_joined'
m.npc('f4_barkeep', '酒場の主人', 1090, 400, 'npc'); m.nodes[-1]['shape'].update(cy=478, r=110);   # counter in front: the zone reaches over it
m.npc('f4_dwarf', '酔っ払いのドワーフ', 960, 900, 'npc'); m.deco('furn_crate', 1050, 930, 44, 26); m.deco('furn_barrel', 880, 930, 36, 24)
m.npc('f4_patron1', '常連の男', 480, 640, 'npc'); m.npc('f4_patron2', '旅の女', 860, 680, 'npc'); m.npc('f4_bard', '吟遊詩人', 300, 820, 'npc')
maps.append(m)


# ---------------- 王都カエルディン: 南大城門・旅人街 + ギルド/宿屋の内部 (Bible 12-17: 南大城門 -> 旅人街 -> 市場 -> 中央広場 -> 王城) ----------------------
CAER = ('王都カエルディン', 'CAERDYN')
m = Map('royal_capital_00_gate', '王都カエルディン　南大城門・旅人街', 'Caerdyn South Great Gate', '南大城門', 4400, 3400, CAER[0], CAER[1], '#bdb6a4', '#8a9a78')
m.card_area = '南大城門　CAERDYN'; m.wind = 0.08
m.floor_rect(200, 200, 4000, 2960); m.floor_rect(1840, 200, 520, 3000, '#c7bda2', 'cobble'); m.floor_rect(1700, 1880, 800, 760, '#c7bda2', 'cobble')
for (gy, nm) in ((2800, 'outer'), (1900, 'inner')):                # 巨大な二重城門
    m.wall(48, gy - 160, 1250, 160, '#c8c2b4'); m.wall(3100, gy - 160, 1252, 160, '#c8c2b4')
    m.solid(1300, gy - 160, 760, 160, 'gate'); m.solid(2340, gy - 160, 760, 160, 'gate'); m.prop('town_caer_gate', 2200, gy)
    for x in range(100, 1300, 200): m.prop('town_battlement', x + 100, gy - 150); m.prop('town_battlement', x + 3100 - 100 + 100 - 100, gy - 150)
m.floor_rect(1840, 2640, 520, 160, '#9a9488', 'cobble'); m.floor_rect(1840, 1740, 520, 160, '#9a9488', 'cobble')
m.deco('town_checkpoint', 1700, 2420, 150, 40); m.deco('town_checkpoint', 2700, 2420, 150, 40)   # 検問所
m.deco('town_cart', 1250, 2380, 120, 30); m.deco('town_cart', 3050, 2300, 120, 30); m.deco('town_cart', 3500, 2400, 120, 30)
m.deco('furn_barrel', 1450, 2230, 36, 24); m.deco('furn_crates_stack', 3300, 2200, 60, 30); m.deco('furn_sacks_pile', 900, 2250, 50, 26)
for x in (1760, 2640): m.deco('town_banner_pole', x, 2980, 18, 12); m.deco('town_torch_post', x + (-60 if x < 2200 else 60), 2990, 20, 14)
for (x, y) in ((500, 3100), (1000, 3180), (3400, 3160), (3900, 3100), (300, 2500), (4100, 2500)): m.deco('town_tree_oak' if (x // 100) % 2 else 'town_tree_pine', x, y, 28, 16)
# 旅人街（北側）: 冒険者ギルド兼大酒場（西） / 宿屋（東）
m.solid(720, 640, 360, 360, 'guild'); m.prop('town_guild_front', 900, 1000); m.floor_rect(840, 1000, 120, 70, '#c9b27a', 'planks'); m.spawn('from_guild', 900, 1090, 'down')
m.solid(3350, 660, 300, 340, 'inn'); m.prop('town_inn_front', 3500, 1000); m.floor_rect(3440, 1000, 120, 70, '#c9b27a', 'planks'); m.spawn('from_inn', 3500, 1090, 'down')
for (x, v) in ((400, 'a'), (1500, 'b'), (2900, 'c'), (4000, 'a')): m.solid(x - 210, 160, 420, 360, 'house'); m.prop('town_house_town_' + v, x, 526)
for y in range(1260, 1800, 260): m.deco('town_lamp_post', 1790, y, 14, 10); m.deco('town_lamp_post', 2410, y, 14, 10)
for y in (700, 1300): m.deco('town_banner_pole', 1800, y, 18, 12); m.deco('town_banner_pole', 2400, y, 18, 12)
m.deco('town_well', 1300, 1500, 70, 30); m.deco('town_flowerbed', 3000, 1400, 100, 26); m.deco('town_bench_stone', 1650, 1300, 56, 18); m.deco('town_bench_stone', 2550, 1300, 56, 18)
m.deco('town_cart', 700, 1500, 120, 30); m.deco('furn_barrel', 3100, 1100, 36, 24); m.deco('town_hay_stack', 3800, 1500, 120, 40)
m.spawn('from_road', 2200, 3250, 'up'); m.spawn('from_market', 2200, 360, 'down'); m.spawn('from_gate_inside', 2200, 1650, 'up')
m.door('tr_g_to_road', 1840, 3288, 520, 64, 'road_dunvall_capital_01', 'from_capital', '南大城門の外 -> 街道 -> ドゥンヴァル砦')
m.door('tr_g_to_market', 1840, 48, 520, 64, 'royal_capital_01_market', 'from_gate', '北へ: 商業・市場地区（王城への軸）')
m.door('tr_g_to_guild', 840, 1000, 120, 60, 'royal_in_guild', 'from_gate', '冒険者ギルド兼大酒場')
m.door('tr_g_to_inn', 3440, 1000, 120, 60, 'royal_in_inn', 'from_gate', '宿屋')
m.npc('g_gate_guard', '門番（騎士団）', 2120, 2560, 'npc', walk=[[0, -50], [0, 0]]); m.npc('g_merchant', '荷馬車の商人', 1250, 2470, 'npc'); m.npc('g_pilgrim', '巡礼者', 2500, 1450, 'npc', walk=[[-70, 0], [0, 0]])
m.npc('g_adv', '駆け出しの冒険者', 1000, 1250, 'npc', walk=[[90, 0], [0, 0]])
m.chest('tr_g_cart', 3400, 2550, 'common', '荷馬車の脇の箱（仮）')
maps.append(m)
# ギルド兼大酒場（1階: 大酒場・依頼掲示板・受付。2階=会議室 / 地下=倉庫 は今後）
m = Map('royal_in_guild', '冒険者ギルド兼大酒場', 'Adventurers\' Guild & Great Tavern', 'ギルド兼大酒場', 1800, 1100, CAER[0], CAER[1], '#a98b5c', '#17110d', 'bgm_fort_interior')
m.wind = 0.0
m.floor_rect(0, 0, 1800, 1100, '#17110d', None); m.floor_rect(48, 248, 1704, 804, '#a98b5c', 'planks'); m.wall(48, 48, 1704, 200, '#76654f', 'wall', 'planks')
m.floor_rect(760, 980, 280, 72, '#b89a68', 'planks')
m.spawn('from_gate', 900, 920, 'up')
m.door('tr_gi_exit', 780, 980, 240, 64, 'royal_capital_00_gate', 'from_guild', '外（旅人街）へ出る')
m.decal('furn_doormat', 900, 1020); m.decal('furn_rug_red', 640, 700)
m.deco('furn_fireplace', 330, 252, 140, 40); m.prop('furn_window_wall', 620, 252, ['deco']); m.prop('furn_tapestry', 900, 252, ['deco']); m.prop('furn_tapestry', 1560, 252, ['deco'])
for x in (1200, 1400): m.deco('furn_counter_inn', x, 470, 224, 56)
for x in (1240, 1400): m.deco('furn_shelf_pots', x, 268, 90, 20)
m.deco('furn_barrel', 1700, 330, 40, 24); m.deco('furn_barrel', 1700, 400, 40, 24); m.deco('furn_crates_stack', 100, 420, 60, 30)
for (x, y) in ((450, 760), (900, 700), (1300, 800)): m.deco('furn_table_round', x, y, 110, 40); m.deco('furn_stool', x - 80, y + 14, 28, 14); m.deco('furn_stool', x + 80, y + 14, 28, 14)
m.deco('furn_map_table', 800, 440, 110, 40); m.deco('furn_bench', 1600, 780, 110, 24)
m.npc('r1_board', '依頼掲示板', 520, 440, 'quest'); m.npc('g_reception', 'ギルドの受付', 1200, 400, 'npc'); m.nodes[-1]['shape'].update(cy=478, r=110)
m.npc('g_barkeep', '大酒場の主人', 1420, 400, 'npc'); m.nodes[-1]['shape'].update(cy=478, r=110)
m.npc('g_patron1', '依頼帰りの冒険者', 600, 700, 'npc'); m.npc('g_patron2', '酔った旅人', 1120, 760, 'npc'); m.npc('g_bard', '宴の吟遊詩人', 1600, 880, 'npc')
m.zones.append({'id': 'ev_upstairs', 'type': 'interact', 'npc': 'g_upstairs', 'label': '2階への階段', 'shape': {'shape': 'circle', 'cx': 180, 'cy': 330, 'r': 90}})
maps.append(m)
# 宿屋（ギルドの隣）: 回復・宿泊・セーブ関連。時間帯を選ぶ宿泊は今後
m = Map('royal_in_inn', '宿屋「旅人の灯」', 'Caerdyn Inn', '宿屋', 1400, 1000, CAER[0], CAER[1], '#a98b5c', '#17110d', 'bgm_fort_interior')
m.wind = 0.0
m.floor_rect(0, 0, 1400, 1000, '#17110d', None); m.floor_rect(48, 248, 1304, 704, '#b09468', 'planks'); m.wall(48, 48, 1304, 200, '#7d6c56', 'wall', 'planks')
m.floor_rect(560, 880, 280, 72, '#b89a68', 'planks')
m.spawn('from_gate', 700, 830, 'up')
m.door('tr_ii_exit', 630, 880, 140, 64, 'royal_capital_00_gate', 'from_inn', '外（旅人街）へ出る')
m.decal('furn_doormat', 700, 920); m.decal('furn_rug_red', 560, 620)
m.deco('furn_fireplace', 330, 252, 140, 40); m.prop('furn_window_wall', 600, 252, ['deco']); m.prop('furn_tapestry', 860, 252, ['deco'])
m.deco('furn_counter_inn', 1100, 470, 224, 56); m.deco('furn_shelf_pots', 1110, 268, 90, 20)
m.deco('furn_table_round', 560, 640, 110, 40); m.deco('furn_stool', 480, 654, 28, 14); m.deco('furn_stool', 640, 654, 28, 14); m.deco('furn_barrel', 1290, 380, 40, 24)
m.npc('r1_inn', '宿屋の主人', 1100, 400, 'npc'); m.nodes[-1]['shape'].update(cy=478, r=110)
m.npc('in_bed', '客室のベッド', 250, 560, 'bed', rest=True); m.npc('in_guest', '旅の客', 880, 700, 'npc')
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
        if t['toMap'] not in ('TBD', 'lind_village') and not any(o.id == t['toMap'] for o in maps):
            e = _disk_spawn(t['toMap'], t['toSpawn'])
            if e: errs.append('%s -> %s' % (t['id'], e))
        elif t['toMap'] not in ('TBD', 'lind_village'):
            tgt = next((o for o in maps if o.id == t['toMap']), None)
            if not tgt: errs.append('%s -> unknown map %s' % (t['id'], t['toMap']))
            elif t['toSpawn'] not in tgt.spawns: errs.append('%s -> %s has no spawn %s' % (t['id'], t['toMap'], t['toSpawn']))
    return errs, len(seen) * G * G / (W * H)

# ---- 未接続出口の差し込み: tools/moss/capital_exits.json (null = TBD のまま)
_EX = json.load(open(os.path.join(os.path.dirname(__file__), 'capital_exits.json'), encoding='utf-8'))
def _disk_spawn(mid, sp):
    f = os.path.join(OUT, mid + '.json')
    if not os.path.exists(f): return 'map file data/maps/%s.json not found' % mid
    if sp not in json.load(open(f, encoding='utf-8'))['spawns']['points']: return 'spawn %s not in %s' % (sp, mid)
    return None
_bad_exit = 0
for mp in maps:
    for t in mp.trans:
        c = _EX.get(t['id'])
        if t['toMap'] == 'TBD' and c:
            err = _disk_spawn(c['toMap'], c['toSpawn'])
            if err: print('capital_exits.json: %s -> %s' % (t['id'], err)); _bad_exit += 1
            else: t['toMap'], t['toSpawn'] = c['toMap'], c['toSpawn']; t['note'] += '（capital_exits.json で接続済み）'

bad = 0
for mp in maps:
    d = mp.doc(); errs, cov = validate(mp, d)
    json.dump(d, open(os.path.join(OUT, mp.id + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('%-34s %5dx%-5d walls=%-3d npc=%d chest=%d trans=%d walkable-reachable=%2.0f%% %s' % (mp.id, mp.w, mp.h, len(mp.rects), len([n for n in mp.nodes]), len(mp.tre), len(mp.trans), cov * 100, 'OK' if not errs else 'PROBLEMS'))
    for e in errs: print('   ', e); bad += 1
sys.exit(1 if (bad or _bad_exit) else 0)
