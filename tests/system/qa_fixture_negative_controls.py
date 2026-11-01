"""26A: original regressions must exit nonzero on missing fixtures and injected faults."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ['QA_OUT']).resolve() if os.environ.get('QA_OUT') else None
if OUT:
    assert not OUT.is_relative_to(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
results = []
def run(name, command, marker, env=None, expected=1):
    proc = subprocess.run(command, cwd=ROOT, env={**os.environ, 'STARTUP_TEST_FILTER': '', 'CONTINUE_TEST_FILTER': '', **(env or {})}, capture_output=True, text=True, timeout=120)
    log = proc.stdout + proc.stderr
    ok = proc.returncode == expected and marker in log
    results.append({'case': name, 'exit_code': proc.returncode, 'expected_exit': expected, 'marker': marker, 'pass': ok})
    if OUT:
        (OUT / (name + '.log')).write_text(log)
        (OUT / 'negative-results.json').write_text(json.dumps(results, indent=2) + '\n')
    print(('ok   ' if ok else 'FAIL ') + name, flush=True)

run('strict-extraction-contract', ['node', '-e', """
const fs=require('node:fs'),assert=require('node:assert/strict'),{dialogueBlock,portraitBlock}=require('./tests/helpers/product-block.cjs');
const h=fs.readFileSync('index.html','utf8');
assert.ok(dialogueBlock(h.replace('say(t, portrait)','say(a,b,c)')).includes('say(a,b,c)'));
assert.ok(portraitBlock(h.replace('storyPortraitPage(sceneId, textId, pages, index)','storyPortraitPage(a,b,c,d,e)')).includes('storyPortraitPage(a,b,c,d,e)'));
for(const f of [dialogueBlock,portraitBlock])assert.throws(()=>f(''),/declaration not found/);
assert.throws(()=>dialogueBlock(h.replace('function closeDialogue(','function omittedClose(')),/missing closeDialogue/);
console.log('strict extraction contract PASS');
"""], 'strict extraction contract PASS', expected=0)
for fault, test, marker, env in [
    ('missing-say', 'startup_race', 'fixture: dialogue declaration not found', {}),
    ('missing-dialogue-end', 'startup_race', 'fixture: dialogue end not found', {}),
    ('missing-portrait', 'continue_restore', 'fixture: story portrait declaration not found', {}),
    ('stale-narration', 'startup_race', 'AssertionError', {'STARTUP_TEST_FILTER': 'a newer conversation that already ended'}),
    ('broken-restore', 'continue_restore', 'AssertionError', {'CONTINUE_TEST_FILTER': 'cold CONTINUE restores field'}),
]:
    run(fault, ['node', '-r', str(ROOT / 'tests/helpers/fixture_fault_preload.cjs'), 'tests/' + test + '.test.cjs'], marker, {**env, 'QA_FIXTURE_FAULT': fault})
for fault, marker in [('lost-android-pass', 'Android history mismatch'), ('forged-android-pass', 'undocumented Android claim'), ('wrong-verified-sha', 'Android history mismatch')]:
    run(fault, [sys.executable, 'tests/helpers/asset_history_fault.py', fault], marker)
fails = sum(not r['pass'] for r in results)
print('FAILS', fails)
raise SystemExit(bool(fails))
