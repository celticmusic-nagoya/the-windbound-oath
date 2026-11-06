"""Fail-fast original UP07 suite with PR156 metrics and pre-assert evidence only."""
import argparse,ast,datetime,functools,gzip,hashlib,http.server,json,os,re,signal,subprocess,sys,threading,time,traceback
from pathlib import Path
from reqa_checkpoint import instrument,Recorder,atomic,now
R=Path(__file__).resolve().parents[2];FIXED='0494f6452548ea476b4cebbc69d9f41d878d540d';QA='442ab3b75141376fd83e37541504d896ba02638e'
BROWSER=['tests/moss/m67_up_production.py','tests/moss/m62_aidan_down_production.py','tests/moss/m58_aidan_side_stride.py','tests/moss/m55_dev_walk_motion.py','tests/system/save_continue_lifecycle.py','tests/system/asset_registry_audit.py','tests/moss/m49_phase4_formal_adoption.py']
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def source(ref,path):return git('show',ref+':'+path)
def protection():
 diff=git('diff','--name-only',FIXED,'HEAD','--','js','img','assets','data','css','index.html','docs/assets').decode().splitlines();history=git('diff','--name-only',QA,'HEAD','--','docs/qa/evidence/player-walk-up-07','docs/qa/evidence/player-walk-up-07-diag').decode().splitlines();changes=[];count=0
 for row in git('ls-tree','-rz',FIXED).split(b'\0'):
  if not row:continue
  info,name=row.split(b'\t',1);path=os.fsdecode(name);blob=info.decode().split()[2]
  if not(path.lower().endswith('.png') or path.startswith('docs/qa/evidence/player-walk-up-07/')):continue
  data=(R/path).read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();count+=1
  if actual!=blob:changes.append(path)
 locks={}
 for name in ['PHASE4_FORMAL_ADOPTION_21A.json','PHASE4_EXPRESSION_BLINK_FORMAL_22A.json','PHASE4_FIONA_22BR4.json']:
  for a in json.loads((R/'docs/portraits'/name).read_text())['assets']:locks[a['file']]=a['sha256']
 prefix=Path('assets/images/characters/portraits/aidan')
 for line in (R/prefix/'SHA256SUMS').read_text().splitlines():
  h,p=line.split(maxsplit=1);locks[str(prefix/p.lstrip('*'))]=h
 for scene in json.loads((R/'img/events/adopted-cg.json').read_text())['scenes'].values():
  for a in scene.values():locks['img/events/'+a['file']]=a['sha256']
 bad=[p for p,h in locks.items() if sha(R/p)!=h];qa_inputs=['tests/moss/m67_up_production.py','tests/helpers/up07_metrics.py','tests/helpers/up07_probe.py'];qa_bad=[p for p in qa_inputs if (R/p).read_bytes()!=source(QA,p)]
 return {'fixed_implementation':FIXED,'fixed_measurement':QA,'production_diff':diff,'history_diff':history,'fixed_png_and_old_evidence_count':count,'fixed_files_changed':changes,'formal_sha_count':len(locks),'formal_sha_failures':bad,'measurement_inputs_changed':qa_bad,'pass':not(diff or history or changes or bad or qa_bad) and len(locks)==259}
def child(path,out):
 out=Path(out);rec=None
 try:
  text=(R/path).read_text();code,calls=instrument(text,str(R/path));rec=Recorder(out,calls,path);atomic(out/'source-proof.json',{'file':path,'source_sha256':sha(R/path),'original_body_and_predicates_preserved':True,'in_memory_QA_logging_only':True});ns={'__name__':'__main__','__file__':str(R/path),'__reqa_checkpoint':rec,'__reqa_unhandled':rec.unhandled};sys.argv=[str(R/path)];exec(code,ns)
 except BaseException:
  atomic(out/'exception.json',{'utc':now(),'traceback':traceback.format_exc(),'recorded_failure':bool(rec and rec.failures)});raise
 finally:
  if rec:atomic(out/'checkpoint-summary.json',{'assertions_seen':rec.index,'failure_count':len(rec.failures),'first_failure':rec.failures[0] if rec.failures else None})
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def run(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);before=protection();atomic(out/'protection-before.json',before)
 if not before['pass']:raise RuntimeError('Protection preflight FAIL')
 node=sorted(str(p.relative_to(R)) for p in (R/'tests').glob('*.test.cjs'));assert len(node)==17
 plan=[{'path':p,'kind':'Node','status':'NOT_RUN'} for p in node]+[{'path':p,'kind':'browser/static','status':'NOT_RUN'} for p in BROWSER];head=git('rev-parse','HEAD').decode().strip();summary={'implementation':FIXED,'measurement':QA,'qa_head':head,'tests':plan,'stop_on_first_failure':True,'initial_failure_deleted':False,'source_mode':'Original scripts from committed worktree; AST logging shim only, no asset-copy snapshot. SAVE uses owned loopback server.'};atomic(out/'results.json',summary)
 known_report=R/'docs/assets/reports/audit_report.md';report_bytes=known_report.read_bytes()
 for i,row in enumerate(plan):
  path=row['path'];folder=out/f'{i+1:02}-{Path(path).stem}';folder.mkdir();source_before=sha(R/path);start=time.monotonic();start_ns=time.monotonic_ns();start_utc=now();env=dict(os.environ,QA_OUT=str(folder/'artifacts'),QA_GAMEPLAY_BOOT='1',PW_CHROMIUM_EXECUTABLE='/usr/bin/chromium',PLAYWRIGHT_BROWSERS_PATH='/workspace/work/dev-walk-cycle-a01/playwright');server=None
  if path.endswith('save_continue_lifecycle.py'):
   server=http.server.ThreadingHTTPServer(('127.0.0.1',8765),functools.partial(Quiet,directory=str(R)));threading.Thread(target=server.serve_forever,daemon=True).start();env['QA_URL']='http://127.0.0.1:8765/index.html?title=1'
  cmd=['node',path] if row['kind']=='Node' else [sys.executable,'-u',str(Path(__file__).resolve()),'--child',path,'--out',str(folder/'assertions')];print('RUN '+path,flush=True);code=None
  try:
   with (folder/'stdout.log').open('w') as log:
    proc=subprocess.Popen(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try:code=proc.wait(timeout=900)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=20);code=124
  finally:
   if server:server.shutdown();server.server_close()
  text=(folder/'stdout.log').read_text();fails=re.findall(r'^(?:FAIL\s|not ok\b).+$',text,re.M);failcounts=list(map(int,re.findall(r'^(?:FAILS\s+|[#ℹ] fail\s+)(\d+)',text,re.M)));skips=list(map(int,re.findall(r'^[#ℹ] skipped\s+(\d+)',text,re.M)));same=source_before==sha(R/path);ok=code==0 and not fails and not any(failcounts) and not any(skips) and same
  generated=None
  if known_report.read_bytes()!=report_bytes:
   generated={'path':str(known_report.relative_to(R)),'generated_sha256':sha(known_report),'restored_sha256':hashlib.sha256(report_bytes).hexdigest()};(folder/'generated-audit-report.md').write_bytes(known_report.read_bytes());tmp=known_report.with_name(known_report.name+'.reqa-restore');tmp.write_bytes(report_bytes);os.replace(tmp,known_report);generated['readback_match']=known_report.read_bytes()==report_bytes;ok=ok and generated['readback_match']
  changes=git('diff','--name-only').decode().splitlines();ok=ok and not changes
  row.update(status='PASS' if ok else 'FAIL',start_utc=start_utc,end_utc=now(),elapsed_seconds=time.monotonic()-start,start_monotonic_ns=start_ns,end_monotonic_ns=time.monotonic_ns(),exit_code=code,expected={'exit':0,'FAIL_lines':0,'nonzero_FAILS':0,'skipped':0,'source_unchanged':True},actual={'FAIL_lines':fails,'FAILS':failcounts,'skipped':skips,'source_unchanged':same},source_sha256=source_before,coordinates_and_RAF={'status':'See pre-assert traces for sampled movements' if row['kind']!='Node' else 'N/A','reason':'Unit/static/UI predicates do not define a sampled movement interval; never invent zero coordinates or RAF.'},checkpoint_evidence=str((folder/'assertions').relative_to(out)) if row['kind']!='Node' else None,log=str((folder/'stdout.log').relative_to(out)),generated_report=generated,unexpected_tracked_changes=changes,reason='All original checks satisfied' if ok else 'Original check/exit/skip/source-integrity gate failed; remaining tests NOT_RUN')
  atomic(folder/'execution.json',row);atomic(out/'results.json',summary);print(row['status']+' '+path+' '+str(round(row['elapsed_seconds'],3)),flush=True)
  if not ok:summary['status']='BLOCKED';summary['first_failed_test']=path;break
 else:summary['status']='PASS'
 summary['protection_after']=protection();summary['all_required_pass']=all(t['status']=='PASS' for t in plan) and summary['protection_after']['pass'];summary['main_merge_permitted']=False;summary['pages_publish_permitted']=False;atomic(out/'results.json',summary)
 raise SystemExit(0 if summary['all_required_pass'] else 1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--child');args=p.parse_args()
 if args.child:child(args.child,args.out)
 else:run(args.out)
