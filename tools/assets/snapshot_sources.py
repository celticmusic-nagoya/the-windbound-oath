#!/usr/bin/env python3
"""Refresh docs/assets/inventory_sources.json: remote branches, unmerged branches and the image files that exist ONLY on unmerged branches
(img/ and docs/art/ additions, QA screenshots excluded), plus PR / Issue counts (needs `gh`; falls back to the previous numbers when offline).
usage: snapshot_sources.py [--no-gh]"""
import json, subprocess, sys, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / 'docs/assets/inventory_sources.json'
REPO = 'celticmusic-nagoya/the-windbound-oath'
def git(*a): return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True).stdout
subprocess.run(['git', 'fetch', '-q', 'origin', '+refs/heads/*:refs/remotes/origin/*'], cwd=ROOT)
branches = [b for b in git('for-each-ref', '--format=%(refname:short)', 'refs/remotes/origin').split() if not b.endswith('HEAD') and b != 'origin']
unmerged = [b for b in branches if subprocess.run(['git', 'merge-base', '--is-ancestor', b, 'origin/main'], cwd=ROOT).returncode != 0]
bo = []
for b in unmerged:
    files = [l.split('\t')[1] for l in git('diff', '--name-status', '--diff-filter=AM', 'origin/main...' + b, '--', 'img', 'docs/art').splitlines()
             if l.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.zip')) and '/qa/' not in l and '/verify/' not in l and 'docs/art/reference' not in l]
    if files:
        bo.append({'branch': b.replace('origin/', '', 1), 'commit': git('rev-parse', b).strip(), 'date': git('log', '-1', '--format=%ad', '--date=short', b).strip(), 'files': files})
old = json.load(open(OUT)) if OUT.exists() else {}
prs, issues = old.get('prs_total'), old.get('issues_total')
if '--no-gh' not in sys.argv:
    prs = int(subprocess.run(['gh', 'api', 'repos/%s/pulls?state=all&per_page=100' % REPO, '--jq', 'length'], capture_output=True, text=True).stdout or prs)
    issues = int(subprocess.run(['gh', 'api', 'repos/%s/issues?state=all&per_page=100' % REPO, '--jq', '[.[]|select(.pull_request|not)]|length'], capture_output=True, text=True).stdout or issues)
json.dump({'snapshot_date': datetime.date.today().isoformat(), 'main_sha': git('rev-parse', 'origin/main').strip(), 'branches_total': len(branches), 'branches_unmerged': len(unmerged), 'prs_total': prs, 'issues_total': issues, 'branch_only_assets': bo}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('branches', len(branches), 'unmerged', len(unmerged), 'branches with branch-only images', len(bo), 'files', sum(len(b['files']) for b in bo), 'PR', prs, 'issues', issues)
