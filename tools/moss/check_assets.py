#!/usr/bin/env python3
"""Moss Forest art manifest checker (M6). Run after dropping real PNGs into img/field/moss/ and editing manifest.json.
usage: python3 tools/moss/check_assets.py [--table]
Checks (exit 1 on any ERROR):
  - manifest.json parses; every rule regex compiles; every 'file' exists, is RGBA PNG, has w/h (world px) > 0
  - ground tiles exist and are square
  - SHADOWING: a rule that can never win because an earlier rule matches the same asset ids (real art listed after a stand-in)
  - NULL-RULE: warns when a 'file: null' rule swallows an id that a later real rule is meant for
  - COVERAGE: every asset id used by the 3 maps (props + scatter pools, by render kind) -> real / standin / none(placeholder)
"""
import glob, json, os, re, sys
from PIL import Image
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
MAN = os.path.join(ROOT, 'img/field/moss/manifest.json')
errs, warns = [], []
def err(m): errs.append(m); print('ERROR', m)
def warn(m): warns.append(m); print('warn ', m)

man = json.load(open(MAN, encoding='utf-8'))
base = os.path.join(ROOT, man['base'])
def png(path, label):
    p = os.path.join(base, path)
    if not os.path.isfile(p): err('%s: missing file %s' % (label, path)); return None
    try: im = Image.open(p)
    except Exception as e: err('%s: unreadable %s (%s)' % (label, path, e)); return None
    if im.mode != 'RGBA' and 'ground' not in label: err('%s: %s is %s, must be transparent RGBA' % (label, path, im.mode))
    return im
for k in ('grass', 'dirt'):
    im = png(man['ground'][k], 'ground.' + k)
    if im and im.width != im.height: err('ground.%s must be square, got %s' % (k, im.size))

ENTITY_KEYS = ['chest_closed', 'chest_open', 'symbol', 'seal', 'seal_corrupted', 'lou', 'fiona']
for k, r in (man.get('entity') or {}).items():
    if k not in ENTITY_KEYS: err('entity.%s unknown key (allowed: %s)' % (k, ', '.join(ENTITY_KEYS))); continue
    if not r.get('file'): continue
    if not (r.get('w', 0) > 0 and r.get('h', 0) > 0): err('entity.%s needs w/h > 0' % k)
    png(r['file'], 'entity.' + k)
print('[entity] real art for: %s' % (', '.join(k for k, r in (man.get('entity') or {}).items() if r.get('file')) or 'none (placeholders: ' + ', '.join(ENTITY_KEYS) + ')'))

# asset ids used by the maps, split by render kind (node = DOM sprite, layer = baked into canvas chunks)
used = {'node': set(), 'layer': set()}
presets = {}   # asset family (id without _NN) -> list of (map, [x,y,w,h]) collision rects, for the art-vs-collision check
for f in sorted(glob.glob(os.path.join(ROOT, 'data/maps/*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    for k, rects in (d.get('collision', {}).get('presets') or {}).items(): presets.setdefault(k, []).append((os.path.basename(f), rects))
    for p in d.get('props', []): used['node'].add(p['asset'])
    for s in d.get('scatter', []):
        for a in s.get('pool', []): used['node' if s.get('render') == 'node' else 'layer'].add(a)

for kind in ('node', 'layer'):
    rules = man.get(kind, [])
    comp = []
    for i, r in enumerate(rules):
        try: comp.append(re.compile(r['match']))
        except re.error as e: err('%s[%d] bad regex %r: %s' % (kind, i, r['match'], e)); comp.append(None)
        if r.get('file'):
            if not (r.get('w', 0) > 0 and r.get('h', 0) > 0): err('%s[%d] %s needs w/h > 0' % (kind, i, r['file']))
            png(r['file'], '%s[%d]' % (kind, i))
    hit = {i: [] for i in range(len(rules))}; cover = {}
    for a in sorted(used[kind]):
        win = next((i for i, c in enumerate(comp) if c and c.search(a)), None)
        cover[a] = win
        later = [i for i, c in enumerate(comp) if c and c.search(a) and (win is None or i > win)]
        if win is not None: hit[win].append(a)
        for i in later:
            if not rules[i].get('standin') and rules[i].get('file') and (win is not None) and rules[win].get('standin', rules[win].get('file') is None):
                warn('SHADOWED %s[%d] (%s) never applies to %s: rule %d (%s) matches first; move the real rule above it' % (kind, i, rules[i]['file'], a, win, rules[win]['match']))
    for i, r in enumerate(rules):
        if comp[i] and not hit[i] and not any(comp[i].search(a) for a in used[kind]):
            if not r.get('standin'): warn('%s[%d] %r matches no asset used by the maps (typo? it is harmless but dead)' % (kind, i, r['match']))
    print('\n[%s] %d asset ids in maps' % (kind, len(used[kind])))
    n = {'real': 0, 'standin': 0, 'none': 0}
    for a, w in cover.items():
        r = rules[w] if w is not None else None
        c = 'none' if (r is None or not r.get('file')) else ('standin' if r.get('standin') else 'real')
        n[c] += 1
        if '--table' in sys.argv: print('   %-28s %-8s %s' % (a, c, r['file'] if r and r.get('file') else '-'))
    print('   real=%d standin=%d placeholder=%d' % (n['real'], n['standin'], n['none']))
    # COLLISION vs ART: a real sprite that is much wider than the preset blocker lets the player walk through its picture
    # (and a much narrower picture leaves an invisible wall). Anchor is bottom-centre, so compare widths only.
    if kind == 'node':
        for a, w in sorted(cover.items()):
            r = rules[w] if w is not None else None
            if not r or not r.get('file') or r.get('standin'): continue
            fam = re.sub(r'_\d+$', '', a)
            for mapname, rects in presets.get(fam, []):
                lo = min(x for x, y, ww, hh in rects); hi = max(x + ww for x, y, ww, hh in rects); cw = hi - lo
                if r['w'] > cw * 1.6: warn('COLLISION %s (%s): art is %dpx wide but the blocker in %s is only %dpx - the player can walk into the picture; widen collision.presets[%s]' % (a, r['file'], r['w'], mapname, cw, fam))
                elif r['w'] < cw * .6: warn('COLLISION %s (%s): art is %dpx wide but the blocker in %s is %dpx - an invisible wall beside the picture; narrow collision.presets[%s]' % (a, r['file'], r['w'], mapname, cw, fam))
print('\n%d error(s), %d warning(s)' % (len(errs), len(warns)))
sys.exit(1 if errs else 0)
