"""INT-01D negative control: battle_loading_safety.py must DETECT deliberately broken product code.
For each mutation the product source is sabotaged on the fly (route rewrite inside the test browser; no file on disk changes) and the matching test group is run:
the run must FAIL, and the expected check name must be among the failures. The unmodified code must pass the same groups (baseline).
Usage: python3 tools/qa/battle_loading_mutation.py (kept under tools/qa so tests/run_all.sh, which runs every tests/**/*.py, does not run this ~25 min driver) [baseline] [mutation names...]   (default: baseline + all)"""
import os,subprocess,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'tests/battle'
# mutation -> (test group, substring that must appear in a FAILED check name, what the sabotage models)
PLAN={
 'notify_first':('A','A1 at the ready notification','ready is announced before the state is committed / the battle resumed (the old order)'),
 'double_ready':('A','A1 each Loading generation notifies ready exactly once','ready announced twice for one generation'),
 'global_pass':('A','A2','the pass stays valid for the whole resume (the old global flag)'),
 'reusable_pass':('A','A2 (same battle again)','the pass ticket is not consumed by its first use'),
 'nolock':('C','C2','Loading takes no input lock'),
 'early_release':('C','C3','Loading lock released before the opening has taken over'),
 'no_manifest_wait':('B','B1 manifest delayed 3200','Loading does not wait for the manifest (the old behaviour)'),
 'silent_manifest_failure':('B','B3','a failed manifest is treated as success'),
 'played_first':('B','B8','BattleOpening marks the battle as played before it knows playback is possible'),
}
def run(mut,group):
    env=dict(os.environ);env['ONLY']=group
    if mut:env['MUT']=mut
    r=subprocess.run([sys.executable,str(HERE/'battle_loading_safety.py')],env=env,capture_output=True,text=True,timeout=900)
    out=r.stdout;failed=[l[5:].strip() for l in out.splitlines() if l.startswith('FAIL ')]
    return r.returncode,failed,out
def main():
    args=sys.argv[1:];names=[a for a in args if a!='baseline'];do_base=(not args) or 'baseline' in args
    if not names and not (args and args==['baseline']):names=list(PLAN)
    bad=[]
    if do_base:
        for g in ('A','C','B'):
            rc,failed,out=run(None,g);ok=(rc==0 and not failed);print('baseline group %s: %s'%(g,'PASS' if ok else 'FAIL %s'%failed),flush=True)
            if not ok:bad.append('baseline '+g)
    for m in names:
        g,needle,why=PLAN[m];rc,failed,out=run(m,g)
        hit=[f for f in failed if needle in f]
        ok=(rc!=0 and bool(hit));print('mutation %-24s (%s) -> %s  [%s] failed checks: %d, expected one matching "%s": %s'%(m,g,'DETECTED' if ok else 'MISSED',why,len(failed),needle,'yes' if hit else 'no'),flush=True)
        if not ok:bad.append(m)
    print('MUTATION_RESULT','OK' if not bad else 'PROBLEMS %s'%bad)
    sys.exit(1 if bad else 0)
main()
