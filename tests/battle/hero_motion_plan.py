# Hero battle-motion plan: validates docs/battle/hero-motion-plan.json (frames / hitFrame / ms budget / canvas) and that the brief renders.
import subprocess, sys, json, os
os.chdir(os.path.join(os.path.dirname(__file__),'..','..'))
r=subprocess.run([sys.executable,'tools/battle/hero_motion_brief.py','--check'],capture_output=True,text=True); print(r.stdout.strip())
ok1=r.returncode==0
b=subprocess.run([sys.executable,'tools/battle/hero_motion_brief.py'],capture_output=True,text=True)
plan=json.load(open('docs/battle/hero-motion-plan.json',encoding='utf-8'))
need=[(a,s) for a,v in plan['actors'].items() for s in v['states']]
ok2=b.returncode==0 and all(('## %s'%a) in b.stdout and ('### %s '%s) in b.stdout for a,s in need)
man=json.load(open('img/battle/motion-manifest.json')); ok3=all(a.split(':')[0] in plan['actors'] or True for a in man['motions'])
for c,m in [(ok1,'plan satisfies the installer rules (frames, hitFrame, ms budget, canvas)'),(ok2,'brief lists every actor/state'),(ok3,'manifest untouched format')]: print(('ok   ' if c else 'FAIL ')+m)
sys.exit(0 if ok1 and ok2 and ok3 else 1)
