import subprocess,sys,json
from pathlib import Path
args=sys.argv[1:];idx=args.index('--out')+1;out=Path(args[idx]);results=[]
for round_id in (1,2,3):
 call=args.copy();call[idx]=str(out/f'round-{round_id}');p=subprocess.run([sys.executable,'-u',str(Path(__file__).with_name('run.py')),*call]);results.append({'round':round_id,'exit_code':p.returncode})
out.mkdir(exist_ok=True);(out/'repeat-results.json').write_text(json.dumps(results,indent=2)+'\n');sys.exit(0 if all(r['exit_code']==0 for r in results) else 1)
