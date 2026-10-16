"""INT-01D negative control for the three formerly always-true test conditions.
For each of them the driver runs the test with an ABNORMAL state injected (NEG=1) in two forms:
  old form (the vacuous expression put back, in a temporary copy) -> must PASS  = the old test missed the fault
  fixed form (the real test)                                      -> must FAIL  = the fixed test detects it
The fixed test without NEG=1 is the normal regression (must pass); it is run by the regular suite, not here.
Usage: python3 tools/qa/battle_loading_negative_control.py (under tools/qa so tests/run_all.sh does not pick it up) [loading|input|async]"""
import os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'tests/battle'
CASES={
 'loading':('battle_loading.py',"""pg.evaluate("window.__open")==1,'duplicate trigger: single battle start (exactly one opening)'""","""pg.evaluate("BattleOpening?1:0")==1,'duplicate trigger: single battle start (exactly one opening)'""",'duplicate trigger: single battle start','a second battle-opening is fired (double start)'),
 'input':('battle_loading_input.py',"check(exp,'%s: a real command is accepted after Loading (its effect is measured)'","check(st1!=st0 or kind=='normal','%s: a real command is accepted after Loading (its effect is measured)'",'normal: a real command is accepted after Loading','the game command silently does nothing (normal battle)'),
 'async':('battle_loading_async.py',"check(pg.evaluate(MODE)=='raider' and pg.evaluate('BattlePresentation.busy') is False,","check(pg.evaluate(MODE)=='raider' and pg.evaluate('BattlePresentation.busy') is False or True,",'S6 next battle started','the next battle is not running'),
}
def run(script,extra):
    env=dict(os.environ);env.update(NEG='1',NEG_STOP='1',**extra)
    r=subprocess.run([sys.executable,str(HERE/script)],env=env,capture_output=True,text=True,timeout=900,cwd=str(ROOT))
    return r.returncode,[l[5:].strip() for l in r.stdout.splitlines() if l.startswith('FAIL ')]
def main():
    which=sys.argv[1:] or list(CASES);bad=[]
    for k in which:
        script,new,old,needle,fault=CASES[k];src=(HERE/script).read_text()
        assert new in src,'fixed expression not found: '+k
        tmp=HERE/('_neg_old_'+script);tmp.write_text(src.replace(new,old,1))
        try:
            rc_old,f_old=run(tmp.name,{})
        finally:
            tmp.unlink()
        rc_new,f_new=run(script,{})
        missed=not any(needle in f for f in f_old);detected=any(needle in f for f in f_new)
        print('%-8s fault: %-55s old expression: %s | fixed test: %s'%(k,fault,'MISSED (passes)' if missed else 'detected','DETECTED (fails)' if detected else 'MISSED'),flush=True)
        if not (missed and detected):bad.append(k)
    print('NEGATIVE_CONTROL','OK' if not bad else 'PROBLEMS %s'%bad);sys.exit(1 if bad else 0)
main()
