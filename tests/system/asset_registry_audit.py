"""ASSET-REGISTRY-01: the registry is fresh, audit has no errors, references resolve, and the audit really detects problems (negative controls)."""
import json, subprocess, sys, shutil, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; fails = []
def check(ok, name, d=''):
    print(('ok   ' if ok else 'FAIL ') + name, d); 
    if not ok: fails.append(name)
def run(*a, cwd=ROOT): return subprocess.run([sys.executable, *a], cwd=cwd, capture_output=True, text=True)
check(run('tools/assets/build_registry.py', '--check').returncode == 0, 'registry is up to date with the repository')
r = run('tools/assets/audit_registry.py'); check(r.returncode == 0, 'audit_registry: no errors', r.stdout.strip()[-200:])
r = run('tools/assets/check_asset_refs.py'); check(r.returncode == 0, 'check_asset_refs: manifests / assets.js / maps resolve', r.stdout.strip()[-200:])
reg = json.load(open(ROOT / 'docs/assets/ASSET_REGISTRY.json', encoding='utf-8')); A = reg['assets']
check(len({a['asset_id'] for a in A}) == len(A), 'no duplicate asset ids')
need = ['asset_id','name','category','character','motion','delivery_date','source_path','source_branch','source_commit','source_sha256','width','height','frame_count','approval_status','implementation_status','integration_status','runtime_reference','arena_available','qa_status','android_status','issue','notes']
check(all(all(k in a for k in need) for a in A), 'every asset carries all registry fields')
check(all(a['android_status'] == 'UNVERIFIED' for a in A), 'no asset is claimed Android-verified')
check(not any(a['integration_status'] == 'MAIN' and a['source_branch'] not in ('main',) and a['asset_id'].startswith('branch:') for a in A), 'branch-only assets are never labelled MAIN')
p0 = [a for a in A if a['approval_status'] == 'APPROVED' and a['implementation_status'] == 'NOT_IMPLEMENTED']
check(any(a['character'] == 'goblin_raider' for a in p0) and any(a['asset_id'] == 'orig:lou_new_ko' for a in p0), 'approved-but-unimplemented extraction finds Raider sheets and Lou KO', len(p0))
check(not any(a['approval_status'] == 'APPROVED' for a in A if 'candidate' in a['source_path']), 'candidate sheets are never APPROVED automatically')
# negative controls on a scratch copy: audit must fail on a duplicate id and on a vanished MAIN file
tmp = Path(tempfile.mkdtemp()); (tmp / 'docs/assets').mkdir(parents=True); (tmp / 'tools/assets').mkdir(parents=True); (tmp / 'img').mkdir()
try:
    shutil.copy(ROOT / 'tools/assets/audit_registry.py', tmp / 'tools/assets/audit_registry.py')
    bad = json.loads(json.dumps(reg)); bad['assets'].append(dict(bad['assets'][0]))
    json.dump(bad, open(tmp / 'docs/assets/ASSET_REGISTRY.json', 'w')); subprocess.run(['git', 'init', '-q'], cwd=tmp)
    r = run('tools/assets/audit_registry.py', '--no-fresh', cwd=tmp); check(r.returncode == 1 and 'duplicate asset_id' in r.stdout, 'negative control: duplicate id is detected')
    check('MAIN but file missing' in r.stdout, 'negative control: missing MAIN file is detected')
finally: shutil.rmtree(tmp, ignore_errors=True)
print('FAILS', len(fails)); sys.exit(1 if fails else 0)
