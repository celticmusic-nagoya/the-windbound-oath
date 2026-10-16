#!/usr/bin/env python3
"""T0 static check (no browser): index.html local script/link/img references exist, no duplicate <script src>, listed JS parses with node --check.
Fails (exit 1) on any missing reference or duplicate script; never edits files."""
import re, subprocess, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.refs = []; s.scripts = []
    def handle_starttag(s, tag, attrs):
        a = dict(attrs)
        if tag == 'script' and a.get('src'):
            s.scripts.append(a['src']); s.refs.append(a['src'])
        elif tag == 'link' and a.get('href'):
            s.refs.append(a['href'])
        elif tag == 'img' and a.get('src'):
            s.refs.append(a['src'])
def local(u):
    p = urlsplit(u)
    return not p.scheme and not u.startswith(('//', 'data:', '#')) and p.path
html = ROOT / 'index.html'
par = P(); par.feed(html.read_text(encoding='utf-8', errors='replace'))
missing = sorted({urlsplit(u).path for u in par.refs if local(u) and not (ROOT / urlsplit(u).path).exists()})
dups = sorted({urlsplit(u).path for u in par.scripts if local(u) and [urlsplit(x).path for x in par.scripts].count(urlsplit(u).path) > 1})
print('local refs: %d  missing: %d  duplicate scripts: %d' % (sum(1 for u in par.refs if local(u)), len(missing), len(dups)))
bad = 0
for m in missing: print('FAIL missing reference', m); bad += 1
for d in dups: print('FAIL duplicate script', d); bad += 1
js = sorted({urlsplit(u).path for u in par.scripts if local(u) and urlsplit(u).path.endswith('.js') and (ROOT / urlsplit(u).path).exists()})
for f in js:
    r = subprocess.run(['node', '--check', str(ROOT / f)], capture_output=True, text=True)
    if r.returncode: print('FAIL syntax', f, r.stderr.strip().splitlines()[:1]); bad += 1
print('FAILS %d' % bad)
sys.exit(1 if bad else 0)
