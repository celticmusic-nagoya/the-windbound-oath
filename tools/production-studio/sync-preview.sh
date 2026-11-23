#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p "$RUNNER_TEMP/studio-zips" "$RUNNER_TEMP/studio-site"
python discover-gallery.py
python - <<'PY'
import json, subprocess, os
from pathlib import Path
selection=json.load(open(Path(os.environ['RUNNER_TEMP'])/'studio-discovered.json'))
assert len(selection)<=20
active=[]
for x in selection:
    a=x['artifact_id']; run=x['run_id']
    assert type(a)==int and type(run)==int and min(a,run)>0
    repo=os.environ['GITHUB_REPOSITORY']
    meta=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/actions/artifacts/{a}']))
    if meta['expired']:
        print(f'Artifact {a} expired; retaining previously published copy if available')
        continue
    assert meta['workflow_run']['id']==run and meta['workflow_run']['head_sha']==x['head']
    assert 0 < meta['size_in_bytes'] <= 128*1024*1024
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
    assert target.stat().st_size <= 128*1024*1024
    active.append(x)
(Path(os.environ['RUNNER_TEMP'])/'studio-selection.json').write_text(json.dumps(active))
PY
python artifact-sync.py "$RUNNER_TEMP/studio-selection.json" "$RUNNER_TEMP/studio-zips" "$RUNNER_TEMP/studio-site/published"
python stage-village.py
npm install --ignore-scripts --no-audit --no-fund
cp -t "$RUNNER_TEMP/studio-site" index.html studio.css studio.js model-inspector.js model-viewer.js artifact-verify.js zip-preview.js gallery-sync.js
mkdir -p "$RUNNER_TEMP/studio-site/vendor/three"
cp -r node_modules/three/{build,examples,LICENSE} "$RUNNER_TEMP/studio-site/vendor/three/"
sed -i 's@./node_modules/three/@./vendor/three/@g' "$RUNNER_TEMP/studio-site/index.html"
