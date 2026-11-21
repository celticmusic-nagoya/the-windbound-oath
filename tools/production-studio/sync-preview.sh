#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p "$RUNNER_TEMP/studio-zips" "$RUNNER_TEMP/studio-site"
python - <<'PY'
import json, subprocess, os
from pathlib import Path
for x in json.load(open('sync-selection.json')):
    a=x['artifact_id']; run=x['run_id']
    assert type(a)==int and type(run)==int and min(a,run)>0
    repo=os.environ['GITHUB_REPOSITORY']
    meta=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/actions/artifacts/{a}']))
    assert not meta['expired'] and meta['workflow_run']['id']==run and meta['workflow_run']['head_sha']==x['head']
    target=Path(os.environ['RUNNER_TEMP'])/'studio-zips'/f'{a}.zip'
    subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{a}/zip'],stdout=target.open('wb'),check=True)
    import hashlib
    digest=meta.get('digest','')
    assert digest.startswith('sha256:') and hashlib.file_digest(target.open('rb'),'sha256').hexdigest()==digest[7:]
PY
python artifact-sync.py sync-selection.json "$RUNNER_TEMP/studio-zips" "$RUNNER_TEMP/studio-site/published"
npm install --ignore-scripts --no-audit --no-fund
cp -t "$RUNNER_TEMP/studio-site" index.html studio.css studio.js model-inspector.js model-viewer.js artifact-verify.js zip-preview.js gallery-sync.js
mkdir -p "$RUNNER_TEMP/studio-site/vendor/three"
cp -r node_modules/three/{build,examples,LICENSE} "$RUNNER_TEMP/studio-site/vendor/three/"
sed -i 's@./node_modules/three/@./vendor/three/@g' "$RUNNER_TEMP/studio-site/index.html"
