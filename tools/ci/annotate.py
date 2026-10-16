#!/usr/bin/env python3
"""Emit the tier result as a GitHub check annotation (readable through the API without downloading logs/artifacts)."""
import json, sys
from pathlib import Path
out = Path(sys.argv[1] if len(sys.argv) > 1 else 'ci-results'); title = sys.argv[2] if len(sys.argv) > 2 else 'tier'
try:
    r = json.loads((out / 'results.json').read_text()); rows = r['results'] if isinstance(r, dict) and 'results' in r else r
except Exception as e:
    print('::warning title=%s::no results.json (%s)' % (title, e)); sys.exit(0)
c = {}
for x in rows: c[x.get('verdict') or x.get('status')] = c.get(x.get('verdict') or x.get('status'), 0) + 1
lines = ['%s %s' % (', '.join('%s=%d' % kv for kv in sorted(c.items())), 'total=%d' % len(rows))]
for x in rows: lines.append('%s | %s | %ss | %s' % (x.get('test') or x.get('name'), x.get('verdict') or x.get('status'), x.get('seconds', x.get('s', '?')), ';'.join(map(str, x.get('first_fail', x.get('fails', []))))[:120] if isinstance(x.get('first_fail', x.get('fails', [])), list) else str(x.get('first_fail', ''))[:120]))
msg = '%0A'.join(l.replace('%', '%25').replace('\r', '').replace('\n', ' ') for l in lines)[:60000]
print('::notice title=%s::%s' % (title, msg))
