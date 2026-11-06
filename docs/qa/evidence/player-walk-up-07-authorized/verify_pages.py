import argparse,urllib.request,json,hashlib,subprocess,datetime
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--sha',required=True);p.add_argument('--out',required=True);a=p.parse_args();root=Path('/workspace/work/player-walk-up-07-reqa/repo');base='https://celticmusic-nagoya.github.io/the-windbound-oath/';files=['index.html','js/field/aidan-field-assets.js','img/field/characters/aidan/up5/adopted-walk.json','img/field/characters/aidan/up5/aidan_walk_up_pushoff.png'];meta=json.loads(subprocess.check_output(['git','show',a.sha+':img/field/characters/aidan/up5/adopted-walk.json'],cwd=root));files+=list(dict.fromkeys(x['path'].split('?')[0] for x in meta['files'] if x['path'] not in files));rows=[]
for f in files:
 want=subprocess.check_output(['git','show',a.sha+':'+f],cwd=root);req=urllib.request.Request(base+f+'?verify='+a.sha[:12],headers={'User-Agent':'Codex-QA','Cache-Control':'no-cache'})
 try:
  got=urllib.request.urlopen(req,timeout=45).read();rows.append({'path':f,'expected_sha256':hashlib.sha256(want).hexdigest(),'public_sha256':hashlib.sha256(got).hexdigest(),'bytes':len(got),'equal':want==got})
 except Exception as e:rows.append({'path':f,'expected_sha256':hashlib.sha256(want).hexdigest(),'equal':False,'request_error':str(e)})
try:
 b=json.load(urllib.request.urlopen(urllib.request.Request('https://api.github.com/repos/celticmusic-nagoya/the-windbound-oath/pages/builds/latest',headers={'User-Agent':'Codex-QA'}),timeout=30));build={k:b.get(k) for k in ['status','commit','created_at','updated_at','error']}
except Exception as e:build={'api_error':str(e)}
o={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'main_sha':a.sha,'url':base,'files':rows,'all_files_match':all(x['equal'] for x in rows),'pages_build':build};Path(a.out).write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o));raise SystemExit(0 if o['all_files_match'] else 1)
