"""Verify archived bytes, metadata and enforced blocked registration (Pillow required)."""
from pathlib import Path
import hashlib
import json
import subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
for slug in ('aidan', 'liam', 'bram'):
    m = json.loads((ROOT / f'assets/characters/{slug}/layer0/MANIFEST.json').read_text())
    assert m['registration_status'] == 'BLOCKED'
    assert m['background_processing']['attempts'] == 2
    assert m['background_processing']['maximum_attempts'] == 2
    for record in [m['original'], *m['background_processing']['outputs']]:
        p = ROOT / record['path']
        assert hashlib.sha256(p.read_bytes()).hexdigest() == record['sha256'], p
        im = Image.open(p)
        assert list(im.size) == record['resolution'] and im.mode == record['mode'], p
        assert list(im.convert('RGBA').getchannel('A').getextrema()) == [record['alpha_min'], record['alpha_max']], p
    assert not (ROOT / m['master']['path']).exists()
    assert all(x['adoption'] == 'REJECTED' for x in m['background_processing']['outputs'])
    print(f'PASS {slug}: source/output hashes and metadata, 2/2 limit, rejected outputs excluded from master')
changes = subprocess.check_output(['git', 'diff', '--name-status', 'cab9aa52da653198a712bd986992adc03ea4bfe2'], cwd=ROOT, text=True).splitlines()
allowed = ('assets/characters/', 'assets/candidates/layer0-male-trio-register-01/', 'docs/qa/layer0-male-trio-register-01/')
assert all(line.startswith('A\t') and line.split('\t', 1)[1].startswith(allowed) for line in changes), changes
print('PASS existing baseline files unchanged; only task additions')
