import subprocess,os,time,json,re,threading,http.server,functools,hashlib
from pathlib import Path
R=Path('/workspace/work/player-walk-up-06-qa/repo');O=R.parent/'independent-runtime';S=R.parent/'independent-screens';S.mkdir(exist_ok=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();paths=['tests/moss/m66_up06_independent.py','tests/moss/m62_aidan_down_production.py','tests/moss/m58_aidan_side_stride.py','tests/moss/m55_dev_walk_motion.py','tests/system/save_continue_lifecycle.py','tests/system/asset_registry_audit.py','tests/moss/m49_phase4_formal_adoption.py'];rows=[]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
for path in paths:
 server=None;before=hashlib.sha256((R/path).read_bytes()).hexdigest();start=time.monotonic();env=dict(os.environ,QA_OUT=str(S),QA_GAMEPLAY_BOOT='1',PW_CHROMIUM_EXECUTABLE='/usr/bin/chromium',PLAYWRIGHT_BROWSERS_PATH='/workspace/work/dev-walk-cycle-a01/playwright');log=O/(Path(path).name+'.log');print('RUN '+path,flush=True)
 if path.endswith('save_continue_lifecycle.py'):
  server=http.server.ThreadingHTTPServer(('127.0.0.1',8765),functools.partial(Quiet,directory=str(R)));threading.Thread(target=server.serve_forever,daemon=True).start();env['QA_URL']='http://127.0.0.1:8765/index.html?title=1'
 try:
  with log.open('w') as f:
   p=subprocess.run(['python3','-u',path],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=900)
  code=p.returncode
 except subprocess.TimeoutExpired:code=124
 finally:
  if server:server.shutdown();server.server_close()
 text=log.read_text();fail=re.findall(r'^FAIL .+$',text,re.M);counts=list(map(int,re.findall(r'^FAILS\s+(\d+)',text,re.M)));same=before==hashlib.sha256((R/path).read_bytes()).hexdigest();ok=code==0 and not fail and not any(counts) and same
 row={'test':path,'exit':code,'seconds':round(time.monotonic()-start,3),'pass':ok,'failure_lines':fail,'reported_fail_counts':counts,'source_test_sha256':before,'source_test_unchanged':same,'log':str(log)};rows.append(row);(O/'results.json').write_text(json.dumps({'runtime_source_head':head,'mode':'direct original tests from committed working tree; explicit title=1 tests do not use gameplay URL rewrite; SAVE owns loopback server','results':rows},indent=2));print(('PASS ' if ok else 'FAIL ')+path+' '+str(row['seconds']),flush=True)
raise SystemExit(0 if all(x['pass'] for x in rows) else 1)
