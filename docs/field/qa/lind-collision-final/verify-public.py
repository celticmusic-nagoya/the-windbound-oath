import re, json, hashlib, subprocess, concurrent.futures, os
from pathlib import Path
root=Path(__file__).resolve().parents[4]
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
html=(root/'index.html').read_text()
paths=['index.html']+re.findall(r'(?:src|href)=["\']((?:js|css)/[^"\']+\.(?:js|css))(?:\?[^"\']*)?["\']',html)
paths=sorted(set(paths+['js/field/lind-collision-footprints.js','js/field/lind-review.js','js/field/field-collision-debug.js','css/field-collision-debug.css']))
def check(p):
 data=subprocess.check_output(['curl','--fail','--silent','--show-error','https://celticmusic-nagoya.github.io/the-windbound-oath/'+p+'?qa='+commit])
 local=(root/p).read_bytes()
 return dict(file=p,sha256=hashlib.sha256(data).hexdigest(),matches=data==local)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: rows=list(pool.map(check,paths))
out=dict(commit=commit,public='https://celticmusic-nagoya.github.io/the-windbound-oath/',checked=len(rows),allMatch=all(r['matches'] for r in rows),files=rows)
output=Path(os.environ.get('FINAL_QA_OUT','/tmp/lind-collision-final'));output.mkdir(parents=True,exist_ok=True)
(output/'public-source.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='files'}))
assert out['allMatch'],[r for r in rows if not r['matches']]
