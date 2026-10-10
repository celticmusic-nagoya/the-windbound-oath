#!/usr/bin/env python3
"""Generate the Rilde Village maps for the Moss runtime (schema v2) and register their art in img/field/moss/manifest.json.
  outdoor : rilde_village_01_peace  /  rilde_village_01_ruin   (same geometry, spawns and exits; the ruin variant is the village after the attack)
  indoor  : rilde_in_aidan, rilde_in_elder, rilde_in_inn_1f, rilde_in_inn_2f, rilde_in_shop, rilde_in_house_01..04, rilde_in_barn, rilde_in_storage, rilde_in_trainshed
 The logical map id 'rilde_village' is resolved to peace/ruin by js/field/rilde-village.js (story state), so every door/exit just says toMap:'rilde_village'.
 Layout comes from the Lind village data (tools/moss/export_lind_layout.js); art from prepare_rilde_lind.py (village, ruins, villagers) and make_rilde_art.py (furniture, debris).
 usage: python3 tools/moss/prepare_rilde_lind.py && python3 tools/moss/make_rilde_art.py && python3 tools/moss/build_rilde_village.py   (exit 1 on validation problems)"""
import json, os, subprocess, sys, zlib, random
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT = os.path.join(ROOT, 'data', 'maps'); MAN = os.path.join(ROOT, 'img/field/moss/manifest.json')
LIND = json.loads(subprocess.check_output(['node', os.path.join(ROOT, 'tools/moss/export_lind_layout.js')]))
META = json.load(open(os.path.join(ROOT, 'tools/moss/rilde_assets.json'), encoding='utf-8'))
FURN = json.load(open(os.path.join(ROOT, 'tools/moss/rilde_furn.json'), encoding='utf-8'))
OX = OY = 100                      # Lind review canvas (2200x1550) -> map: 100px margin all round (+ the 48px edge blockers)
W, H = 2400, 1750
G = 32
OBJ = {o['id']: o for o in LIND['objects']}
EXTRA_COLL = {}

def r1(v): return round(v, 1)
def obj_rects(o):
    """Collision rects of a Lind object, absolute map coords."""
    out = []
    for c in ([o['collision']] if o.get('collision') else []) + (o.get('collisions') or []):
        out.append([r1(o['x'] + c[0] + OX), r1(o['y'] + c[1] + OY), c[2], c[3]])
    return out

# ------------------------------------------------------------------------------------------------ generic map container
class Room:
    def __init__(s, mid, ja, en, w, h, bgm, tod='day', interior=False, base='#17110d', weather=None):
        s.id, s.ja, s.en, s.w, s.h, s.bgm, s.tod, s.interior = mid, ja, en, w, h, bgm, tod, interior
        s.base = base; s.weather = weather
        s.rects = []; s.fills = []; s.spawns = {}; s.trans = []; s.zones = []; s.props = []; s.walkers = []; s.paths = []; s.waters = []; s.patches = []; s.vista = []; s.tre = []
        s.n = 0; s.notes = []
    def uid(s, p): s.n += 1; return '%s_%02d' % (p, s.n)
    def solid(s, x, y, w, h, tag='solid'): s.rects.append([r1(x), r1(y), r1(w), r1(h), tag])
    def fill(s, color, x, y, w, h, pattern=None, waves=False): s.fills.append((color, (pattern, waves), [r1(x), r1(y), r1(w), r1(h)]))
    def spawn(s, name, x, y, facing='down'): s.spawns[name] = {'x': r1(x), 'y': r1(y), 'facing': facing}
    def door(s, tid, x, y, w, h, to_map, to_spawn, note='', fade=.35):
        s.trans.append({'id': tid, 'rect': {'shape': 'rect', 'x': r1(x), 'y': r1(y), 'w': w, 'h': h}, 'toMap': to_map, 'toSpawn': to_spawn, 'fade': {'out': fade, 'in': fade}, 'enabled': True, 'note': note})
    def prop(s, asset, x, y, z=None, tags=None, pid=None):
        p = {'id': pid or s.uid('p'), 'asset': asset, 'x': r1(x), 'y': r1(y)}
        if z is not None: p['z'] = z
        if tags: p['tags'] = tags
        s.props.append(p); return p
    def interact(s, zid, x, y, r=80, **kw):
        z = {'id': zid, 'type': 'interact', 'shape': {'shape': 'circle', 'cx': r1(x), 'cy': r1(y), 'r': r}}; z.update(kw); s.zones.append(z); return z
    def vista_fire(s, x, y, w=150, h=170, seed=1, kind='fire_spot'): s.vista.append({'id': s.uid('fire'), 'kind': kind, 'x': r1(x - w / 2), 'y': r1(y - h), 'w': w, 'h': h, 'seed': seed, 'on': True})

    def doc(s):
        edge = 48
        edges = [{'shape': 'rect', 'x': 0, 'y': 0, 'w': s.w, 'h': edge}, {'shape': 'rect', 'x': 0, 'y': s.h - edge, 'w': s.w, 'h': edge}, {'shape': 'rect', 'x': 0, 'y': 0, 'w': edge, 'h': s.h}, {'shape': 'rect', 'x': s.w - edge, 'y': 0, 'w': edge, 'h': s.h}]
        blockers = [{'id': 'cb_%02d' % i, 'tag': t, 'shape': 'rects', 'rects': [[x, y, w, h]]} for i, (x, y, w, h, t) in enumerate(s.rects)]
        order = []
        for c, pt, r in s.fills:
            if not order or order[-1][0] != (c, pt): order.append([(c, pt), []])
            order[-1][1].append(r)
        first = 'default' if 'default' in s.spawns else next(iter(s.spawns))
        card = {'regionJa': 'リルド村', 'regionEn': 'Rilde Village', 'areaJa': s.ja, 'areaEn': s.en, 'triggerZone': 'ev_arrival'}
        sp = s.spawns[first]
        zones = [{'id': 'ev_arrival', 'type': 'locationCard', 'shape': {'shape': 'rect', 'x': sp['x'] - 120, 'y': sp['y'] - 120, 'w': 240, 'h': 240}, 'once': True}] + s.zones
        d = {'schemaVersion': 2, 'id': s.id, 'region': 'rilde_village', 'areaIndex': 1, 'displayName': {'ja': s.ja, 'en': s.en}, 'locationCard': card,
             'world': {'width': float(s.w), 'height': float(s.h), 'tile': 8, 'unitScale': 2.5},
             'layers': ['GROUND', 'GROUND_DETAIL', 'LOWER_PROP', 'ACTOR', 'UPPER_FOLIAGE', 'FOREGROUND'],
             'spawns': {'default': first, 'points': s.spawns},
             'terrain': {'base': {'tiles': ['gnd_grass_sunny_01', 'gnd_grass_sunny_02'], 'surface': 'grass', 'seed': zlib.crc32(s.id.encode()) % 9000}, 'baseColor': s.base,
                         'patches': s.patches, 'openAreas': [], 'paths': s.paths, 'waters': s.waters, 'cliffs': [],
                         'fills': [dict({'id': 'fill_%d' % i, 'color': k[0], 'rects': r}, **({'pattern': k[1][0]} if k[1][0] else {}), **({'waves': True} if k[1][1] else {})) for i, (k, r) in enumerate(order)]},
             'props': s.props, 'walkers': s.walkers, 'scatter': [], 'effects': [],
             'collision': {'bounds': {'x': 0, 'y': 0, 'w': float(s.w), 'h': float(s.h)}, 'edgeBlockers': edges, 'blockers': blockers, 'presets': {}},
             'transitions': s.trans, 'encounterZones': [], 'treasurePoints': s.tre, 'eventZones': zones, 'cameraFocus': [],
             'ambience': {'grade': {'id': 'rilde', 'tint': '#FFF2D0', 'tintStrength': .04, 'brightness': 1.02, 'saturation': 1.0}, 'shadow': {'dir': [.55, .83], 'alpha': .2}, 'wind': {'strength': .2, 'dirDeg': 60, 'gustPeriodSec': [6, 10], 'targets': {}}},
             'particles': [], 'audio': {'bgm': {'id': s.bgm, 'fadeInSec': 1.5}, 'layers': [], 'hooks': []},
             'taint': {'baseLevel': 0, 'maxCoverageRatio': 0.0, 'palette': {'crack': '#120A1F', 'glow': '#8A4DFF'}, 'spots': []},
             'debug': {'showCollision': False, 'showPaths': False, 'showZones': False},
             'timeOfDay': {'default': s.tod}, 'story': {'rilde': True, 'interior': s.interior},
             'culling': {'chunk': 256, 'margin': 1, 'maxLiveNodes': 900, 'viewportWorst': [1920, 1080], 'scatterRender': 'chunkLayer'}}
        if s.vista: d['vista'] = s.vista
        if s.weather: d['weather'] = s.weather
        return d

# ------------------------------------------------------------------------------------------------ outdoor village
BUILD = ['lind_elder_house', 'lind_inn', 'lind_aidan_house', 'lind_item_shop', 'lind_house_01', 'lind_house_02', 'lind_house_03', 'lind_house_04', 'lind_barn', 'lind_storage', 'train_shed']
DOOR = {   # logical room, spawn name, door dx from the building's centre, label
    'lind_aidan_house': ('rilde_in_aidan', 'from_aidan', 0, 'エイダンの家'), 'lind_elder_house': ('rilde_in_elder', 'from_elder', 0, '長老の家'), 'lind_inn': ('rilde_in_inn_1f', 'from_inn', 0, '宿屋「風見鶏」'),
    'lind_item_shop': ('rilde_in_shop', 'from_shop', 0, '道具屋「若葉の袋」'), 'lind_house_01': ('rilde_in_house_01', 'from_house_01', 0, '村人の家'), 'lind_house_02': ('rilde_in_house_02', 'from_house_02', 0, '村人の家'),
    'lind_house_03': ('rilde_in_house_03', 'from_house_03', 0, '村人の家'), 'lind_house_04': ('rilde_in_house_04', 'from_house_04', 0, '村人の家'), 'lind_barn': ('rilde_in_barn', 'from_barn', 0, '納屋'),
    'lind_storage': ('rilde_in_storage', 'from_storage', 0, '倉庫'), 'train_shed': ('rilde_in_trainshed', 'from_trainshed', 0, '見張り小屋')}
DECAL = {'train_ground', 'lind_bridge', 'lind_fishing_pier', 'lind_field_wheat', 'lind_field_vegetables', 'lind_field_flower', 'lind_flower_patch', 'lind_grass_tuft', 'lind_reeds', 'lind_river_rocks'}
SKIP_ALWAYS = {'cliff'}   # the Lind "cliff" tile is the review canvas' backdrop; here the cliff trail is the south exit
SIGN = 'lind_sign'

def tree_ring(room, ruin):
    rnd = random.Random(7)
    t = OBJ['lind_tree_01']; w, h = t['width'], t['height']
    pts = []
    for x in range(120, W - 100, 150): pts += [(x + rnd.randrange(-25, 25), 128 + rnd.randrange(-10, 14)), (x + rnd.randrange(-25, 25), H - 70 + rnd.randrange(-6, 10))]
    for y in range(280, H - 150, 190): pts += [(108 + rnd.randrange(-10, 10), y), (W - 96 + rnd.randrange(-10, 10), y)]
    out = []
    for (x, y) in pts:
        if abs(x - (730 + OX)) < 130 and y > H - 300: continue      # south trail
        if abs(y - (595 + OY)) < 150 and x > W - 300: continue      # east road
        if abs(y - (595 + OY)) < 120 and x < 250: continue
        if x > 1500 + OX - 120 and x < 1630 + OX + 120: continue    # river corridor
        out.append((x, y))
    for i, (x, y) in enumerate(out):
        a = 'rv_burnt_tree' if ruin else 'rv_lind_tree_01'
        room.prop(a, x, y, pid='tree_%02d' % i, tags=['tree'])
        c = t['collision']
        room.solid(x - w / 2 + c[0], y - h + c[1], c[2], c[3], 'tree')

def outdoor(ruin):
    R = Room('rilde_village_01_' + ('ruin' if ruin else 'peace'), 'リルド村' + ('（襲撃後）' if ruin else ''), 'Rilde Village' + (' (After the Attack)' if ruin else ''), W, H,
             'bgm_rilde_ruin' if ruin else 'bgm_rilde_day', 'ember' if ruin else 'day', base='#4d4a3c' if ruin else '#7d8a5a',
             weather={'default': 'smoke', 'rules': []} if ruin else None)
    # ---- terrain: roads, plaza, river
    lay = LIND['layout']
    for rt in lay['routes'] + lay['trails']:
        R.paths.append({'id': rt['id'], 'points': [[p[0] + OX, p[1] + OY] for p in rt['points']], 'width': rt['width']})
    R.paths.append({'id': 'road-east', 'points': [[1800 + OX, 595 + OY], [2260 + OX, 595 + OY]], 'width': 70})
    R.paths.append({'id': 'south-trail', 'points': [[730 + OX, 1350 + OY], [730 + OX, 1700 + OY]], 'width': 84})
    pl = lay['plaza']; R.fill('#948c7a' if ruin else '#b3ab96', pl['x'] + OX, pl['y'] + OY, pl['width'], pl['height'], 'cobble')
    water, bank = ('#4a6f78', '#33505a') if ruin else ('#3f86ae', '#2d6a8c')
    R.fill(bank, 1448 + OX - 6, 0, 196, H); R.fill(water, 1448 + OX, 0, 184, H, None, True)   # river (the bridge / pier decals are drawn over it)
    if ruin:
        R.patches += [{'id': 'ash_%d' % i, 'polygon': poly, 'tint': '#0c0808'} for i, poly in enumerate(ASH_POLYS)]
    # river collision with two crossings (bridge, fishing pier); generous gaps so the 32px navigation grid passes
    rx, rw = 1448 + OX, 184
    gaps = [(560 + OY, 635 + OY), (1330 + OY, 1410 + OY)]
    y0 = 0
    for (a, b) in gaps: R.solid(rx, y0, rw, a - y0, 'river'); y0 = b
    R.solid(rx, y0, rw, H - y0, 'river')
    # ---- buildings / props from the Lind layout
    DOORS = {}
    for o in LIND['objects']:
        i = o['id']
        if i in SKIP_ALWAYS: continue
        if i in DECAL:
            R.prop('rv_' + i, o['x'] + o['width'] / 2 + OX, o['y'] + o['height'] + OY, z=1, tags=['decal'], pid='d_' + i); continue
        asset = ('rvr_' + i) if (ruin and i in META['ruin']) else 'rv_' + i
        cx, by = o['x'] + o['width'] / 2 + OX, o['y'] + o['height'] + OY
        if ruin and i in META['ruin'] and META['ruin'][i].get('wReal') and i in ('lind_tree_01', 'lind_orchard_apple'): pass
        R.prop(asset, cx, by, pid='b_' + i, tags=['building' if i in BUILD else 'prop'])
        for rc in obj_rects(o): R.solid(rc[0], rc[1], rc[2], rc[3], i)
        if i in DOOR:
            c = o['collision']; dx = DOOR[i][2]; dy = o['y'] + c[1] + c[3] + OY
            DOORS[i] = (cx + dx, dy)
    ws = LIND['windStone']; wx, wy = ws['x'] + ws['width'] / 2 + OX, ws['y'] + ws['height'] + OY
    R.prop('rv_wind_stone_off' if ruin else 'rv_wind_stone_normal', wx, wy, pid='b_wind_stone', tags=['landmark'])
    c = ws['collision']; R.solid(ws['x'] + c[0] + OX, ws['y'] + c[1] + OY, c[2], c[3], 'wind_stone')
    R.interact('ev_wind_stone', wx, wy - 40, 90, hook='rilde_wind_stone', label='風の石')
    tree_ring(R, ruin)
    # animals in the pens (peaceful only)
    if not ruin:
        for name, (x, y) in {'cow': (1010, 1018), 'pig': (1170, 1018), 'chicken': (1330, 1030), 'chicken2': (1305, 1010)}.items():
            R.prop('rv_animal_' + name.rstrip('2'), x + OX, y + OY, pid='an_' + name, tags=['animal'])
    # signs: the east road and the south trail
    R.prop('rv_lind_sign', 2140 + OX, 560 + OY, pid='sign_east', tags=['sign'])
    R.interact('ev_sign_east', 2140 + OX, 540 + OY, 80, text='木の標識：『← リルド村　／　ドゥンヴァル砦 →』', label='標識')
    R.prop('rv_lind_sign', 700 + OX, 1540 + OY, pid='sign_south', tags=['sign'])
    R.interact('ev_sign_south', 700 + OX, 1520 + OY, 80, text='木の標識：『← リルド村　／　風見の断崖 ↓』', label='標識')
    # ---- doors
    for i, (room, sp, dx, label) in DOOR.items():
        x, y = DOORS[i]
        if ruin:
            R.interact('ev_door_' + i, x, y + 24, 78, text=label + 'は完全に倒壊している。炎と瓦礫で中へは入れない。', label=label)
        else:
            R.door('tr_v_' + i, x - 44, y - 4, 88, 56, room, 'from_village', label)
            R.prop('furn_doormat', x, y + 26, z=1, tags=['decal'], pid='mat_' + i)
        R.spawn(sp, x, y + 84)
    # ---- exits
    R.door('tr_v_to_cliff', 730 + OX - 90, H - 48 - 100, 180, 60, 'TBD', 'TBD', '南の小道 -> 風見の断崖（story hook onVillageExit）')
    R.door('tr_v_to_fort', W - 48 - 80, 595 + OY - 90, 70, 180, 'TBD', 'TBD', '東の街道 -> ドゥンヴァル砦（story hook onVillageExit）')
    # ---- spawns
    R.spawn('default', 1245 + OX, 560 + OY, 'down')
    R.spawn('from_cliff', 730 + OX, H - 48 - 150, 'up'); R.spawn('from_fort', W - 48 - 140, 595 + OY, 'left')
    R.spawn('from_plaza', 920 + OX, 760 + OY); R.spawn('from_training', 1777 + OX, 760 + OY); R.spawn('from_sunset', 730 + OX, 1450 + OY, 'up')
    # ---- NPCs / people
    people(R, ruin)
    if ruin: ruin_dressing(R)
    return R

ASH_POLYS = []
def _blob(cx, cy, rx, ry, seed):
    rnd = random.Random(seed); import math
    return [[r1(cx + math.cos(a / 8 * 6.283) * rx * rnd.uniform(.7, 1.15)), r1(cy + math.sin(a / 8 * 6.283) * ry * rnd.uniform(.7, 1.15))] for a in range(8)]

PEACE_WALK = {   # registry id -> (path offsets, speed)
}
def npc_zone(R, nid, talk, label, x, y, r=78, **kw): return R.interact('ev_' + nid, x, y - 22, r, npc=talk, label=label, **kw)
def place_npc(R, aid, nid, x, foot, talk, label, walk=None, speed=14, anim=False, fps=None, face=None):
    """Villager art `aid` standing/patrolling at visible feet (x, foot), talk table `talk`."""
    m = META['npc'][aid]; ix, iy = x - m['dx'], foot + m['dy']      # image anchor (bottom-centre of the full frame)
    if (walk or anim) and m['frames'] >= 2:
        w = {'id': 'w_' + nid, 'look': 'rv_' + aid, 'x': r1(ix), 'y': r1(iy), 'path': walk or [], 'speed': speed, 'rest': [2.5, 5.5]}
        if anim: w['anim'] = True
        if face: w['dir'] = face
        if fps: w['fps'] = fps
        R.walkers.append(w)
    else:
        R.prop('rv_npc_' + aid, ix, iy, tags=['npc'], pid='p_' + nid)
    if talk: npc_zone(R, nid, talk, label, x, foot)

def people(R, ruin):
    reg = {n['id']: n for n in LIND['npcs']}
    def at(i): return reg[i]['x'] + OX, reg[i]['footY'] + OY
    if not ruin:
        walk = {'farmer_female': [[-12, 4]], 'young_man': [[-60, 14], [-60, 80], [0, 80]], 'young_woman': [[70, 10], [70, -50], [0, -50]], 'elder_man': [[30, 0]], 'elder_woman': [[-20, 0]],
                'caretaker': [[0, -36]], 'emma': [[24, -8], [24, 40]]}
        spd = {'young_man': 26, 'young_woman': 24, 'elder_man': 10, 'elder_woman': 9, 'caretaker': 14, 'emma': 8, 'farmer_female': 8}
        for n in LIND['npcs']:
            i = n['id']
            if i in ('merchant', 'innkeeper', 'fisherman', 'boy', 'girl', 'boy_swordsman'): continue
            x, y = at(i)
            place_npc(R, i, i, x, y, n['talk'], n['label'], walk=walk.get(i), speed=spd.get(i, 10))
        x, y = at('boy'); place_npc(R, 'boy', 'boy', x, y, 'boy', '男の子', walk=[[140, 0], [140, 70], [-40, 70]], speed=46)
        x, y = at('girl'); place_npc(R, 'girl', 'girl', x, y, 'girl', '女の子', walk=[[120, 20], [100, 90], [-60, 70]], speed=40)
        x, y = at('boy_swordsman'); place_npc(R, 'boy_swordsman', 'boy_swordsman', x, y, 'boy_swordsman', '少年剣士', anim=True, fps=7, face=-1)
        x, y = at('fisherman'); place_npc(R, 'fisherman', 'fisherman', x, y, 'fisherman', '釣り人')
        # the hill elder (cliff trail) and the people of the legacy side quests
        place_npc(R, 'elder_man', 'hill_old', 780 + OX, 1500 + OY, 'hill_old', '風見の丘の老人')
        R.interact('ev_fiona_wait', 1930, 885, 110, hook='rilde_fiona', label='フィオナ', requires={'flag': 'rilde_fiona_waiting', 'is': True})
        R.interact('ev_training_dummy', 1780 + OX, 805 + OY, 80, hook='rilde_dummy', label='訓練用の木人')
        R.interact('ev_trainsign', 1730 + OX, 700 + OY, 70, hook='rilde_text:trainingSign', label='看板')
        R.interact('ev_well', 650 + OX, 760 + OY, 80, hook='rilde_text:well', label='井戸')
        R.interact('ev_balloon_tree', 115 + OX, 330 + OY, 90, hook='rilde_balloon_tree', label='木')
        place_npc(R, 'young_woman', 'sq_catowner', 520 + OX, 1010 + OY, None, '女の子')
        R.interact('ev_sq_catowner', 520 + OX, 990 + OY, 80, hook='rilde_catowner', label='猫を探す女の子')
        R.prop('furn_cat_white', 1330 + OX, 1230 + OY, pid='p_cat', tags=['npc'])
        R.interact('ev_cat', 1330 + OX, 1210 + OY, 70, hook='rilde_cat', label='白い猫')
        place_npc(R, 'boy', 'sq_kid', 235 + OX, 345 + OY, None, '風船の子')
        R.interact('ev_sq_kid', 235 + OX, 325 + OY, 80, hook='rilde_kid', label='風船の子')
    else:
        # after the attack: a few survivors, no patrols; the king's soldiers hold the plaza
        place_npc(R, 'elder_man', 'rr_elder', 830 + OX, 905 + OY, 'rr_elder', '長老')
        place_npc(R, 'elder_woman', 'rr_oldwoman', 690 + OX, 930 + OY, 'rr_oldwoman', '村の老婆')
        place_npc(R, 'young_woman', 'rr_woman', 1040 + OX, 860 + OY, 'rr_woman', '若い女性')
        place_npc(R, 'farmer_male', 'rr_farmer', 1160 + OX, 640 + OY, 'rr_farmer', '農夫')
        place_npc(R, 'boy', 'rr_boy', 940 + OX, 960 + OY, 'rr_boy', '男の子')
        R.props.append({'id': 'p_rr_knight', 'asset': 'npc_slot_soldier', 'x': 980 + OX, 'y': 700 + OY, 'tags': ['npc']})
        R.interact('ev_rr_knight', 980 + OX, 680 + OY, 80, npc='rr_knight', label='王国の兵士')
        R.props.append({'id': 'p_rr_knight2', 'asset': 'npc_slot_guard', 'x': 560 + OX, 'y': 640 + OY, 'tags': ['npc']})
        R.interact('ev_rr_knight2', 560 + OX, 620 + OY, 80, npc='rr_knight2', label='王国の兵士')
        R.interact('ev_trainsign', 1730 + OX, 700 + OY, 70, text='訓練場の看板は焦げて、半分に折れている。', label='看板')
        R.interact('ev_well', 650 + OX, 760 + OY, 80, text='井戸の水は濁り、灰が浮いている。', label='井戸')

def ruin_dressing(R):
    """Rubble, burnt beams, ash and fire spots over the burnt village (all deterministic)."""
    rnd = random.Random(2026)
    # fire spots at the burnt buildings (roof collapse height ~ 55% of the building)
    for k, i in enumerate(['lind_aidan_house', 'lind_inn', 'lind_item_shop', 'lind_elder_house', 'lind_house_01', 'lind_house_02', 'lind_house_04', 'lind_barn']):
        o = OBJ[i]; cx = o['x'] + o['width'] / 2 + OX; top = o['y'] + OY
        R.vista_fire(cx + (k % 3 - 1) * 20, top + o['height'] * .62, w=int(o['width'] * .62), h=int(o['height'] * .95), seed=11 + k)
    for i in ('lind_storage', 'lind_house_03'):
        o = OBJ[i]; R.vista_fire(o['x'] + o['width'] / 2 + OX, o['y'] + o['height'] * .6 + OY, w=int(o['width'] * .5), h=int(o['height'] * .8), seed=40 + len(R.vista), kind='smoke_column')
    R.vista_fire(wx_stone_x() , 640 + OY, w=60, h=80, seed=77, kind='smoke_column')
    # rubble piles in front of the buildings and scattered on the roads
    for i in BUILD:
        o = OBJ[i]; cx = o['x'] + o['width'] / 2 + OX; by = o['y'] + o['height'] + OY
        for (dx, dy, a) in ((-o['width'] * .38, 6, 'furn_rubble_m'), (o['width'] * .42, 14, 'furn_rubble_s'), (o['width'] * .05, 40, 'furn_rubble_s')):
            R.prop(a, cx + dx, by + dy, pid=R.uid('rub'), tags=['debris']); R.solid(cx + dx - 26, by + dy - 14, 52, 14, 'rubble')
        R.prop('furn_scorch', cx, by + 6, z=2, tags=['decal'], pid=R.uid('scorch'))
    for x, y in ((640, 600), (1020, 640), (860, 780), (700, 840), (1200, 610), (500, 700), (930, 1010), (1450, 900)):
        a = rnd.choice(['furn_rubble_s', 'furn_rubble_m', 'furn_burnt_beam', 'furn_post_burnt'])
        R.prop(a, x + OX + rnd.randrange(-30, 30), y + OY + rnd.randrange(-20, 20), pid=R.uid('deb'), tags=['debris'])
    for x, y in ((760, 740), (1000, 700), (900, 900), (600, 620), (1180, 860), (420, 560), (1280, 1180), (1000, 1150)):
        R.prop(rnd.choice(['furn_ash_patch', 'furn_scorch']), x + OX, y + OY, z=2, tags=['decal'], pid=R.uid('ash'))
    R.prop('furn_cart_wreck', 1130 + OX, 1260 + OY, pid='cart_wreck', tags=['debris']); R.solid(1130 + OX - 40, 1260 + OY - 22, 80, 22, 'wreck')
    R.prop('furn_banner_torn', 860 + OX, 820 + OY, pid='banner', tags=['debris'])
    for x, y in ((470, 520), (1330, 560), (1190, 1230)): R.vista_fire(x + OX, y + OY, w=70, h=90, seed=90 + x // 10, kind='fire_spot')

def wx_stone_x(): return LIND['windStone']['x'] + LIND['windStone']['width'] / 2 + OX

for k, (cx, cy, rx, ry) in enumerate(((1250, 330, 260, 170), (870, 270, 250, 150), (300, 560, 250, 160), (520, 300, 240, 140), (280, 920, 210, 150), (580, 1070, 230, 150), (590, 850, 230, 150), (1100, 760, 230, 130), (900, 720, 260, 190))):
    ASH_POLYS.append(_blob(cx + OX, cy + OY, rx, ry, k + 5))

# ------------------------------------------------------------------------------------------------ interiors
BW = 150    # back-wall band height (px) below the 48px border
FOOT = {    # asset -> (collision width factor, depth px) ; None = no collision
    'bed': (.9, 46), 'bed_small': (.9, 38), 'chair': (.5, 14), 'chair_back': (.5, 14), 'stool': (.6, 14), 'bench': (.9, 20), 'table_round': (.8, 30), 'table_long': (.92, 36), 'table_small': (.9, 30),
    'counter': (.96, 44), 'counter_shop': (.96, 44), 'counter_inn': (.96, 44), 'shelf_books': (.9, 28), 'shelf_pots': (.9, 28), 'shelf_goods': (.9, 28), 'cupboard': (.9, 30), 'jar': (.6, 14), 'barrel': (.7, 18), 'crate': (.8, 22),
    'sack': (.6, 14), 'basket': (.6, 12), 'bucket': (.6, 12), 'hay_bale': (.9, 26), 'crates_stack': (.9, 34), 'sacks_pile': (.8, 28), 'tool_rack': (.9, 24), 'spinning_wheel': (.8, 22), 'weapon_rack': (.9, 24),
    'fireplace': (.84, 40), 'candle_stand': (.5, 10), 'rune_pillar': (.5, 16), 'map_table': (.9, 32), 'stairs_up': (.0, 0), 'stairs_down': (.0, 0), 'plant_pot': (.6, 12), 'spill_bowl': (.5, 10)}
DECOR = {'tapestry', 'window_wall', 'door_wall', 'herb_bundle', 'rug_green', 'rug_red', 'doormat', 'window_light'}

class Interior:
    """Builder for one furnished room."""
    def __init__(s, mid, ja, en, w, h, bgm='bgm_rilde_home', floor='#a98b5c', wall='#76654f', exit_to=None, sx=None):
        s.R = Room(mid, ja, en, w, h, bgm, 'day', True); R = s.R; s.w, s.h = w, h
        R.fill(base_ := '#17110d', 0, 0, w, h); R.fill(wall, 48, 48, w - 96, BW, 'planks'); R.solid(48, 48, w - 96, BW, 'wall')
        R.fill(floor, 48, 48 + BW, w - 96, h - 96 - BW, 'planks')
        R.fill('#3a2c20', 48, 48 + BW - 10, w - 96, 12)        # skirting shadow
        cx = w // 2
        sx = sx or cx
        R.spawn('default', sx, h - 48 - 140, 'up'); R.spawn('from_village', sx, h - 48 - 140, 'up')
        if exit_to:
            R.door('tr_exit', cx - 70, h - 48 - 74, 140, 62, 'rilde_village', exit_to, '外へ出る')
            R.prop('furn_doormat', cx, h - 48 - 28, z=1, tags=['decal'], pid='mat')
    def put(s, asset, x, y, text=None, hook=None, label=None, z=None, flip=False, npc=None, collide=True, r=None):
        R = s.R; name = asset
        zz = 1 if name in ('rug_green', 'rug_red', 'doormat', 'window_light') else (2 if name in ('tapestry', 'window_wall', 'door_wall', 'herb_bundle') else z)
        R.prop('furn_' + name, x, y, z=zz, tags=['furniture'])
        if name in FOOT and collide:
            fw, d = FOOT[name]; w = FURN[name]['w'] * fw
            if fw and d: R.solid(x - w / 2, y - d, w, d, name)
        if text or hook or npc:
            h = FURN[name]['h'] if name in FURN else 60
            kw = {}
            if text: kw['text'] = text
            if hook: kw['hook'] = hook
            if npc: kw['npc'] = npc
            R.interact(R.uid('ev_' + name), x, y - min(40, h * .4), r or max(50, FURN[name]['w'] * .5 if name in FURN else 60), label=label or name, **kw)
    def person(s, aid, nid, x, foot, talk, label, text=None):
        place_npc(s.R, aid, nid, x, foot, talk, label)
        s.R.solid(x - 14, foot - 10, 28, 10, 'npc')
    def doc(s): return s.R.doc()

def rooms():
    out = []
    # ---------------- エイダンの家 ----------------
    I = Interior('rilde_in_aidan', 'エイダンの家', "Aidan's House", 960, 720, exit_to='from_aidan'); R = I.R; R.spawn('from_bed', 250, 330, 'down'); R.spawn('default', 250, 330, 'down')
    I.put('window_wall', 400, 178); I.put('tapestry', 560, 190)
    I.put('bed', 160, 290, text='使い慣れたベッドだ。今はまだ休む時間じゃない。', label='ベッド')
    I.put('cupboard', 320, 212, hook='rilde_drawer', label='タンス')
    I.put('fireplace', 700, 214, text='薪がぱちぱちと燃えている。', label='暖炉')
    I.put('shelf_books', 860, 212, text='父さんの古い剣術書だ。難しい言葉が並んでいる。', label='本棚')
    I.put('rug_green', 480, 500)
    I.put('table_round', 480, 470, text='木のテーブルだ。家族で食事をした跡が残っている。', label='テーブル')
    I.put('chair', 480, 398); I.put('chair_back', 480, 556); I.put('stool', 392, 470); I.put('stool', 570, 470)
    I.put('jar', 870, 590, hook='rilde_pot', label='壺'); I.put('barrel', 150, 600); I.put('basket', 780, 610); I.put('bucket', 830, 640)
    R.vista.append({'id': 'hearth', 'kind': 'hearth', 'x': 590, 'y': 120, 'w': 220, 'h': 220, 'seed': 3, 'on': True})
    out.append(I)
    # ---------------- 長老の家 ----------------
    I = Interior('rilde_in_elder', '長老の家 ― 風見の丘', "Elder's House", 960, 720, exit_to='from_elder', floor='#9a7e54', wall='#6a5d4a')
    I.put('window_wall', 220, 178); I.put('window_wall', 740, 178); I.put('tapestry', 480, 190)
    I.put('rune_pillar', 130, 330, text='古い風のルーンが刻まれた石柱だ。ᚠ ……読めない文字の奥で、何かが静かに息をしている。', label='ルーン石'); I.put('rune_pillar', 830, 330, text='古い風のルーンが刻まれた石柱だ。ᚱ ……触れると、かすかに温かい。', label='ルーン石')
    I.put('shelf_books', 300, 212, text='古びた書物だ。風とルーンについて記されているが、読めない箇所が多い。', label='本棚'); I.put('shelf_books', 660, 212, text='古びた書物だ。風とルーンについて記されているが、読めない箇所が多い。', label='本棚')
    I.put('fireplace', 480, 216, text='薪がぱちぱちと燃えている。', label='暖炉')
    I.put('rug_red', 480, 500); I.put('map_table', 480, 480, text='古い村の地図だ。村の北には、風を示す奇妙な紋様が刻まれている。', label='古い村の地図')
    I.put('chair_back', 480, 556); I.put('stool', 380, 480); I.put('plant_pot', 120, 600); I.put('candle_stand', 840, 600); I.put('bench', 770, 600)
    I.person('elder_man', 'elder', 480, 420, 'elder', '長老')
    I.R.vista.append({'id': 'hearth', 'kind': 'hearth', 'x': 370, 'y': 120, 'w': 220, 'h': 220, 'seed': 4, 'on': True})
    out.append(I)
    # ---------------- 宿屋 1F ----------------
    I = Interior('rilde_in_inn_1f', '宿屋「風見鶏」 1階', 'Inn "Kazamidori" 1F', 1200, 800, exit_to='from_inn', floor='#a4835a', wall='#6e5a46'); R = I.R; R.spawn('from_stairs', 1000, 330, 'down')
    I.put('window_wall', 560, 178); I.put('window_wall', 900, 178); I.put('tapestry', 720, 190)
    I.put('counter_inn', 300, 346, text='磨かれた木のカウンターだ。主人に話しかけよう。', label='カウンター'); I.person('innkeeper', 'innkeeper', 300, 262, 'innkeeper', '宿屋の主人')
    I.put('shelf_pots', 120, 214, text='食器や保存食が並んでいる。', label='棚'); I.put('barrel', 440, 232); I.put('barrel', 490, 238)
    I.put('fireplace', 740, 216, text='大きな暖炉に火が入っている。旅人が足を休めている。', label='暖炉')
    I.put('stairs_up', 1040, 236); R.door('tr_inn_up', 990, 250, 110, 90, 'rilde_in_inn_2f', 'from_stairs', '2階へ', .25)
    I.put('rug_green', 700, 560); I.put('table_long', 700, 560); I.put('chair_back', 640, 640); I.put('chair_back', 760, 640); I.put('chair', 640, 508); I.put('chair', 760, 508)
    I.put('table_round', 250, 600); I.put('stool', 170, 600); I.put('stool', 330, 600); I.put('table_round', 1010, 610); I.put('stool', 930, 610); I.put('stool', 1090, 610)
    I.put('plant_pot', 90, 420); I.put('candle_stand', 1120, 420)
    I.person('young_man', 'inn_traveler', 1010, 540, 'inn_traveler', '旅人')
    R.vista.append({'id': 'hearth', 'kind': 'hearth', 'x': 630, 'y': 120, 'w': 220, 'h': 220, 'seed': 5, 'on': True})
    out.append(I)
    # ---------------- 宿屋 2F ----------------
    I = Interior('rilde_in_inn_2f', '宿屋「風見鶏」 2階', 'Inn "Kazamidori" 2F', 1100, 760, floor='#9d7d55', wall='#6a5845'); R = I.R
    R.spawns.clear(); R.spawn('default', 220, 330); R.spawn('from_stairs', 220, 330)
    for i, x in enumerate((220, 400, 580, 760, 940)):
        I.put('door_wall', x, 198, text='客室20%d の扉だ。今は宿泊客が利用している。' % (i + 1), label='客室20%d' % (i + 1), collide=False, r=70)
    I.put('stairs_down', 110, 250); R.door('tr_inn_down', 60, 262, 110, 80, 'rilde_in_inn_1f', 'from_stairs', '1階へ', .25)
    I.put('window_wall', 560, 178)
    I.put('rug_red', 560, 480); I.put('bench', 560, 600, text='廊下のベンチだ。窓の外から、風見鶏の軋む音が聞こえる。', label='ベンチ'); I.put('plant_pot', 980, 330); I.put('candle_stand', 330, 560); I.put('candle_stand', 800, 560)
    out.append(I)
    # ---------------- 道具屋 ----------------
    I = Interior('rilde_in_shop', '道具屋「若葉の袋」', 'Item Shop "Wakaba no Fukuro"', 960, 720, exit_to='from_shop', floor='#a9895c', wall='#72604a')
    I.put('window_wall', 480, 178); I.put('herb_bundle', 300, 172); I.put('herb_bundle', 660, 172)
    I.put('shelf_goods', 130, 214, text='薬草と薬瓶が並んでいる。', label='薬棚'); I.put('shelf_goods', 830, 214, text='旅道具が整然と並んでいる。', label='旅道具の棚'); I.put('shelf_goods', 480, 214, text='干した薬草のいい匂いがする。', label='棚')
    I.put('counter_shop', 480, 420, text='カウンターだ。店主に話しかけよう。', label='カウンター'); I.person('merchant', 'merchant', 480, 340, 'merchant', '道具屋の店主')
    I.put('rug_red', 480, 560); I.put('crate', 140, 560); I.put('sacks_pile', 210, 600); I.put('barrel', 820, 580); I.put('basket', 760, 620); I.put('plant_pot', 880, 400)
    out.append(I)
    # ---------------- 民家 ----------------
    I = Interior('rilde_in_house_01', '村人の家', "Villager's House", 860, 640, exit_to='from_house_01', floor='#a4875c', wall='#705e49')
    I.put('window_wall', 230, 178); I.put('tapestry', 600, 190); I.put('fireplace', 420, 214, text='薪がぱちぱちと燃えている。', label='暖炉')
    I.put('bed', 130, 292, text='ふかふかのベッドだ。', label='ベッド'); I.put('bed_small', 740, 280, text='子ども用の小さなベッドだ。', label='ベッド')
    I.put('rug_green', 430, 430); I.put('table_small', 430, 440, text='食べかけのパンが置かれている。', label='テーブル'); I.put('chair_back', 430, 506); I.put('stool', 350, 450)
    I.put('spinning_wheel', 740, 520, text='糸車だ。今も使われているようだ。', label='糸車'); I.put('barrel', 110, 520); I.put('jar', 160, 580)
    out.append(I)
    I = Interior('rilde_in_house_02', '村人の家', "Villager's House", 860, 640, exit_to='from_house_02', floor='#a58a5e', wall='#6f5e4a')
    I.put('window_wall', 600, 178); I.put('tapestry', 230, 190); I.put('shelf_pots', 130, 214, text='調理道具や保存瓶が並んでいる。', label='棚'); I.put('cupboard', 340, 212, text='衣類がきれいに畳まれている。', label='タンス')
    I.put('fireplace', 560, 214, text='薪がぱちぱちと燃えている。', label='暖炉'); I.put('bed', 730, 296, text='きれいに整えられたベッドだ。', label='ベッド')
    I.put('table_round', 360, 450, text='木のテーブルだ。', label='テーブル'); I.put('chair', 360, 380); I.put('chair_back', 360, 536); I.put('stool', 280, 450); I.put('stool', 440, 450); I.put('rug_red', 360, 480)
    I.put('basket', 700, 560); I.put('plant_pot', 770, 480); I.put('bucket', 130, 560)
    out.append(I)
    I = Interior('rilde_in_house_03', '村人の家', "Villager's House", 860, 640, exit_to='from_house_03', floor='#a48658', wall='#715f49')
    I.put('window_wall', 430, 178); I.put('tapestry', 700, 190); I.put('bed', 150, 292, text='使い込まれたベッドだ。', label='ベッド'); I.put('shelf_books', 330, 214, text='古い物語の本が並んでいる。', label='本棚')
    I.put('fireplace', 560, 216, text='薪がぱちぱちと燃えている。', label='暖炉'); I.put('table_small', 560, 450, text='木のテーブルだ。', label='テーブル'); I.put('chair_back', 560, 512); I.put('chair', 480, 450)
    I.put('rug_green', 520, 470); I.put('barrel', 740, 540); I.put('crate', 140, 540); I.put('jar', 200, 600); I.put('candle_stand', 760, 330)
    out.append(I)
    I = Interior('rilde_in_house_04', '村人の家', "Villager's House", 860, 640, exit_to='from_house_04', floor='#a78c60', wall='#735f4a', sx=690)
    I.put('window_wall', 220, 178); I.put('window_wall', 640, 178); I.put('fireplace', 430, 214, text='薪がぱちぱちと燃えている。', label='暖炉'); I.put('cupboard', 700, 212, text='古い衣類が入っている。', label='タンス'); I.put('bed', 130, 292, text='ふかふかのベッドだ。', label='ベッド')
    I.put('table_long', 430, 470, text='長い食卓だ。大家族で使っていたのだろう。', label='食卓'); I.put('bench', 430, 540); I.put('chair', 330, 400); I.put('chair', 530, 400)
    I.put('rug_red', 430, 480); I.put('sack', 120, 560); I.put('basket', 750, 560); I.put('plant_pot', 760, 330)
    out.append(I)
    # ---------------- 納屋 / 倉庫 / 見張り小屋 ----------------
    I = Interior('rilde_in_barn', '納屋', 'Barn', 1000, 700, exit_to='from_barn', floor='#9a7c4e', wall='#6b5640')
    I.put('window_wall', 500, 178); I.put('tool_rack', 160, 214, text='鍬や熊手が立てかけてある。', label='農具'); I.put('tool_rack', 840, 214, text='よく手入れされた農具だ。', label='農具')
    for x, y in ((320, 232), (400, 236), (360, 296)): I.put('hay_bale', x, y)
    I.put('hay_bale', 780, 400); I.put('hay_bale', 780, 460); I.put('crates_stack', 560, 300, text='収穫物の木箱が積まれている。', label='木箱'); I.put('barrel', 640, 232); I.put('sacks_pile', 700, 260); I.put('bucket', 880, 560); I.put('basket', 220, 560); I.put('sack', 150, 480)
    out.append(I)
    I = Interior('rilde_in_storage', '倉庫', 'Storehouse', 760, 600, exit_to='from_storage', floor='#977a4f', wall='#68543e')
    I.put('shelf_goods', 150, 214, text='保存食や雑貨が整理されている。', label='棚'); I.put('shelf_pots', 600, 214, text='壺や瓶が並んでいる。', label='棚'); I.put('crates_stack', 380, 250, text='木箱が積まれている。', label='木箱')
    I.put('barrel', 140, 420); I.put('barrel', 190, 440); I.put('sacks_pile', 560, 420); I.put('crate', 640, 460); I.put('jar', 130, 500, text='壺の中は乾燥した豆だ。', label='壺'); I.put('basket', 500, 500)
    out.append(I)
    I = Interior('rilde_in_trainshed', '訓練場の見張り小屋', 'Training Ground Hut', 640, 520, exit_to='from_trainshed', floor='#9c7f55', wall='#69563f', sx=500)
    I.put('window_wall', 320, 178); I.put('weapon_rack', 150, 214, text='稽古用の木剣と槍が並んでいる。', label='武器架'); I.put('weapon_rack', 490, 214, text='稽古用の木剣が立てかけてある。', label='武器架')
    I.put('bench', 330, 350, text='訓練の合間に休むベンチだ。', label='ベンチ'); I.put('barrel', 560, 340); I.put('sacks_pile', 90, 350); I.put('bucket', 200, 410)
    out.append(I)
    return out

# ------------------------------------------------------------------------------------------------ validation
def validate(R, doc):
    errs = []
    solid = [(x, y, w, h) for (x, y, w, h, t) in R.rects]
    edges = [(0, 0, R.w, 48), (0, R.h - 48, R.w, 48), (0, 0, 48, R.h), (R.w - 48, 0, 48, R.h)]
    def blocked(x, y):
        for (a, b, c, d) in solid + edges:
            if a <= x < a + c and b <= y < b + d: return True
        return not (0 <= x < R.w and 0 <= y < R.h)
    cols, rows = R.w // G, R.h // G
    free = lambda i, j: not blocked(i * G + G / 2, j * G + G / 2)
    sp = R.spawns[doc['spawns']['default']]; start = (int(sp['x'] // G), int(sp['y'] // G))
    seen = {start}; q = [start]
    if not free(*start): errs.append('default spawn blocked')
    while q:
        i, j = q.pop()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (i + di, j + dj)
            if n in seen or not (0 <= n[0] < cols and 0 <= n[1] < rows) or not free(*n): continue
            seen.add(n); q.append(n)
    def reach(x, y, pad):
        ci, cj = int(x // G), int(y // G); r = pad // G + 1
        return any((ci + a, cj + b) in seen for a in range(-r, r + 1) for b in range(-r, r + 1))
    for n, p in R.spawns.items():
        if blocked(p['x'], p['y']): errs.append('spawn %s inside a wall' % n)
        elif (int(p['x'] // G), int(p['y'] // G)) not in seen: errs.append('spawn %s unreachable' % n)
    for t in R.trans:
        r = t['rect']
        if not any((i, j) in seen and r['x'] <= i * G + G / 2 < r['x'] + r['w'] and r['y'] <= j * G + G / 2 < r['y'] + r['h'] for i in range(int(r['x'] // G), int((r['x'] + r['w']) // G) + 1) for j in range(int(r['y'] // G), int((r['y'] + r['h']) // G) + 1)):
            errs.append('transition %s: no reachable ground inside its rect' % t['id'])
    for z in R.zones:
        if z['type'] != 'interact': continue
        sh = z['shape']
        if not reach(sh['cx'], sh['cy'], 160): errs.append('zone %s unreachable' % z['id'])
    return errs, len(seen) * G * G / (R.w * R.h)

# ------------------------------------------------------------------------------------------------ manifest
def manifest_rules():
    rules = []
    for i, m in META['objects'].items(): rules.append({'match': '^rv_%s$' % i, 'file': m['file'], 'w': m['w'], 'h': m['h'], 'gen': 'rilde'})
    for i, m in META['ruin'].items():
        rules.append({'match': '^rvr_%s$' % i, 'file': m['file'], 'w': m.get('wReal', m['w']), 'h': m['h'], 'gen': 'rilde'})
    t = META['ruin']['lind_tree_01']; rules.append({'match': '^rv_burnt_tree$', 'file': t['file'], 'w': t.get('wReal', t['w']), 'h': t['h'], 'gen': 'rilde'})
    for k, m in META['landmark'].items(): rules.append({'match': '^rv_%s$' % k, 'file': m['file'], 'w': m['w'], 'h': m['h'], 'gen': 'rilde'})
    for k, m in META['animals'].items(): rules.append({'match': '^rv_animal_%s$' % k, 'file': m['file'], 'w': m['w'], 'h': m['h'], 'gen': 'rilde'})
    for k, m in META['npc'].items():
        rules.append({'match': '^rv_npc_%s$' % k, 'file': m['idle'], 'w': m['w'], 'h': m['h'], 'gen': 'rilde'})
        if m['frames'] >= 2: rules.append({'match': '^npc_slot_rv_%s$' % k, 'file': m['idle'], 'w': m['w'], 'h': m['h'], 'walk': {'file': m['frame'], 'frames': m['frames']}, 'gen': 'rilde'})
    for k, m in FURN.items(): rules.append({'match': '^furn_%s$' % k, 'file': m['file'], 'w': m['w'], 'h': m['h'], 'gen': 'rilde'})
    return rules

def main():
    allr = [outdoor(False), outdoor(True)] + [i.R for i in rooms()]
    bad = 0; byid = {r.id: r for r in allr}
    for R in allr:
        d = R.doc(); errs, cov = validate(R, d)
        for t in R.trans:   # targets
            if t['toMap'] in ('TBD', 'rilde_village'): continue
            tg = byid.get(t['toMap'])
            if not tg: errs.append('%s -> unknown map %s' % (t['id'], t['toMap']))
            elif t['toSpawn'] not in tg.spawns: errs.append('%s -> %s has no spawn %s' % (t['id'], t['toMap'], t['toSpawn']))
        for t in R.trans:
            if t['toMap'] == 'rilde_village':
                for v in ('peace', 'ruin'):
                    if t['toSpawn'] not in byid['rilde_village_01_' + v].spawns: errs.append('%s -> village %s has no spawn %s' % (t['id'], v, t['toSpawn']))
        json.dump(d, open(os.path.join(OUT, R.id + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        print('%-26s %4dx%-4d props=%-3d walkers=%-2d zones=%-3d trans=%d vista=%d reach=%2.0f%% %s' % (R.id, R.w, R.h, len(R.props), len(R.walkers), len(R.zones), len(R.trans), len(R.vista), cov * 100, 'OK' if not errs else 'PROBLEMS'))
        for e in errs: print('   ', e); bad += 1
    # the two village variants must expose identical spawns (doors/exits resolve to either)
    if set(byid['rilde_village_01_peace'].spawns) != set(byid['rilde_village_01_ruin'].spawns): print('spawn sets differ between peace/ruin'); bad += 1
    m = json.load(open(MAN, encoding='utf-8'))
    m['node'] = [r for r in m['node'] if r.get('gen') != 'rilde']
    m['node'][0:0] = manifest_rules()
    open(MAN, 'w', encoding='utf-8').write(json.dumps(m, ensure_ascii=False, indent=1))
    print('manifest: %d rilde rules' % len(manifest_rules()))
    sys.exit(1 if bad else 0)
if __name__ == '__main__': main()
