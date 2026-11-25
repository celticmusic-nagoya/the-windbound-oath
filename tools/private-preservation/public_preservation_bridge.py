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

SOURCE = 'celticmusic-nagoya/the-windbound-oath'
DEST = SOURCE + '-handoff'
ENGINE = 'tools/preserve_reviewed_artifacts.py'
ENGINE_BLOB = '56e8aa0c4f2e9972504d0149d0320632e13aece5'
QUEUE = 'reports/preservation/PENDING_ORIGINAL_ARCHIVES_20261125.json'
PILOT = (15018392749, 15020595762)
EXPECTED = dict(GITHUB_REPOSITORY=SOURCE, GITHUB_REF='refs/heads/main',
                GITHUB_EVENT_NAME='workflow_dispatch', GITHUB_ACTOR='celticmusic-nagoya',
                GITHUB_TRIGGERING_ACTOR='celticmusic-nagoya', CONFIRM_WRITE='PRESERVE_REVIEWED_PILOT')

def require(ok):
    if not ok:
        raise ValueError('bridge validation failed')

def api(token, endpoint):
    env = dict(os.environ, GH_TOKEN=token, GH_PROMPT_DISABLED='1')
    p = subprocess.run(['gh', 'api', endpoint], env=env, capture_output=True, check=False)
    require(p.returncode == 0)
    return json.loads(p.stdout)

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

def select_pilot(queue):
    require(queue.get('source_repository') == SOURCE and isinstance(queue.get('items'), list))
    rows = []
    for aid in PILOT:
        found = [x for x in queue['items'] if isinstance(x, dict) and x.get('artifact_id') == aid]
        require(len(found) == 1 and found[0].get('rights') == 'APPROVED_PRIVATE_COPY')
        rows.append(found[0])
    return rows

def run():
    require(all(os.environ.get(k) == v for k, v in EXPECTED.items()))
    source, dest = os.environ.get('SOURCE_TOKEN'), os.environ.get('DEST_TOKEN')
    require(source and dest and source != dest)
    repo = api(dest, f'repos/{DEST}')
    require(repo.get('full_name') == DEST and repo.get('private') is True)
    ref = api(dest, f'repos/{DEST}/git/ref/heads/main')
    target = ref.get('object', {}).get('sha', '')
    require(ref.get('ref') == 'refs/heads/main' and ref.get('object', {}).get('type') == 'commit' and re.fullmatch('[0-9a-f]{40}', target))
    engine = read_file(dest, target, ENGINE, ENGINE_BLOB)
    queue = json.loads(read_file(dest, target, QUEUE))
    rows = select_pilot(queue)
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp)/'engine.py'
        path.write_bytes(engine)
        spec = importlib.util.spec_from_file_location('private_engine', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.require_reviewed_queue(rows, queue)
        module.preserve(rows, source, dest, target, public_bridge=True)

def main():
    # Never print private API bodies, paths, exceptions, or the private engine receipts.
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            run()
    except Exception:
        print('PILOT_BLOCKED: inspect private release state before any retry')
        return 1
    print('PILOT_READBACK_VERIFIED: confirm private release metadata separately')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
