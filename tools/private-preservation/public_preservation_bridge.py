"""Public runner bootstrap. Only reviewed pilot archives, no public data output."""
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import subprocess
import tempfile
from release_transport import ReleaseTransport, TransportError, request as rest_request

SOURCE = 'celticmusic-nagoya/the-windbound-oath'
DEST = SOURCE + '-handoff'
ENGINE = 'tools/preserve_reviewed_artifacts.py'
ENGINE_BLOB = 'bab153f104c1f0de34fa403e0b08b6dd7cc00902'
QUEUE = 'reports/preservation/PENDING_ORIGINAL_ARCHIVES_20261125.json'
BATCH_REQUEST = 'approved_batch.json'
EXPECTED = dict(GITHUB_REPOSITORY=SOURCE, GITHUB_REF='refs/heads/main',
                GITHUB_EVENT_NAME='workflow_dispatch', GITHUB_ACTOR='celticmusic-nagoya',
                GITHUB_TRIGGERING_ACTOR='celticmusic-nagoya', CONFIRM_WRITE='PRESERVE_REVIEWED_PILOT')
AUTO_EXPECTED = dict(EXPECTED, GITHUB_EVENT_NAME='push', CONFIRM_WRITE='PRESERVE_REVIEWED_MAIN_PUSH',
                     GITHUB_RUN_ATTEMPT='1', DIAGNOSE_ONLY='false',
                     GITHUB_WORKFLOW_REF=SOURCE+'/.github/workflows/public-preservation-pilot.yml@refs/heads/main')
STAGES = frozenset(('RUNNER', 'DEST_ACCESS', 'DEST_REF', 'ENGINE_PIN', 'REVIEW_QUEUE',
                    'ENGINE_IMPORT', 'RELEASE_PREFLIGHT', 'SOURCE_META', 'SOURCE_ZIP', 'TRANSFER', 'RELEASE_CREATE',
                    'RELEASE_UPLOAD', 'RELEASE_DRAFT_READBACK', 'RELEASE_PUBLISH', 'RELEASE_FINAL_READBACK'))
STAGE = 'RUNNER'

class ApiError(ValueError):
    def __init__(self, status):
        self.status = status if status in (400,401,403,404,409,422,429,500,502,503,504) else 0
        super().__init__('API request failed')

def stage(name):
    global STAGE
    if name not in STAGES:
        raise ValueError('invalid stage')
    STAGE = name

def require(ok):
    if not ok:
        raise ValueError('bridge validation failed')

def api(token, endpoint, output=None):
    env = dict(os.environ, GH_TOKEN=token, GH_PROMPT_DISABLED='1')
    p = subprocess.run(['gh', 'api', endpoint], env=env,
                       stdout=subprocess.PIPE if output is None else output,
                       stderr=subprocess.PIPE, check=False)
    if p.returncode:
        matches = re.findall(rb'HTTP ([0-9]{3})\b', p.stderr)
        raise ApiError(int(matches[-1]) if matches else 0)
    return json.loads(p.stdout) if output is None else None

def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def read_file(token, target, path, expected=None):
    obj = api(token, f'repos/{DEST}/contents/{path}?ref={target}')
    require(obj.get('type') == 'file' and obj.get('path') == path and obj.get('encoding') == 'base64')
    require(type(obj.get('size')) is int and 0 < obj['size'] <= 65536)
    data = base64.b64decode(''.join(obj['content'].split()), validate=True)
    require(len(data) == obj['size'] and git_blob(data) == obj.get('sha'))
    require(expected is None or obj['sha'] == expected)
    return data

def select_pilot(queue, ids):
    require(queue.get('source_repository') == SOURCE and isinstance(queue.get('items'), list))
    rows = []
    for aid in ids:
        found = [x for x in queue['items'] if isinstance(x, dict) and x.get('artifact_id') == aid]
        require(len(found) == 1 and found[0].get('rights') == 'APPROVED_PRIVATE_COPY')
        rows.append(found[0])
    return rows

def absent(token, endpoint):
    try:
        api(token, endpoint)
    except ApiError as exc:
        if exc.status == 404:
            return True
        raise
    return False

def preflight(module, rows, source, dest, root):
    stage('RELEASE_PREFLIGHT')
    existing = set(module.gh(dest, ['api', '--paginate', f'repos/{DEST}/releases?per_page=100', '--jq', '.[].tag_name']).decode().splitlines())
    for item in rows:
        aid = item['artifact_id']
        tag = f'preserved-artifact-{aid}'
        stage('RELEASE_PREFLIGHT')
        require(tag not in existing and absent(dest, f'repos/{DEST}/releases/tags/{tag}') and absent(dest, f'repos/{DEST}/git/ref/tags/{tag}'))
        stage('SOURCE_META')
        endpoint = f'repos/{SOURCE}/actions/artifacts/{aid}'
        module.verify_meta(item, api(source, endpoint))
        stage('SOURCE_ZIP')
        path = root / f'{aid}.zip'
        with path.open('xb') as f:
            api(source, endpoint + '/zip', output=f)
        module.verify_zip(path, item)

def read_batch_request(path=None):
    path = path or pathlib.Path(__file__).with_name(BATCH_REQUEST)
    require(path.is_file() and 0 < path.stat().st_size <= 4096)
    batch = json.loads(path.read_bytes())
    require(isinstance(batch, dict) and set(batch) == {'artifact_ids', 'reviewed_queue_blob', 'operation'})
    ids = batch['artifact_ids']
    require(isinstance(ids, list) and 1 <= len(ids) <= 13)
    require(all(type(i) is int and i > 0 and i != 14602858760 for i in ids) and len(set(ids)) == len(ids))
    require(batch['operation'] in ('preserve', 'verify_existing'))
    pin = batch['reviewed_queue_blob']
    require(isinstance(pin, str) and re.fullmatch('[0-9a-f]{40}', pin))
    return batch

def verify_existing(module, rows, dest, root):
    for item in rows:
        stage('RELEASE_PREFLIGHT')
        tag = f"preserved-artifact-{item['artifact_id']}"
        name = f"{item['artifact_id']}.zip"
        release = api(dest, f'repos/{DEST}/releases/tags/{tag}')
        require(release.get('tag_name') == tag and release.get('draft') is False and release.get('prerelease') is True)
        assets = release.get('assets')
        require(isinstance(assets, list) and len(assets) == 1)
        asset = assets[0]
        aid = asset.get('id')
        require(type(aid) is int and aid > 0 and asset.get('state') == 'uploaded' and asset.get('name') == name and asset.get('size') == item['bytes'] and asset.get('digest') == 'sha256:'+item['sha256'])
        stage('RELEASE_FINAL_READBACK')
        data = rest_request(dest, 'GET', f'https://api.github.com/repos/{DEST}/releases/assets/{aid}', binary=True, limit=item['bytes'])
        path = root/name
        with path.open('xb') as f:
            f.write(data)
        module.verify_zip(path, item)

def run():
    stage('RUNNER')
    auto = all(os.environ.get(k) == v for k, v in AUTO_EXPECTED.items())
    require(auto or all(os.environ.get(k) == v for k, v in EXPECTED.items()))
    batch = read_batch_request()
    source, dest = os.environ.get('SOURCE_TOKEN'), os.environ.get('DEST_TOKEN')
    require(source and dest and source != dest)
    mode = os.environ.get('DIAGNOSE_ONLY', 'true')
    require(mode in ('true', 'false'))
    stage('DEST_ACCESS')
    repo = api(dest, f'repos/{DEST}')
    require(repo.get('full_name') == DEST and repo.get('private') is True)
    stage('DEST_REF')
    ref = api(dest, f'repos/{DEST}/git/ref/heads/main')
    target = ref.get('object', {}).get('sha', '')
    require(ref.get('ref') == 'refs/heads/main' and ref.get('object', {}).get('type') == 'commit' and re.fullmatch('[0-9a-f]{40}', target))
    stage('ENGINE_PIN')
    engine = read_file(dest, target, ENGINE, ENGINE_BLOB)
    stage('REVIEW_QUEUE')
    queue = json.loads(read_file(dest, target, QUEUE, batch['reviewed_queue_blob']))
    rows = select_pilot(queue, batch['artifact_ids'])
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        path = root/'engine.py'
        path.write_bytes(engine)
        stage('ENGINE_IMPORT')
        spec = importlib.util.spec_from_file_location('private_engine', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.require_reviewed_queue(rows, queue)
        if batch['operation'] == 'verify_existing':
            verify_existing(module, rows, dest, root)
            return 'EXISTING_READBACK'
        if mode == 'true':
            preflight(module, rows, source, dest, root)
        else:
            stage('TRANSFER')
            module.gh = ReleaseTransport(module.gh, dest, stage)
            module.preserve(rows, source, dest, target, public_bridge=True)

def main():
    # Only fixed stage codes and allowlisted HTTP status numbers reach public logs.
    stage('RUNNER')
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = run()
    except Exception as exc:
        status = exc.status if isinstance(exc, (ApiError, TransportError)) else 0
        print('PILOT_BLOCKED: stage=' + (STAGE if STAGE in STAGES else 'RUNNER') + ' http=' + str(status))
        return 1
    if result == 'EXISTING_READBACK':
        print('PILOT_EXISTING_READBACK_VERIFIED: no remote writes')
        return 0
    print('PILOT_PREFLIGHT_VERIFIED: no remote writes' if os.environ.get('DIAGNOSE_ONLY','true') == 'true' else 'PILOT_READBACK_VERIFIED: confirm private release metadata separately')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
