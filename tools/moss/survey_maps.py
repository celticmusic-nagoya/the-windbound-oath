#!/usr/bin/env python3
"""Read-only map inventory and conservative 2D grid survey (no runtime mutation).
Use --json for machine output; --root selects a checkout; --step defaults to 32 world px.
"""
import argparse
from collections import deque
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mf_lib import Hash  # existing 22x10 feet footprint and spatial hash


def shape_rects(s):
    if s.get('shape') == 'rect':
        return [[s['x'], s['y'], s['w'], s['h']]]
    if s.get('shape') == 'rects':
        return s['rects']
    raise ValueError('runtime collision supports rect/rects only: '+str(s.get('shape')))


def collision(m, flags):
    rows = []
    for i, b in enumerate(m.get('collision', {}).get('edgeBlockers', [])):
        rows += [('edge'+str(i), r) for r in shape_rects(b)]
    for b in m.get('collision', {}).get('blockers', []):
        when = b.get('enabledWhen')
        if when and flags.get(when['flag']) != when['is']:
            continue
        rows += [(b['id'], r) for r in shape_rects(b)]
    presets = m.get('collision', {}).get('presets', {})
    for p in m.get('props', []):
        if p.get('noCollision') or (p.get('hideIf') and flags.get(p['hideIf'])):
            continue
        for x, y, w, h in presets.get(re.sub(r'_\d+$', '', p.get('asset', '')), []):
            rows.append((p['id'], [p['x']+(-x-w if p.get('flip') else x), p['y']+y, w, h]))
    return rows


def reachability(m, flags, step):
    width, height = m['world']['width'], m['world']['height']
    solid = Hash(collision(m, flags))
    points = m.get('spawns', {}).get('points', {})
    start_name = m.get('spawns', {}).get('default')
    start = points.get(start_name)
    if not start:
        return {'status': 'no_default_spawn', 'flags': flags}

    def clear(x, y):
        return 11 <= x <= width-11 and 10 <= y <= height and not solid.hit(x, y)

    def line(a, b):
        n = max(1, math.ceil(math.dist(a, b)/8))
        return all(clear(a[0]+(b[0]-a[0])*i/n, a[1]+(b[1]-a[1])*i/n) for i in range(n+1))

    origin = (start['x'], start['y'])
    origin_blocker = solid.hit(*origin)
    if not clear(*origin):
        return {'status': 'default_spawn_blocked', 'flags': flags, 'spawn': start_name, 'blocker': origin_blocker}
    # Global grid, connected to the exact spawn only by sampled clear segments.
    sx, sy = round(origin[0]/step), round(origin[1]/step)
    seen = set()
    queue = deque()
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            cell = sx+dx, sy+dy
            if line(origin, (cell[0]*step, cell[1]*step)):
                seen.add(cell); queue.append(cell)
    checked = {}
    def free(cell):
        if cell not in checked:
            checked[cell] = clear(cell[0]*step, cell[1]*step)
        return checked[cell]
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cell = (x+dx, y+dy)
            if cell in seen or not free(cell):
                continue
            if line((x*step, y*step), (cell[0]*step, cell[1]*step)):
                seen.add(cell); queue.append(cell)

    def approach(x, y, radius=0):
        n = max(2, math.ceil(radius/step)+1)
        cx, cy = round(x/step), round(y/step)
        for yy in range(cy-n, cy+n+1):
            for xx in range(cx-n, cx+n+1):
                if (xx, yy) not in seen:
                    continue
                point = xx*step, yy*step
                if radius:
                    if math.dist(point, (x, y)) <= radius:
                        return True
                elif line(point, (x, y)):
                    return True
        return False

    targets = []
    for name, p in points.items():
        targets.append({'kind': 'spawn', 'id': name, 'reachable': approach(p['x'], p['y']), 'blocked': solid.hit(p['x'], p['y'])})
    for p in m.get('treasurePoints', []):
        targets.append({'kind': 'treasure_approach', 'id': p['id'], 'reachable': approach(p['x'], p['y'], 100)})
    for t in m.get('transitions', []):
        r = t.get('rect')
        if not r:
            targets.append({'kind': 'transition', 'id': t['id'], 'reachable': None}); continue
        reached = any((x, y) in seen for y in range(math.ceil(r['y']/step), math.floor((r['y']+r['h'])/step)+1)
                      for x in range(math.ceil(r['x']/step), math.floor((r['x']+r['w'])/step)+1))
        # Thin rectangles may contain no grid point: connect reachable neighbouring cells to actual points.
        if not reached:
            for fx, fy in ((.5, .5), (.1, .5), (.9, .5), (.5, .1), (.5, .9)):
                if approach(r['x']+r['w']*fx, r['y']+r['h']*fy):
                    reached = True; break
        targets.append({'kind': 'transition', 'id': t['id'], 'reachable': reached, 'enabled': t.get('enabled', True)})
    return {'status': 'sampled_2d', 'flags': flags, 'grid_step': step, 'segment_step': 8,
            'start': start_name, 'visited_cells': len(seen), 'compiled_rects': solid.n,
            'reached': sum(t['reachable'] is True for t in targets), 'total': len(targets), 'targets': targets,
            'unreached': [t for t in targets if t['reachable'] is False]}


def priority(m):
    i = m['id']
    if i.startswith('cliff_'): return (0, i)
    if i.startswith('fort_'): return (1, i)
    if i.startswith('moss_forest_01'): return (2, i)
    if i.startswith('moss_forest_02'): return (3, i)
    if i.startswith('moss_forest_03'): return (4, i)
    if i.startswith('rilde_'): return (5, i)
    return (6, i)


def candidates(m):
    result, materials = [], []
    # Inspect explicit landmark descriptions, not arbitrary decorative plant names.
    terrain = m.get('terrain', {})
    chunks = terrain.get('cliffs', []) + terrain.get('waters', []) + terrain.get('paths', [])
    chunks += [{'id': p.get('id'), 'asset': p.get('asset'), 'tags': p.get('tags', [])} for p in m.get('props', [])]
    chunks += [{'id': t.get('id'), 'note': t.get('note', '')} for t in m.get('transitions', [])]
    text = json.dumps(chunks, ensure_ascii=False).lower()
    specs = [('崖/高台', r'cliff|plateau|rim|ledge|断崖|高台|崖', '崖正面・上端・角'),
             ('階段/坂', r'stair|ramp|slope|ascent|階段|坂', '階段/坂4方向・踊り場'),
             ('橋/桟橋', r'bridge|pier|桟橋|橋', '床・側面・欄干・橋脚'),
             ('滝/低地', r'waterfall|ravine|gorge|pool|滝|渓谷', '滝・水際・低地の縁'),
             ('樹冠', r'tree_ancient|root_arch|巨木', '上層樹冠・通行用根アーチ')]
    if terrain.get('cliffs'):
        result.append('崖/高台'); materials.append('崖正面・上端・角')
    for label, pattern, material in specs:
        if re.search(pattern, text) and label not in result:
            result.append(label); materials.append(material)
    if m['id'].startswith('fort_'):
        result.append('城壁/主塔（IDからの候補）'); materials.append('石壁側面・階段・欄干')
    return result or ['明示的な候補なし'], list(dict.fromkeys(materials))


def survey(root, step):
    paths = sorted((root/'data/maps').glob('*.json'))
    maps = [json.loads(p.read_text()) for p in paths]
    by_id = {m['id']: m for m in maps}
    output = []
    for path, m in sorted(zip(paths, maps), key=lambda pair: priority(pair[1])):
        print('survey '+m['id'], file=sys.stderr, flush=True)
        events = m.get('eventZones', [])
        props = m.get('props', [])
        npc_refs = {e['npc'] for e in events if e.get('npc')}
        npc_ids = {p['id'] for p in props if 'npc' in p.get('tags', []) or p.get('asset', '').startswith('npc_')}
        enemies = m.get('monsters', []) + m.get('enemies', [])
        story_symbols = m.get('story', {}).get('prologue', {}).get('symbols', [])
        zones = m.get('encounterZones', [])
        terrain = {k: len(v) for k, v in m.get('terrain', {}).items() if isinstance(v, list)}
        indoor = bool(m.get('story', {}).get('interior')) or '_in_' in m['id'] or m['id'].endswith('_keep')
        flags = {b['enabledWhen']['flag']: False for b in m.get('collision', {}).get('blockers', []) if b.get('enabledWhen')}
        variants = [reachability(m, flags, step)]
        if flags:
            variants.append(reachability(m, {k: True for k in flags}, step))
        connections = []
        for t in m.get('transitions', []):
            target = by_id.get(t.get('toMap'))
            status = ('target_spawn_ok' if t.get('toSpawn') in target.get('spawns', {}).get('points', {}) else 'target_spawn_missing') if target else 'external_hook_or_missing'
            connections.append({'id': t['id'], 'toMap': t.get('toMap'), 'toSpawn': t.get('toSpawn'), 'enabled': t.get('enabled', True), 'status': status, 'note': t.get('note', '')})
        candidate, material = candidates(m)
        output.append({'id': m['id'], 'display_name': m.get('displayName', {}).get('ja', m['id']), 'file': str(path.relative_to(root)),
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'width': m['world']['width'], 'height': m['world']['height'],
                       'terrain_total': sum(terrain.values()), 'terrain_counts': terrain, 'props': len(props), 'walkers': len(m.get('walkers', [])),
                       'npc_static_unique': len(npc_ids), 'npc_static_ids': sorted(npc_ids), 'npc_event_refs': sorted(npc_refs), 'enemies_explicit': len(enemies), 'story_enemy_symbols': len(story_symbols), 'monster_types': sorted({e.get('type', e.get('id')) for e in enemies}),
                       'encounter_zones': len(zones), 'encounter_zones_enabled': sum(z.get('enabled', True) for z in zones),
                       'enemy_types_in_zones': sorted({e['id'] for z in zones for e in z.get('enemies', [])}),
                       'treasures': len(m.get('treasurePoints', [])), 'herbs': sum(p.get('kind')=='herb' for p in m.get('treasurePoints', [])), 'event_zones': len(events), 'transitions': len(connections),
                       'transitions_enabled': sum(t['enabled'] for t in connections), 'height_present': bool(m.get('height')),
                       'indoors': indoor, 'candidates': candidate, 'material_estimates': material,
                       'reachability': variants, 'connections': connections})
    try:
        sha = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        sha = None
    return {'source_sha': sha, 'map_count': len(output), 'grid_step': step,
            'limitations': ['2D static survey: height/scatter-node collision and moving NPCs are not reproduced.',
                            'Grid failures are investigation candidates, not proofs of runtime unreachability.',
                            'Treasure approach uses a 100px survey radius, not an assertion of the game interaction radius.',
                            'Connections with no JSON may be runtime hooks; they require separate verification.',
                            'Enemy counts include JSON monsters and story symbols, but exclude DEV/runtime-created extras; zones are configuration, not active spawn counts.'], 'maps': output}


def markdown(result):
    lines = ['# 全マップ調査 (2026-10-13)', '', f"基準コード: `03d053e` / 調査HEAD `{result['source_sha']}`。マップ **{result['map_count']}件**。ブランチ `work/codex-night-j`。STATUS: READY（静的調査）。mainへの反映なし。", '',
             '件数はJSONに明示されたもの。NPCは描画用npc_ asset/npcタグのprops数＋walkers数（ベッド等のNPC slot代用を含む、会話refの数は足さない）。敵はmonsters/enemies定義数＋story.prologue.symbols数、遭遇ゾーンは別記。宝箱欄はtreasurePoints総数（採取ポイントも含み、JSONのherbsで別集計）。runtimeが生成するスライム等の実在数は含まない。地形はterrain直下の配列要素の合計、オブジェクトはprops数。屋内はstory.interiorまたは命名からの推定。', '',
             '到達は既存mf_lib.Hashの22×10足元とforest-loaderのrect/preset方式を参照した独立2D静的チェック。default spawnから32px四近傍、各辺を8px以下でサンプル。spawnは正確な地点、遷移はrect内、宝箱は100px以内への接近。条件付きblockerは全flag false/trueを分ける。散布node衝突、動くNPC、ストーリー条件、イベント発火と高さは再現しない。「未到達」は細い通路/格子/条件の問題を含む調査候補。ゲームの到達可否の断定ではない。', '',
             '| マップID / 表示名 | サイズ | 地形/props | NPC props+歩行 | 明示敵+story / 遭遇zone(有効) | 宝箱 / event / 遷移(有効) | height / 屋内外 | 到達サンプル | 立体化候補 / 必要素材（推定） |', '|---|---|---|---|---|---|---|---|---|']
    for m in result['maps']:
        reach = ' / '.join(f"{r.get('reached',0)}/{r.get('total',0)}" if r['status']=='sampled_2d' else r['status'] for r in m['reachability'])
        lines.append(f"| {m['id']} / {m['display_name']} | {m['width']:g}×{m['height']:g} | {m['terrain_total']}/{m['props']} | {m['npc_static_unique']}+{m['walkers']} | {m['enemies_explicit']}+{m['story_enemy_symbols']} / {m['encounter_zones']}({m['encounter_zones_enabled']}) | {m['treasures']}/{m['event_zones']}/{m['transitions']}({m['transitions_enabled']}) | {'あり' if m['height_present'] else 'なし'} / {'屋内推定' if m['indoors'] else '屋外推定'} | {reach} | {'・'.join(m['candidates'])} / {'・'.join(m['material_estimates']) or '候補決定後'} |")
    lines += ['', '## 未到達の調査候補（flags別）', '']
    for m in result['maps']:
        for r in m['reachability']:
            if r['status'] != 'sampled_2d' or r['unreached']:
                detail = ', '.join(t['kind']+':'+t['id'] for t in r.get('unreached', [])) or r['status']
                lines.append(f"- `{m['id']}` flags={r['flags']}: {detail}")
    lines += ['', '## JSON未解決接続 / spawn不一致', '', '未解決は欠損と確定しない。lind_village等はruntime hookで処理される場合がある。無効/TBDもそのまま列挙。']
    for m in result['maps']:
        for t in m['connections']:
            if t['status'] != 'target_spawn_ok':
                lines.append(f"- `{m['id']}` / `{t['id']}` → `{t['toMap']}` / `{t['toSpawn']}`: {t['status']}、enabled={t['enabled']}")
    lines += ['', '## 再実行 / 未検証', '', '```sh', 'python3 tools/moss/survey_maps.py > docs/qa/map-survey-20261013.md', 'python3 tools/moss/survey_maps.py --json > docs/qa/map-survey-20261013.json', '```', '',
              'JSONは各マップのSHA256、地形カテゴリ別個数、NPC ID、接続、到達ターゲット/flagsを保持する。上の標準実行とJSON実行は同じsurvey関数を使う。チェッカーcheck_a2はA2設計専用のルート・座標を要求するため全件に流用せず、Hashだけ再使用し実JSONのcollision.presetsを読む。', '',
              '立体化候補はID/地形/props/遷移noteからの推定で、必要な段差・高さ・新マップを確定しない。採用済み画像/JSONは未編集。橋の上下通行や屋根/樹冠遮蔽は高さ実装と作者確認が必要。Android負荷、全マップ歩行、宝箱の実開封、ストーリー全ゲートは未検証。資料/新規ツールだけなのでmainのロールバック不要。']
    return '\n'.join(lines)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--step', type=int, default=32)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.step < 8 or args.step > 64:
        parser.error('--step must be 8..64')
    result = survey(args.root, args.step)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else markdown(result), end='\n' if args.json else '')


if __name__ == '__main__':
    main()
