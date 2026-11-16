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
    c = json.loads(CONFIG.read_text())
    if c.get('profile') == 'production':
        for settings in c['units'].values():
            assert settings.get('art_status') != 'PASS', 'G2 PASS cannot be assigned by deterministic configuration'
    return c


def fingerprint(unit, runtime):
    c = config()
    assert c['units'][unit]['enabled'], 'unit disabled'
    for path, expected in [(c['source'], c['source_sha256']), (c['original'], c['original_sha256'])]:
        assert digest(ROOT / path) == expected, 'protected input SHA mismatch: ' + path
    paths = ['tools/map_pipeline/tasks.json', 'tools/map_pipeline/pipeline.py', 'tools/map_pipeline/blender_unit.py', c['history'], 'tools/map_blender/lind/blender-ubuntu24.04.sha256']
    if c.get('profile') == 'production':
        paths = ['tools/map_pipeline/pipeline.py', c['units'][unit]['producer'], c['qa_script'], c['interface'], c['history'], 'tools/map_blender/lind/blender-ubuntu24.04.sha256']
    payload = {'unit': unit, 'runtime': runtime, 'source': c['source_sha256'], 'original': c['original_sha256'], 'files': {p: digest(ROOT / p) for p in paths}}
    if c.get('profile') == 'production':
        payload['configuration'] = {k: v for k, v in c.items() if k != 'units'}
        payload['unit_configuration'] = c['units'][unit]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def validate(path, unit, sha):
    m = json.loads((path / 'state.json').read_text())
    assert m['unit'] == unit and m['input_sha256'] == sha
    assert m['status'] == 'PASS', 'unchanged failed input is blocked; inspect failure.json and change the cause before resuming'
    assert m['outputs'] and all(digest(path / p) == v for p, v in m['outputs'].items()), 'cached output SHA mismatch'
    qa = json.loads((path / 'qa.json').read_text())
    assert qa.get('technical_gate', qa['G3']) == 'PASS'
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
        production = c.get('profile') == 'production'
        command = ['blender', '-b', '--disable-autoexec', str(ROOT / c['source']), '--python-exit-code', '1', '--python', str(ROOT / 'tools/map_pipeline/blender_unit.py'), '--', '--unit', unit, '--out', str(out.resolve())]
        if production:
            command = ['blender', '-b', '--factory-startup', '--disable-autoexec', '--python-exit-code', '1', '--python', str(ROOT / c['units'][unit]['producer']), '--', '--out', str(out.resolve())]
        with (out / 'build.log').open('w') as log:
            r = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        assert r.returncode == 0, 'Blender failed with exit ' + str(r.returncode)
        if production:
            with (out / 'independent-qa.log').open('w') as log:
                r = subprocess.run(['blender', '-b', '--disable-autoexec', str((out / c['units'][unit]['blend']).resolve()), '--python-exit-code', '1', '--python', str(ROOT / c['qa_script']), '--', '--unit', unit, '--out', str(out.resolve())], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=900)
            assert r.returncode == 0, 'Independent saved-blend QA failed; inspect qa.json / independent-qa.log'
        qa = json.loads((out / 'qa.json').read_text())
        assert qa.get('technical_gate', qa['G3']) == 'PASS'
        assert fingerprint(unit, runtime) == sha, 'input mutated during run'
        names = ['unit.blend', 'preview.png', 'qa.json']
        if production:
            names = [c['units'][unit]['blend'], *c['units'][unit]['images'], 'settings.json', 'interface.json', 'manifest.json', 'qa.json']
            state.update({'method': c['units'][unit]['method'], 'G1': qa['G1'], 'G2': qa['G2'], 'G3': qa['G3'], 'dependencies': [{'interface': c['interface'], 'sha256': digest(ROOT / c['interface'])}]})
        state['outputs'] = {p: digest(out / p) for p in names}
        state['output_sha256'] = hashlib.sha256(json.dumps(state['outputs'], sort_keys=True).encode()).hexdigest()
        state['status'] = 'PASS'
    except Exception as e:
        log = out / 'build.log'
        if (out / 'independent-qa.log').exists():
            log = out / 'independent-qa.log'
        tail = log.read_text(errors='replace').splitlines()[-35:] if log.exists() else []
        (out / 'failure.json').write_text(json.dumps({'unit': unit, 'input_sha256': sha, 'method': c['units'][unit].get('method', c['method']), 'cause': str(e), 'related_log_tail': tail, 'automatic_retry': False, 'resume': 'Codex: diagnose root cause; retain evidence; same geology family remains stopped'}, indent=2))
        raise
    finally:
        (out / 'state.json').write_text(json.dumps(state, indent=2) + '\n')


def integrate(base, runtime):
    c = config()
    assert c['approval']['evidence-integration'] is True
    rows = [validate(base / u, u, fingerprint(u, runtime)) for u in ['WORLD', 'ROUTE']]
    packet = {'schema': 1, 'stage': 'evidence-integration', 'status': 'PASS', 'scope': 'artifact integrity and limited technical QA only; no scene assembly/adoption', 'units': rows, 'G1': 'FULL_REVIEW_BLOCKED', 'G2': 'FAIL_INHERITED_NO_NEW_IMAGE_EVALUATION', 'G4': 'NOT_RUN', 'next': 'CODEX_REQUIRED: image evaluation and structurally different approved geology/support work', 'references': {u: str(base / u / 'preview.png') for u in ['WORLD', 'ROUTE']}}
    if c.get('profile') == 'production':
        packet.update({'G2': 'FAIL_METHOD_FAMILIES_STOPPED; CI does not evaluate images', 'G3': 'PARTIAL_CHECKED_SUBSETS_ONLY', 'next': 'CODEX_REQUIRED: stopped art families cannot be retried; define structurally different method and approved interfaces before expansion', 'references': {u: [str(base / u / f) for f in c['units'][u]['images']] for u in ['WORLD', 'ROUTE']}})
    (base / 'handoff.json').write_text(json.dumps(packet, indent=2) + '\n')
    url = os.environ.get('GITHUB_SERVER_URL', 'https://github.com') + '/' + os.environ.get('GITHUB_REPOSITORY', 'celticmusic-nagoya/the-windbound-oath') + '/actions/runs/' + os.environ.get('GITHUB_RUN_ID', 'LOCAL')
    text = f"WORLD/ROUTE limited technical evidence PASS. G2 {packet['G2']}; G4 NOT_RUN.\n\nRun: {url}\n\n"
    for row in rows:
        images = ', '.join(c['units'][row['unit']]['images']) if c.get('profile') == 'production' else 'preview.png'
        text += f"- {row['unit']}: artifact `map-{row['unit']}-{row['input_sha256']}`; images `{images}`; input `{row['input_sha256']}`; output `{row['output_sha256']}`\n"
    (base / 'references.md').write_text(text)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write(text)


def main():
    global CONFIG
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['key', 'run', 'integrate'])
    p.add_argument('--unit', choices=['WORLD', 'ROUTE'], default='WORLD')
    p.add_argument('--runtime', default='4.0.2')
    p.add_argument('--base', type=Path, default=Path('.map-pipeline'))
    p.add_argument('--profile', choices=['evidence', 'production'], default='evidence')
    a = p.parse_args()
    if a.profile == 'production':
        CONFIG = ROOT / 'tools/map_pipeline/production_tasks.json'
    if a.action == 'key':
        print(fingerprint(a.unit, a.runtime))
    elif a.action == 'run':
        run(a.unit, a.runtime, a.base)
    else:
        integrate(a.base, a.runtime)


if __name__ == '__main__':
    main()
