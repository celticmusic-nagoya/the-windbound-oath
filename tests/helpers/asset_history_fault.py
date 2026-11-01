"""Run the actual asset regression with one in-memory false registry record."""
import builtins
import io
import json
import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
registry = root / 'docs/assets/ASSET_REGISTRY.json'
data = json.loads(registry.read_text())
fault = sys.argv[1]
if fault == 'lost-android-pass':
    next(a for a in data['assets'] if a['android_status'] == 'PASS')['android_status'] = 'UNVERIFIED'
elif fault == 'forged-android-pass':
    next(a for a in data['assets'] if a['android_status'] == 'UNVERIFIED')['android_status'] = 'PASS'
elif fault == 'wrong-verified-sha':
    next(a for a in data['assets'] if a['android_status'] == 'PASS')['source_sha256'] = '0' * 64
else:
    raise ValueError('unknown asset fault')
print('INJECTED ' + fault, file=sys.stderr)
original_open = builtins.open
def patched_open(file, *args, **kwargs):
    if isinstance(file, (str, Path)) and Path(file).resolve() == registry:
        return io.StringIO(json.dumps(data))
    return original_open(file, *args, **kwargs)
builtins.open = patched_open
sys.argv = [str(root / 'tests/system/asset_registry_audit.py')]
runpy.run_path(sys.argv[0], run_name='__main__')
