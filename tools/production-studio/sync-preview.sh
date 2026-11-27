#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p "$RUNNER_TEMP/studio-zips" "$RUNNER_TEMP/studio-site"
git fetch --no-tags --depth=1 origin refs/heads/studio-published
git show FETCH_HEAD:gallery-manifest.json > "$RUNNER_TEMP/studio-published-history.json"
python discover-gallery.py --published-history "$RUNNER_TEMP/studio-published-history.json"
python - <<'PY'
import json, subprocess, os
from datetime import datetime, timezone
from pathlib import Path
from artifact_availability import recorded_expired_404, retained_receipt_matches, archive_budget, reusable_group_kind
selection=json.load(open(Path(os.environ['RUNNER_TEMP'])/'studio-discovered.json'))
active=[]
reused=[]
approvals=json.loads(Path('publication-approvals.json').read_text())
history=json.loads((Path(os.environ['RUNNER_TEMP'])/'studio-published-history.json').read_text())
kinds={x['artifact_id']:reusable_group_kind(x,history,approvals) for x in selection}
assert len(kinds)==len(selection), 'duplicate discovered artifact'
assert sum(kind is None for kind in kinds.values())<=36, 'active selection exceeds budget'
for x in selection:
    a=x['artifact_id']; run=x['run_id']
    assert type(a)==int and type(run)==int and min(a,run)>0
    repo=os.environ['GITHUB_REPOSITORY']
    budget=archive_budget(x)
    if kinds[a]=='legacy':
        print(f'REUSED: artifact {a} exact published entries; downstream merge rehashes retained images')
        continue
    if kinds[a]=='ordinary':
        print(f'REUSED: artifact {a} exact approved published images; downstream merge rehashes retained files')
        reused.append(a)
        continue
    try:
        meta=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/actions/artifacts/{a}'],stderr=subprocess.PIPE))
    except subprocess.CalledProcessError as exc:
        stderr=exc.stderr.decode('utf-8',errors='replace')
        if not recorded_expired_404(x,stderr,datetime.now(timezone.utc)):
            raise
        if not retained_receipt_matches(x,history):
            raise ValueError(f'expired artifact {a}: exact published history not found') from exc
        print(f'NOT_RUN: artifact {a} recorded expiry elapsed and HTTP 404; exact historical entries retained by downstream SHA verification')
        continue
    if meta['expired']:
        print(f'Artifact {a} expired; retaining previously published copy if available')
        continue
    assert meta['workflow_run']['id']==run and meta['workflow_run']['head_sha']==x['head']
    assert 0 < meta['size_in_bytes'] <= budget
    if 'exact_archive_bytes' in x:
        assert meta['size_in_bytes']==budget
    x['created_at']=meta['created_at']
    target=Path(os.environ['RUNNER_TEMP'])/'studio-zips'/f'{a}.zip'
    if not target.exists():
        with target.open('wb') as out:
            subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{a}/zip'],stdout=out,check=True)
    import hashlib
    digest=meta.get('digest','')
    expected=x.get('artifact_digest')
    if expected is not None:
        assert isinstance(expected,str) and len(expected)==71 and expected.startswith('sha256:'), 'invalid pinned archive digest'
        assert digest==expected, f'archive digest changed: {a}'
    assert digest.startswith('sha256:') and hashlib.file_digest(target.open('rb'),'sha256').hexdigest()==digest[7:]
    assert target.stat().st_size <= budget
    if 'exact_archive_bytes' in x:
        assert target.stat().st_size==budget
    active.append(x)
print(f'SYNC: reused {len(reused)} ordinary groups; staged {len(active)} groups (legacy exception separate)')
(Path(os.environ['RUNNER_TEMP'])/'studio-selection.json').write_text(json.dumps(active))
PY
python artifact-sync.py "$RUNNER_TEMP/studio-selection.json" "$RUNNER_TEMP/studio-zips" "$RUNNER_TEMP/studio-site/published"
python stage-village.py
npm install --ignore-scripts --no-audit --no-fund
cp -t "$RUNNER_TEMP/studio-site" index.html studio.css studio-ux.css studio.js handoff-readiness.js model-inspector.js model-viewer.js artifact-verify.js zip-preview.js gallery-sync.js recent-review-artifacts.js
mkdir -p "$RUNNER_TEMP/studio-site/vendor/three"
cp -r node_modules/three/{build,examples,LICENSE} "$RUNNER_TEMP/studio-site/vendor/three/"
sed -i 's@./node_modules/three/@./vendor/three/@g' "$RUNNER_TEMP/studio-site/index.html"
