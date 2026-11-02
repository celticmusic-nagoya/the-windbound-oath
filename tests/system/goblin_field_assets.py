"""Candidate provenance/alpha protection and local branch audit negative controls."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
manifest = json.loads((ROOT / 'img/field/monsters/goblin/manifest.json').read_text())
assert manifest['status'] == 'CANDIDATE_NOT_APPROVED' and len(manifest['frames']) == 20
for frame in manifest['frames']:
    p = ROOT / frame['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == frame['sha256'], p
    im = Image.open(p)
    assert im.mode == 'RGBA' and im.size == (320, 320)
    assert im.getchannel('A').getextrema() == (0, 255)
    box = im.getchannel('A').point(lambda a: 255 if a > 32 else 0).getbbox()
    assert 0 < box[0] < box[2] < 320 and 0 < box[1] < box[3] < 320
assert hashlib.sha256((ROOT / manifest['reference']).read_bytes()).hexdigest() == manifest['reference_sha256']
reg = json.loads((ROOT / 'docs/assets/ASSET_REGISTRY.json').read_text())
candidate_paths = {f['path'] for f in manifest['frames']}
groups = [a for a in reg['assets'] if a['source_path'] in candidate_paths]
assert len(groups) == 5 and sum(a['frame_count'] for a in groups) == 20
assert {p for a in groups for p in a['frames']} == candidate_paths
assert all(a['approval_status'] == 'PENDING' and a['integration_status'] == 'BRANCH_ONLY' and a['android_status'] == 'UNVERIFIED' for a in groups)
with tempfile.TemporaryDirectory(prefix='goblin-audit-') as temp:
    dst = Path(temp)
    (dst / 'tools/assets').mkdir(parents=True)
    (dst / 'docs/assets').mkdir(parents=True)
    shutil.copy2(ROOT / 'tools/assets/audit_registry.py', dst / 'tools/assets/audit_registry.py')
    entry = copy.deepcopy(groups[0])
    for p in entry['frames']:
        (dst / p).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / p, dst / p)
    for p in entry['runtime_reference']:
        (dst / p).parent.mkdir(parents=True, exist_ok=True)
        (dst / p).write_text('// isolated reference target')
    subprocess.run(['git', 'init', '-q'], cwd=dst, check=True)
    subprocess.run(['git', 'add', 'img'], cwd=dst, check=True)
    def run():
        data = dict(reg, assets=[entry])
        (dst / 'docs/assets/ASSET_REGISTRY.json').write_text(json.dumps(data))
        return subprocess.run([sys.executable, 'tools/assets/audit_registry.py', '--no-fresh'], cwd=dst, capture_output=True, text=True)
    result = run()
    assert result.returncode == 0, result.stdout + result.stderr
    entry['frames_sha256'][0] = '0' * 64
    result = run()
    assert result.returncode == 1 and 'sha256 changed' in result.stdout, result.stdout + result.stderr
    entry['frames_sha256'][0] = groups[0]['frames_sha256'][0]
    (dst / entry['frames'][0]).unlink()
    result = run()
    assert result.returncode == 1 and 'not in the registry' in result.stdout, result.stdout + result.stderr
print('PASS 20 PNG/provenance/alpha; 5 candidate-only groups; corrupt hash and missing branch frame detected')
