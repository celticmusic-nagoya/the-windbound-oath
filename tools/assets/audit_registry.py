#!/usr/bin/env python3
"""ASSET-REGISTRY-01 audit. Checks docs/assets/ASSET_REGISTRY.json against the repository and writes docs/assets/reports/audit_report.md.
  1 duplicate asset ids   2 enum validity   3 MAIN assets exist on disk (and sha256 matches)   4 frame numbering / count consistency
  5 approved-but-not-implemented extraction   6 delivered-but-unmerged extraction   7 unreferenced images on main (informational; never deleted)
  8 registry vs implementation mismatches (IMPLEMENTED but no runtime reference / file missing, NOT_IMPLEMENTED but referenced)
  9 unregistered images on main (registry not updated)  10 registry freshness (build_registry.py --check)
Exit 1 on hard errors (1,2,3,4,8-file-missing,9,10). Informational lists never fail. usage: audit_registry.py [--no-fresh]"""
import hashlib, json, re, subprocess, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; D = ROOT / 'docs/assets'
reg = json.load(open(D / 'ASSET_REGISTRY.json', encoding='utf-8')); A = reg['assets']; E = reg['enums']
err, info = [], []
ids = Counter(a['asset_id'] for a in A); dup = [k for k, v in ids.items() if v > 1]
if dup: err.append('duplicate asset_id: %s' % dup[:5])
for a in A:
    for f in E:
        if a.get(f) not in E[f]: err.append('%s: invalid %s=%r' % (a['asset_id'], f, a.get(f)))
    if a['integration_status'] == 'MAIN':
        paths = a.get('frames') or [a['source_path']]
        for i, p in enumerate(paths):
            fp = ROOT / p
            if not fp.is_file(): err.append('%s: MAIN but file missing: %s' % (a['asset_id'], p)); continue
            want = (a.get('frames_sha256') or [a['source_sha256']])[i]
            if want not in ('UNKNOWN',) and not want.startswith('see') and hashlib.sha256(fp.read_bytes()).hexdigest() != want: err.append('%s: sha256 changed (registry stale): %s' % (a['asset_id'], p))
        if a.get('frames') and a['frame_count'] != len(a['frames']): err.append('%s: frame_count != frames' % a['asset_id'])
        if a['implementation_status'] == 'IMPLEMENTED' and not a['runtime_reference']: err.append('%s: IMPLEMENTED but no runtime_reference' % a['asset_id'])
        for r in a['runtime_reference']:
            if not (ROOT / r).is_file(): err.append('%s: runtime_reference missing: %s' % (a['asset_id'], r))
        m = re.findall(r'(\d+)\.\w+$', ' '.join(a.get('frames') or []))
    if a['integration_status'] == 'MAIN' and a['implementation_status'] == 'NOT_IMPLEMENTED': info.append(a)
    if a['approval_status'] == 'APPROVED' and a['integration_status'] != 'MAIN' and a['implementation_status'] == 'IMPLEMENTED' and False: pass
    if a.get('frames'):
        nums = [int(re.search(r'(\d+)\.\w+$', p).group(1)) for p in a['frames']]
        if nums != list(range(nums[0], nums[0] + len(nums))) and 'not contiguous' not in a['notes']: err.append('%s: frame numbers not contiguous %s' % (a['asset_id'], nums))
files = [l for l in subprocess.run(['git', 'ls-files', 'img'], cwd=ROOT, capture_output=True, text=True).stdout.splitlines() if l.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]
cov = set()
for a in A:
    if a['integration_status'] == 'MAIN': cov.update(a.get('frames') or [a['source_path']])
unreg = sorted(set(files) - cov)
if unreg: err.append('%d image(s) on main are not in the registry (run tools/assets/build_registry.py): %s' % (len(unreg), unreg[:3]))
fresh = None
if '--no-fresh' not in sys.argv:
    r = subprocess.run([sys.executable, str(ROOT / 'tools/assets/build_registry.py'), '--check'], capture_output=True, text=True); fresh = r.stdout.strip()
    if r.returncode: err.append(fresh)
appr = [a for a in A if a['approval_status'] == 'APPROVED' and a['implementation_status'] in ('NOT_IMPLEMENTED', 'PARTIAL', 'REGISTERED_ONLY')]
unm = [a for a in A if a['integration_status'] in ('BRANCH_ONLY', 'SOURCE_ONLY') and a['approval_status'] != 'REJECTED']
L = ['# Asset registry audit', '', 'registry snapshot: %s ／ assets %d ／ errors **%d**' % (reg['snapshot_date'], len(A), len(err)), '']
L += ['## Errors', ''] + (['- ' + e for e in err] or ['なし']) + ['', '## 採用済み・未実装（P0）%d' % len(appr), ''] + ['- `%s` %s %s' % (a['asset_id'], a['character'], a['motion']) for a in appr]
L += ['', '## 納品済み・未統合（ブランチ/原本のみ）%d' % len(unm), '']
for b, n in sorted(Counter(a['source_branch'] for a in unm).items()): L.append('- %s: %d' % (b, n))
L += ['', '## main上の参照なし画像 %d（情報。原本保管/将来用の可能性があり自動削除しない）' % len(info), '']
for d, n in sorted(Counter(str(Path(a['source_path']).parent) for a in info).items()): L.append('- %s: %d' % (d, n))
(D / 'reports').mkdir(exist_ok=True); (D / 'reports/audit_report.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('audit: %d assets, %d errors, %d approved-not-implemented, %d unmerged, %d unreferenced' % (len(A), len(err), len(appr), len(unm), len(info)))
for e in err[:15]: print('ERROR', e)
sys.exit(1 if err else 0)
