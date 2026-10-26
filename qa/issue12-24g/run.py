"""Frozen 86-suite browser execution, no retries, unchanged assertions."""
import argparse,collections,datetime,hashlib,json,os,platform,re,shutil,signal,socket,subprocess,sys,tempfile,time,traceback,urllib.request
from pathlib import Path
from policy import accepted,environment,idle_analysis,IDLE,NAME as MINOR_NAME,REQUIRED as MINOR_REQUIRED
HERE=Path(__file__).resolve().parent
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stop(p):
 if p and p.poll() is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def cmd(*args,cwd):return subprocess.check_output(args,cwd=cwd,text=True).strip()
def server(root,port,log):
 with socket.socket() as s:
  s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port))
 p=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=root,stdout=log,stderr=log,start_new_session=True)
 for _ in range(100):
  if p.poll() is not None:raise RuntimeError('server died')
  try:urllib.request.urlopen(f'http://127.0.0.1:{port}/index.html',timeout=.5).close();return p
  except OSError:time.sleep(.1)
 stop(p);raise RuntimeError('server readiness timeout')
def main():
 a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--baseline',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--shard',type=int,required=True);a.add_argument('--probe',action='store_true');a.add_argument('--focus',action='store_true');args=a.parse_args();source=args.source.resolve();out=args.out.resolve()/f'shard-{args.shard}';out.mkdir(parents=True,exist_ok=True)
 m=json.loads((HERE/'manifest.json').read_text());inv=json.loads((HERE/'full-inventory.json').read_text());expected=[x['test'] for x in inv if x['status'].startswith('NOT_RUN')];names=[x['name'] for x in m['tests']]
 assert m['count']==len(names)==len(set(names))==86 and names==expected
 assert sha(HERE/'full-inventory.json')==m['inventory_sha256']
 assert cmd('git','rev-parse','HEAD',cwd=source)==m['source_commit'];assert cmd('git','rev-parse','HEAD',cwd=args.baseline)==m['baseline_commit']
 assert subprocess.run(['git','diff','--quiet','HEAD'],cwd=source).returncode==0
 for t in m['tests']+m.get('extra_core_tests',[]):assert (source/t['name']).is_file() and sha(source/t['name'])==t['sha256']
 all_tests={x['name']:x for x in m['tests']+m.get('extra_core_tests',[])}
 selected=[all_tests[n] for n in m['focus_tests' if args.focus else 'probe_tests']] if args.focus or args.probe else m['tests'];shard_count=m['focus_shards'] if args.focus else m['probe_shards'] if args.probe else m['shards']
 main_start=cmd('git','ls-remote','origin','refs/heads/main',cwd=source).split()[0]
 meta={'source_commit':m['source_commit'],'baseline_commit':m['baseline_commit'],'main_at_start':main_start,'started_at':utc(),'logical_cpus':os.cpu_count(),'runner_os':platform.platform(),'python':sys.version,'run_id':os.environ['GITHUB_RUN_ID'],'run_attempt':os.environ['GITHUB_RUN_ATTEMPT'],'shard':args.shard,'manifest_sha256':sha(HERE/'manifest.json'),'mode':'focus' if args.focus else 'core' if args.probe else 'full','main_base_commit':m['main_base_commit'],'expected_names':[x['name'] for x in selected[args.shard::shard_count]],'results':[]}
 def report():
  meta['counts']=dict(collections.Counter(x['status'] for x in meta['results']));(out/'results.json').write_text(json.dumps(meta,indent=2)+'\n')
 report();Path('/tmp/claude-0').mkdir(exist_ok=True)
 for t in selected[args.shard::shard_count]:
  name=t['name'];label=name.replace('/','_');art=out/'artifacts'/label;art.mkdir(parents=True);logpath=out/(label+'.log');serverlog=out/(label+'.server.log');baseline_log=out/(label+'.baseline.log');proof=out/(label+'.browser.json');start=utc();tick=time.monotonic();row={'name':name,'started_at':start,'status':'NOT_RUN','test_sha256':t['sha256'],'exit_code':None};p=None;web=None;baseweb=None
  with tempfile.TemporaryDirectory(prefix='full86-') as temp,logpath.open('w') as log,serverlog.open('w') as slog,baseline_log.open('w') as blog:
   root=Path(temp)/'game';shutil.copytree(source,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   if name=='tests/moss/m33_boy_swordsman.py':
    # Preserve real historical objects for the exact, unchanged Git-based asset assertions.
    subprocess.run(['git','init','-q',str(root)],check=True)
    (root/'.git/objects/info/alternates').write_text(str(source/'.git/objects')+'\n')
    cmd('git','update-ref','refs/heads/qa',m['source_commit'],cwd=root);cmd('git','symbolic-ref','HEAD','refs/heads/qa',cwd=root);cmd('git','read-tree','HEAD',cwd=root)
    row['isolated_git_history']=True
   extra=['moss_forest_02_mossy_ravine.json'] if name=='tests/moss/walk_map.py' else ['--out',str(art)] if name=='tests/moss/m19_plan_bench.py' else []
   env=dict(os.environ,QA_GAMEPLAY_BOOT='1',PORT='8765',QA_URL='http://127.0.0.1:8765/index.html',BASELINE_URL='http://127.0.0.1:8766/index.html',QA_OUT=str(art),OUT=str(art/'perf.json') if name=='tests/moss/m19_perf.py' else str(art),BROWSER_EVIDENCE=str(proof))
   try:
    web=server(root,8765,slog)
    if name=='tests/issue54_mobile_baseline.py':baseweb=server(args.baseline,8766,blog)
    p=subprocess.Popen([sys.executable,'-u',str(HERE/'browser_child.py'),str(root),name,'8765',json.dumps(extra)],cwd=root,env=env,stdout=log,stderr=log,start_new_session=True)
    try:row['exit_code']=p.wait(timeout=m['timeout_seconds'])
    except subprocess.TimeoutExpired:stop(p);row['exit_code']=124;log.write('\nTIMEOUT: 900 seconds\n')
   except Exception as e:row['environment_error']=repr(e);log.write(traceback.format_exc())
   finally:stop(p);stop(web);stop(baseweb)
   row['test_sha256_after']=sha(root/name)
  text=logpath.read_text(errors='replace');proofdata=json.loads(proof.read_text()) if proof.exists() else {};row['browser_evidence']=proofdata;row['failure_lines']=re.findall(r'^FAIL .*$',text,re.M);row['reported_fails']=[int(x) for x in re.findall(r'^FAILS\s+(\d+)(?=\s|$)',text,re.M)];row['skip_lines']=re.findall(r'^(?:SKIP(?:PED)?\b|NOT_RUN\b|XFAIL\b|XPASS\b).*$',text,re.M)
  if row.get('environment_error'):row['status']='NOT_RUN'
  elif row['exit_code']==124 or (row['exit_code']!=0 and ('TimeoutError' in text or re.search(r'Timeout \d+ms exceeded',text))):row['status']='TIMEOUT'
  elif row['exit_code']!=0 or row['failure_lines'] or any(row['reported_fails']):row['status']='FAIL'
  elif row['skip_lines']:row['status']='SKIP'
  elif not proofdata.get('browsers') or not proofdata.get('navigations'):row['status']='NOT_RUN';row['environment_error']='No actual browser/navigation evidence'
  elif row['test_sha256_after']!=t['sha256']:row['status']='FAIL';row['failure_lines'].append('FAIL test source changed')
  else:row['status']='PASS'
  if name==IDLE and row['status']=='FAIL' and (art/'idle-timing.json').exists():
   row['native_idle_timing']=json.loads((art/'idle-timing.json').read_text())
   if environment(row):row['classification']='ENV_WARNING';row['environment_evidence']=idle_analysis(row['native_idle_timing'])
  if name==MINOR_NAME and row['status']=='SKIP':
   data=json.loads((art/'m24.json').read_text());checks=data.get('checks',[])
   row['limitation_evidence']={'all_current_checks_pass':bool(checks) and all(c.get('pass') is True for c in checks),'checked':[c['check'] for c in checks if c.get('pass') is True],'errors':data.get('errors'),'scope':'No shipped external rest/ambience effect hooks. Runtime level-specific zone contract is tested. Raw SKIP retained.'}
  row.update(ended_at=utc(),seconds=round(time.monotonic()-tick,3),log=logpath.name);meta['results'].append(row);report();print(f"{args.shard} {name}: {row['status']}",flush=True)
 meta['ended_at']=utc();meta['main_at_finish']=cmd('git','ls-remote','origin','refs/heads/main',cwd=source).split()[0];report()
 return 0 if all(x['status']=='PASS' for x in meta['results']) or (not args.probe and all(accepted(x) for x in meta['results'])) else 1
if __name__=='__main__':sys.exit(main())
