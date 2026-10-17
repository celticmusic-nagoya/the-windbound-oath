"""Serve exact baseline HTML/CSS without switching or modifying the candidate checkout."""
from pathlib import Path
import subprocess,os,json,time,threading,http.server,functools,urllib.parse,hashlib,re
r=Path('/workspace/battle-ui-integration-03');out=Path('/workspace/battle-ui-integration-03-evidence');base='fd5a8576a5e18dfc1e5ea903cdf7d210f3d2be13';overlay={}
for name in ['index.html','css/battle-polish.css']:overlay['/'+name]=subprocess.check_output(['git','-C',str(r),'show',base+':'+name])
# Audit all product paths before classifying this as baseline runtime.
changed=subprocess.check_output(['git','-C',str(r),'diff','--name-only',base,'--','index.html','css','js','img','data'],text=True).splitlines();assert set(changed)=={'css/battle-polish.css','index.html'},changed
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  path=urllib.parse.urlsplit(self.path).path
  if path in overlay:
   data=overlay[path];self.send_response(200);self.send_header('Content-Type','text/css'if path.endswith('.css')else'text/html');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  else:super().do_GET()
server=http.server.ThreadingHTTPServer(('127.0.0.1',8828),functools.partial(Handler,directory=str(r)));threading.Thread(target=server.serve_forever,daemon=True).start();rows=[];env=dict(os.environ,PW_CHROMIUM_EXECUTABLE='/usr/bin/chromium',PORT='8828')
try:
 lines=(out/'related/results.tsv').read_text().splitlines()[1:];failed=[x.split('\t')[0]for x in lines if x.split('\t')[1]!='0']
 for test in failed:
  name=Path(test).stem;start=time.monotonic();log=out/('baseline-'+name+'.log')
  with log.open('w')as f:p=subprocess.run(['python3','tests/run_python.py',test],cwd=r,env=env,stdout=f,stderr=subprocess.STDOUT)
  text=log.read_text();row={'test':test,'exit':p.returncode,'seconds':round(time.monotonic()-start,2),'failure_lines':[l for l in text.splitlines()if l.startswith('FAIL ')or re.match(r'^FAILS [1-9]',l)]};rows.append(row);print(json.dumps(row),flush=True)
finally:server.shutdown();server.server_close()
(out/'baseline-comparison.json').write_text(json.dumps({'baseline':base,'method':'Exact baseline HTML and battle-polish.css served via isolated HTTP overlay; every other product file is unchanged from baseline, no source switching/writing; same original test files and assertions','overlaid_sha256':{p:hashlib.sha256(v).hexdigest()for p,v in overlay.items()},'candidate_changed_product_paths':changed,'tests':rows},indent=2)+'\n')
