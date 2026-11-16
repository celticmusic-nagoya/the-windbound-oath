"""Small deterministic task runner. Cache successes and failures; never auto-retry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'tools/map_pipeline/tasks.json'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def config():
    return json.loads(CONFIG.read_text())


def fingerprint(unit, runtime):
    c = config()
    assert c['units'][unit]['enabled'], 'unit disabled'
    for path, expected in [(c['source'], c['source_sha256']), (c['original'], c['original_sha256'])]:
        assert digest(ROOT / path) == expected, 'protected input SHA mismatch: ' + path
    paths = ['tools/map_pipeline/tasks.json', 'tools/map_pipeline/pipeline.py', 'tools/map_pipeline/blender_unit.py', c['history'], 'tools/map_blender/lind/blender-ubuntu24.04.sha256']
    payload = {'unit': unit, 'runtime': runtime, 'source': c['source_sha256'], 'original': c['original_sha256'], 'files': {p: digest(ROOT / p) for p in paths}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def validate(path, unit, sha):
    m = json.loads((path / 'state.json').read_text())
    assert m['unit'] == unit and m['input_sha256'] == sha
    assert m['status'] == 'PASS', 'unchanged failed input is blocked; inspect failure.json and change the cause before resuming'
    assert m['outputs'] and all(digest(path / p) == v for p, v in m['outputs'].items()), 'cached output SHA mismatch'
    assert json.loads((path / 'qa.json').read_text())['G3'] == 'PASS'
    assert m['output_sha256'] == hashlib.sha256(json.dumps(m['outputs'], sort_keys=True).encode()).hexdigest()
    return m


def run(unit, runtime, base):
    c = config()
    sha = fingerprint(unit, runtime)
    out = base / unit
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'state.json').exists():
        validate(out, unit, sha)
        print('REUSED', unit, sha)
        return
    # An interrupted cache cannot be mistaken for success or silently retried.
    assert not (out / 'started.json').exists(), 'incomplete attempt requires causal investigation'
    (out / 'started.json').write_text(json.dumps({'unit': unit, 'input_sha256': sha}))
    state = {'unit': unit, 'input_sha256': sha, 'dependencies': c['units'][unit]['dependencies'], 'method': c['method'], 'status': 'FAIL', 'G2': 'FAIL_INHERITED', 'G4': 'NOT_RUN'}
    try:
        actual = subprocess.check_output(['blender', '--version'], text=True).splitlines()[0]
        assert actual == 'Blender ' + runtime, actual
        with (out / 'build.log').open('w') as log:
            r = subprocess.run(['blender', '-b', '--disable-autoexec', str(ROOT / c['source']), '--python-exit-code', '1', '--python', str(ROOT / 'tools/map_pipeline/blender_unit.py'), '--', '--unit', unit, '--out', str(out.resolve())], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        assert r.returncode == 0, 'Blender failed with exit ' + str(r.returncode)
        qa = json.loads((out / 'qa.json').read_text())
        assert qa['G3'] == 'PASS'
        assert fingerprint(unit, runtime) == sha, 'input mutated during run'
        state['outputs'] = {p: digest(out / p) for p in ['unit.blend', 'preview.png', 'qa.json']}
        state['output_sha256'] = hashlib.sha256(json.dumps(state['outputs'], sort_keys=True).encode()).hexdigest()
        state['status'] = 'PASS'
    except Exception as e:
        log = out / 'build.log'
        tail = log.read_text(errors='replace').splitlines()[-35:] if log.exists() else []
        (out / 'failure.json').write_text(json.dumps({'unit': unit, 'input_sha256': sha, 'method': c['method'], 'cause': str(e), 'related_log_tail': tail, 'automatic_retry': False, 'resume': 'Codex: diagnose root cause; retain evidence; same geology family remains stopped'}, indent=2))
        raise
    finally:
        (out / 'state.json').write_text(json.dumps(state, indent=2) + '\n')


def integrate(base, runtime):
    c = config()
    assert c['approval']['evidence-integration'] is True
    rows = [validate(base / u, u, fingerprint(u, runtime)) for u in ['WORLD', 'ROUTE']]
    packet = {'schema': 1, 'stage': 'evidence-integration', 'status': 'PASS', 'scope': 'artifact integrity and limited technical QA only; no scene assembly/adoption', 'units': rows, 'G1': 'FULL_REVIEW_BLOCKED', 'G2': 'FAIL_INHERITED_NO_NEW_IMAGE_EVALUATION', 'G4': 'NOT_RUN', 'next': 'CODEX_REQUIRED: image evaluation and structurally different approved geology/support work', 'references': {u: str(base / u / 'preview.png') for u in ['WORLD', 'ROUTE']}}
    (base / 'handoff.json').write_text(json.dumps(packet, indent=2) + '\n')
    url = os.environ.get('GITHUB_SERVER_URL', 'https://github.com') + '/' + os.environ.get('GITHUB_REPOSITORY', 'celticmusic-nagoya/the-windbound-oath') + '/actions/runs/' + os.environ.get('GITHUB_RUN_ID', 'LOCAL')
    text = f'WORLD/ROUTE limited technical evidence PASS. G2 FAIL (inherited); G4 NOT_RUN.\n\nRun: {url}\n\n'
    for row in rows:
        text += f"- {row['unit']}: artifact `map-{row['unit']}-{row['input_sha256']}`; image `preview.png`; input `{row['input_sha256']}`; output `{row['output_sha256']}`\n"
    (base / 'references.md').write_text(text)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write(text)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['key', 'run', 'integrate'])
    p.add_argument('--unit', choices=['WORLD', 'ROUTE'], default='WORLD')
    p.add_argument('--runtime', default='4.0.2')
    p.add_argument('--base', type=Path, default=Path('.map-pipeline'))
    a = p.parse_args()
    if a.action == 'key':
        print(fingerprint(a.unit, a.runtime))
    elif a.action == 'run':
        run(a.unit, a.runtime, a.base)
    else:
        integrate(a.base, a.runtime)


if __name__ == '__main__':
    main()
