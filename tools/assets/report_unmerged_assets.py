#!/usr/bin/env python3
"""ASSET-REGISTRY-01: unmerged-asset report. Re-reads the remote branches (git, no network beyond `git fetch`) and lists image files that exist only on
unmerged branches, compared with the registry. Writes docs/assets/reports/unmerged_assets.md. Differences between this live scan and the registry snapshot
(`branch_only_assets`) are listed as 'registry not updated'. usage: report_unmerged_assets.py [--fetch]"""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def git(*a): return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True).stdout
if '--fetch' in sys.argv: subprocess.run(['git', 'fetch', '-q', 'origin', '+refs/heads/*:refs/remotes/origin/*'], cwd=ROOT)
reg = json.load(open(ROOT / 'docs/assets/ASSET_REGISTRY.json', encoding='utf-8'))
known = {(a['source_branch'], a['source_path']) for a in reg['assets'] if a['integration_status'] in ('BRANCH_ONLY', 'SOURCE_ONLY')}
live = []; L = ['# Unmerged asset report', '']
branches = [b for b in git('for-each-ref', '--format=%(refname:short)', 'refs/remotes/origin').split() if not b.endswith('HEAD') and b != 'origin']
for b in branches:
    if subprocess.run(['git', 'merge-base', '--is-ancestor', b, 'origin/main'], cwd=ROOT).returncode == 0: continue
    fs = [l.split('\t')[1] for l in git('diff', '--name-status', '--diff-filter=AM', 'origin/main...' + b, '--', 'img', 'docs/art').splitlines()
          if l.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.zip')) and '/qa/' not in l and '/verify/' not in l and 'docs/art/reference' not in l]
    if fs:
        L.append('- `%s`: %d files (latest %s)' % (b.replace('origin/', '', 1), len(fs), git('log', '-1', '--format=%h %ad', '--date=short', b).strip()))
        live += [(b.replace('origin/', '', 1), f) for f in fs]
missing = [x for x in live if x not in known]
L += ['', '## Registry not updated for (%d)' % len(missing), ''] + ['- %s : %s' % x for x in missing[:80]]
(ROOT / 'docs/assets/reports').mkdir(parents=True, exist_ok=True); (ROOT / 'docs/assets/reports/unmerged_assets.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('unmerged image files on branches: %d, not in registry: %d' % (len(live), len(missing)))
