#!/usr/bin/env python3
"""Register the 20 additional moss assets in img/field/moss/manifest.json (node rules, world w/h from the quality report, bottom-centre anchored).
Rules are tagged gen='moss_additional_20261019' and inserted before the stand-in rules (first match wins). Idempotent. Existing rules are untouched."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; GEN = 'moss_additional_20261019'
rep = json.load(open(ROOT / 'docs/art/delivered/moss_additional_20261019/quality/report.json'))
f = ROOT / 'img/field/moss/manifest.json'; m = json.load(open(f))
m['node'] = [r for r in m['node'] if r.get('gen') != GEN]
at = next(i for i, r in enumerate(m['node']) if r.get('standin') or r.get('file') is None and r['match'].startswith('^tree_'))
new = [{'match': '^%s$' % k, 'file': 'art/%s.png' % k, 'w': v['manifest_wh'][0], 'h': v['manifest_wh'][1], 'gen': GEN} for k, v in rep.items()]
m['node'][at:at] = new
ind = 1 if f.read_text(encoding='utf-8').startswith('{\n') else None
json.dump(m, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=ind)
print('registered', len(new), 'at index', at)
