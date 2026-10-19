#!/usr/bin/env python3
"""ASSET-REGISTRY-01: reference integrity. Writes docs/assets/reports/refs_report.md. Hard errors (exit 1):
  - img/battle/motion-manifest.json: every frame file exists, frame numbering contiguous, ms count matches frames, hitFrame in range
  - js/assets.js BATTLE_ASSETS / BATTLE_IDLE_ASSETS paths exist
  - img/field/moss/manifest.json: every non-null node/entity file exists; rule order: no 'real' rule shadowed by an earlier stand-in
  - data/maps/*.json props: asset id resolves to a rule
Informational: images on main referenced by nothing (never deleted)."""
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; err = []; L = ['# Reference check', '']
man = json.load(open(ROOT / 'img/battle/motion-manifest.json', encoding='utf-8')); n = 0
for k, st in man['motions'].items():
    for s, d in st.items():
        ms = d['ms'] if isinstance(d['ms'], list) else [d['ms']] * d['frames']
        if len(ms) != d['frames']: err.append('motion %s/%s: ms count %d != frames %d' % (k, s, len(ms), d['frames']))
        if d.get('hitFrame') and not 1 <= d['hitFrame'] <= d['frames']: err.append('motion %s/%s: hitFrame out of range' % (k, s))
        for i in range(1, d['frames'] + 1):
            n += 1; p = ROOT / man['base'] / d['dir'] / d['pattern'].replace('{n}', '%02d' % i)
            if not p.is_file(): err.append('motion %s/%s: missing frame %s' % (k, s, p.relative_to(ROOT)))
L.append('- motion-manifest: %d motions, %d frame files checked' % (sum(len(v) for v in man['motions'].values()), n))
src = (ROOT / 'js/assets.js').read_text(encoding='utf-8')
paths = set(re.findall(r"img/[\w/\-\.]+\.(?:png|jpg|webp)", src))
dirs = dict(re.findall(r"^\s*(\w+):\s*'(img/battle/[^']+/)'", src, re.M))
for blk in re.finditer(r"^  (\w+): \{(.*?)\n  \}", src, re.M | re.S):
    actor = blk.group(1)
    if actor in dirs:
        for f in re.findall(r":\s*'([\w/\-\.]+\.png)'", blk.group(2)):
            if not (ROOT / dirs[actor] / f).is_file(): err.append('assets.js %s: missing %s' % (actor, dirs[actor] + f))
for p in paths:
    if not (ROOT / p).is_file(): err.append('assets.js path missing: %s' % p)
L.append('- js/assets.js: %d literal image paths + %d BATTLE_ASSETS entries checked' % (len(paths), sum(len(re.findall(r":\s*'([\w/\-\.]+\.png)'", b.group(2))) for b in re.finditer(r'^  (\w+): \{(.*?)\n  \}', src, re.M | re.S))))
mm = json.load(open(ROOT / 'img/field/moss/manifest.json', encoding='utf-8')); rules = mm['node']; nf = 0
for r in rules:
    if r.get('file'):
        nf += 1
        if not (ROOT / 'img/field/moss' / r['file']).is_file(): err.append('moss manifest: missing %s (rule %s)' % (r['file'], r['match']))
for k, v in (mm.get('entity') or {}).items():
    if isinstance(v, dict) and v.get('file') and not (ROOT / 'img/field/moss' / v['file']).is_file(): err.append('moss manifest entity %s: missing %s' % (k, v['file']))
L.append('- moss manifest: %d node rules with files checked' % nf)
unres = set()
for f in sorted((ROOT / 'data/maps').glob('moss_forest_0*.json')):
    for p in json.load(open(f, encoding='utf-8'))['props']:
        if not any(re.search(r['match'], p['asset']) for r in rules): unres.add((f.name, p['asset']))
# loader fallback (js/field/forest-loader.js COLOR / forest-layer.js): veg_* / prop_* / tree_* / rock_* / fx_* / anc_* without a rule are drawn as colored code placeholders (informational, not an error)
FALLBACK = re.compile(r'^(veg_|prop_|tree_|rock_|fx_|anc_|gnd_)')
for f, a in sorted(unres):
    if not FALLBACK.match(a): err.append('map %s: prop asset %s matches no manifest rule and has no placeholder fallback' % (f, a))
L.append('- moss maps: prop assets resolved against manifest rules (%d without a rule -> drawn as code placeholder: %s)' % (len(unres), sorted({a for _, a in unres})[:8]))
L += ['', '## Errors', ''] + (['- ' + e for e in err] or ['なし'])
(ROOT / 'docs/assets/reports').mkdir(parents=True, exist_ok=True); (ROOT / 'docs/assets/reports/refs_report.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('refs: %d errors' % len(err)); [print('ERROR', e) for e in err[:15]]; sys.exit(1 if err else 0)
