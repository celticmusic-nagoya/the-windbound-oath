#!/usr/bin/env python3
"""Check height-map foot-box reachability on a 16 px grid (no game writes).

Usage: python3 tools/moss/check_levels.py [map_id ...] [--json]
Explicit JSON paths are accepted for isolated broken-copy checks. Only maps with
height are checked. A lower/upper overlap requires a connector or an overpass;
this is a data safety contract, not proof of the browser movement implementation.
"""
import argparse
from collections import deque
from functools import lru_cache
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
GRID = 16
# FieldCollision.footprint: actor (feet.x-17,feet.y-42) -> box.
FOOT = (-11, -10, 22, 10)


def rect(value):
    if not isinstance(value, list) or len(value) != 4 or not all(
            isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in value):
        raise ValueError('rectangle needs four finite numbers')
    if value[2] <= 0 or value[3] <= 0:
        raise ValueError('rectangle size must be positive')
    return tuple(value)


def inside(x, y, r):
    return r[0] <= x <= r[0]+r[2] and r[1] <= y <= r[1]+r[3]


def check_map(data):
    errors = []
    spec = data['height']
    if not isinstance(spec, dict):
        raise ValueError('height must be an object')
    width, height = data['world']['width'], data['world']['height']
    if not all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in (width, height)):
        raise ValueError('world dimensions must be finite and positive')
    walks = {}
    for key, value in spec.get('levels', {}).items():
        level = int(key)
        if level < 0 or str(level) != key:
            raise ValueError('level keys must be nonnegative integers')
        walks[level] = [rect(r) for r in value.get('walk', [])]
    connectors = []
    ids = set()
    for raw in spec.get('connectors', []):
        c = {**raw, 'rect': rect(raw['rect']), 'zone': raw.get('zone', .22)}
        if not c.get('id') or c['id'] in ids:
            raise ValueError('connector ids must be unique and nonempty')
        ids.add(c['id'])
        if c.get('axis') not in ('x', 'y') or c.get('fromEnd') not in ('min', 'max'):
            raise ValueError('invalid connector direction: '+c['id'])
        if any(type(c.get(k)) is not int or c[k] < 0 for k in ('from', 'to')) or c['from'] == c['to']:
            raise ValueError('invalid connector levels: '+c['id'])
        if not isinstance(c['zone'], (int, float)) or not 0 < c['zone'] < .5:
            raise ValueError('invalid connector end zone: '+c['id'])
        connectors.append(c)
    levels = sorted({0, *walks, *(c[k] for c in connectors for k in ('from', 'to'))})
    if any(l > 0 and not walks.get(l) for l in levels):
        errors.append('Every upper level needs a nonempty walk region')
    decks = []
    for raw in spec.get('overpasses', []):
        if type(raw.get('level')) is not int or raw['level'] not in levels or raw['level'] <= 0:
            raise ValueError('invalid overpass level')
        decks.append({**raw, 'rect': rect(raw['rect'])})
    solids = []
    collision = data.get('collision', {})
    blockers = list(collision.get('edgeBlockers', [])) + list(collision.get('blockers', []))
    # Props use the same asset-family preset and horizontal flip as ForestLoader.
    for prop in data.get('props', []):
        if prop.get('noCollision'):
            continue
        family = re.sub(r'_\d+$', '', prop['asset'])
        for x, y, w, h in collision.get('presets', {}).get(family, []):
            blockers.append({'shape': 'rect', 'x': prop['x']+(-x-w if prop.get('flip') else x),
                             'y': prop['y']+y, 'w': w, 'h': h})
    if any(s.get('render') == 'node' for s in data.get('scatter', [])):
        errors.append('Procedural node scatter collision is not supported; browser verification required')
    for b in blockers:
        if b.get('enabledWhen'):
            errors.append('Conditional blocker has no declared flag state: '+str(b.get('id')))
        parts = [[b[k] for k in ('x', 'y', 'w', 'h')]] if b.get('shape') == 'rect' else b.get('rects') if b.get('shape') == 'rects' else None
        if parts is None:
            raise ValueError('unsupported blocker shape: '+str(b.get('shape')))
        ls = b.get('levels')
        if ls is not None and (not isinstance(ls, list) or any(type(l) is not int or l < 0 for l in ls)):
            raise ValueError('invalid blocker levels')
        solids.extend((rect(r), ls) for r in parts)

    # Exact rectangle coverage complements the 16px graph: a one-pixel walk
    # expansion must not create undeclared upper/lower overlap between grid nodes.
    for level, regions in walks.items():
        if level == 0:
            continue
        support = [r for r, ls in solids if ls is None or 0 in ls]
        support += [d['rect'] for d in decks if d['level'] == level]
        support += [c['rect'] for c in connectors if level in (c['from'], c['to'])]
        for region in regions:
            x, y, w, h = region
            if x < 0 or y < 0 or x+w > width or y+h > height:
                errors.append('Upper walk rectangle extends outside world: '+str(region))
            nearby = [r for r in support if r[0] < x+w and r[0]+r[2] > x and r[1] < y+h and r[1]+r[3] > y]
            xs = sorted({x, x+w, *(max(x, min(x+w, q)) for r in nearby for q in (r[0], r[0]+r[2]))})
            ys = sorted({y, y+h, *(max(y, min(y+h, q)) for r in nearby for q in (r[1], r[1]+r[3]))})
            gap = next(((a, b, c-a, d-b) for a, c in zip(xs, xs[1:]) for b, d in zip(ys, ys[1:])
                        if not any(inside((a+c)/2, (b+d)/2, r) for r in nearby)), None)
            if gap:
                errors.append('Level %d walk has unsupported lower-ground overlap: %s' % (level, gap))

    def connector_at(x, y):
        return next((c for c in connectors if inside(x, y, c['rect'])), None)

    def level_at(x, y, level):
        c = connector_at(x, y)
        if c is None:
            return level
        r = c['rect']; axis = 0 if c['axis'] == 'x' else 1
        t = ((x, y)[axis]-r[axis])/r[axis+2]
        if c['fromEnd'] == 'max':
            t = 1-t
        t = max(0, min(1, t))
        if t <= c['zone']:
            return c['from']
        if t >= 1-c['zone']:
            return c['to']
        return level if level in (c['from'], c['to']) else c['from']

    @lru_cache(maxsize=500000)
    def walkable(x, y, level):
        x0, y0 = x+FOOT[0], y+FOOT[1]; x1, y1 = x0+22, y0+10
        if x0 < 0 or y0 < 0 or x1 > width or y1 > height:
            return False
        if any((ls is None or level in ls) and x1 > r[0] and x0 < r[0]+r[2]
               and y1 > r[1] and y0 < r[1]+r[3] for r, ls in solids):
            return False
        if level == 0:
            return True
        rs = walks.get(level, []) + [c['rect'] for c in connectors if level in (c['from'], c['to'])]
        # Exactly the four corner checks used by FieldHeight.inWalk.
        return all(any(inside(px, py, r) for r in rs) for px in (x0, x1) for py in (y0, y1))

    valid = {l: set() for l in levels}
    overlaps = []; exposed = []
    for y in range(0, math.floor(height)+1, GRID):
        for x in range(0, math.floor(width)+1, GRID):
            ok = [l for l in levels if walkable(x, y, l)]
            for l in ok:
                if level_at(x, y, l) == l:
                    valid[l].add((x, y))
            if len(ok) > 1:
                overlaps.append({'feet': [x, y], 'levels': ok})
                c = connector_at(x, y)
                for l in ok:
                    if l and 0 in ok and not (c and l in (c['from'], c['to'])) and not any(
                            d['level'] == l and inside(x, y, d['rect']) for d in decks):
                        if len(exposed) < 16:
                            exposed.append({'feet': [x, y], 'level': l})
    if exposed:
        errors.append('Upper/lower overlap outside declared connectors/overpasses: '+json.dumps(exposed))

    def segment(x, y, level, nx, ny):
        steps = max(1, math.ceil(math.hypot(nx-x, ny-y)/2)); changed = []
        for i in range(1, steps+1):
            fx, fy = x+(nx-x)*i/steps, y+(ny-y)*i/steps
            new = level_at(fx, fy, level)
            if new != level:
                c = connector_at(fx, fy)
                if c is None:
                    return None
                changed.append(c['id'])
            level = new
            if not walkable(fx, fy, level):
                return None
        return level, changed

    spawns = data.get('spawns', {})
    points = spawns.get('points', {})
    start = points.get(spawns.get('default'))
    if start is None:
        errors.append('Default spawn missing')
    visited = set(); queue = deque(); crossings = {c['id']: 0 for c in connectors}
    if start:
        sx, sy = start['x'], start['y']
        sl = start.get('level', 0 if walkable(sx, sy, 0) else max(levels))
        if not walkable(sx, sy, sl):
            errors.append('Default spawn not walkable at starting level')
        else:
            for ix in range(round(sx/GRID)-1, round(sx/GRID)+2):
                for iy in range(round(sy/GRID)-1, round(sy/GRID)+2):
                    x, y = ix*GRID, iy*GRID
                    result = segment(sx, sy, sl, x, y)
                    if result and (x, y) in valid[result[0]]:
                        node = (x, y, result[0]); visited.add(node); queue.append(node)
    links = set()
    while queue:
        x, y, l = queue.popleft()
        for dx, dy in ((GRID, 0), (-GRID, 0), (0, GRID), (0, -GRID),
                       (GRID, GRID), (GRID, -GRID), (-GRID, GRID), (-GRID, -GRID)):
            nx, ny = x+dx, y+dy
            if not any((nx, ny) in valid[k] for k in levels):
                continue
            result = segment(x, y, l, nx, ny)
            if result is None or (nx, ny) not in valid[result[0]]:
                continue
            nl, changes = result
            for cid in changes:
                crossings[cid] += 1
                links.add((l, nl))
            node = (nx, ny, nl)
            if node not in visited:
                visited.add(node); queue.append(node)
    for l in levels:
        if l == 0:
            continue
        missing = [p for p in valid[l] if (*p, l) not in visited]
        if not valid[l] or missing:
            errors.append('Level %d: %d/%d canonical grid cells unreachable from default spawn' % (l, len(missing), len(valid[l])))
    for cid, count in crossings.items():
        if not count:
            errors.append('Connector is not crossable from default spawn: '+cid)

    locations = []
    for name, p in points.items():
        locations.append(('spawn:'+name, p['x'], p['y']))
    for category in ('eventZones', 'treasurePoints', 'transitions'):
        for p in data.get(category, []):
            sh = p.get('rect') or p.get('shape') or p
            if isinstance(sh, dict) and all(k in sh for k in ('x', 'y', 'w', 'h')):
                x, y = sh['x']+sh['w']/2, sh['y']+sh['h']/2
            elif isinstance(sh, list) and len(sh) == 4:
                x, y = sh[0]+sh[2]/2, sh[1]+sh[3]/2
            elif 'x' in p and 'y' in p:
                x, y = p['x'], p['y']
            else:
                errors.append('Unsupported location shape: '+str(p.get('id', category)))
                continue
            locations.append((category+':'+str(p.get('id')), x, y))
    checked = []
    for name, x, y in locations:
        ok = [l for l in levels if walkable(x, y, l)]
        checked.append({'id': name, 'feet': [x, y], 'walkable_levels': ok})
        if not ok:
            errors.append('Location is not walkable at any level: '+name)
    return {'id': data.get('id'), 'grid_px': GRID, 'foot_box': {'offset_from_feet': [-11, -10], 'size': [22, 10]},
            'levels': [{'level': l, 'walkable_cells': len(valid[l]), 'reachable_cells': sum(n[2] == l for n in visited)} for l in levels],
            'level_links': [list(p) for p in sorted(links)], 'connectors': crossings,
            'locations': checked, 'overlap_points': overlaps, 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('maps', nargs='*', help='map IDs or explicit JSON paths')
    parser.add_argument('--json', action='store_true', help='print one JSON object without human output')
    args = parser.parse_args()
    paths = [Path(v) if v.endswith('.json') else ROOT/'data/maps'/(v+'.json') for v in args.maps] if args.maps else sorted((ROOT/'data/maps').glob('*.json'))
    reports = []; errors = []
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise ValueError('map must be an object')
            if 'height' not in data:
                continue
            result = check_map(data); result['file'] = str(path); reports.append(result)
        except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError) as exc:
            errors.append(str(path)+': '+str(exc))
    count = len(errors)+sum(len(r['errors']) for r in reports)
    if args.json:
        print(json.dumps({'maps': reports, 'errors': errors, 'problem_count': count}, ensure_ascii=False, indent=2))
    else:
        for r in reports:
            print('[%s] grid 16px, foot box 22x10' % r['id'])
            for level in r['levels']:
                print('  level %(level)s: reachable %(reachable_cells)s / walkable %(walkable_cells)s' % level)
            print('  level links:', r['level_links'], 'connector crossings:', r['connectors'])
            print('  locations: %d; shared XY: %d (first 8: %s)' % (len(r['locations']), len(r['overlap_points']), r['overlap_points'][:8]))
            for error in r['errors']:
                print('ERROR', error)
        for error in errors:
            print('ERROR', error)
        if reports or errors:
            print('Problems:', count)
    return 1 if count else 0


if __name__ == '__main__':
    sys.exit(main())
