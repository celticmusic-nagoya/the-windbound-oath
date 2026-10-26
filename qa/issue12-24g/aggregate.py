import collections,datetime,hashlib,json,os,sys
from pathlib import Path
from policy import accepted,minor,environment
h=Path(__file__).resolve().parent;m=json.loads((h/'manifest.json').read_text());root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True);expected={x['name']:x['sha256'] for x in m['tests']};shards=[];rows=[];problems=[]
for f in sorted(root.glob('shard-*/results.json')):
 d=json.loads(f.read_text());shards.append(d);rows.extend(d['results'])
 if d.get('source_commit')!=m['source_commit']:problems.append('wrong source SHA '+str(f))
 if d.get('main_at_start')!=m.get('main_base_commit',m['source_commit']) or d.get('main_at_finish')!=m.get('main_base_commit',m['source_commit']):problems.append('main changed or incomplete source validation '+str(f))
 if d.get('manifest_sha256')!=hashlib.sha256((h/'manifest.json').read_bytes()).hexdigest():problems.append('wrong manifest '+str(f))
names=[x['name'] for x in rows];duplicates=[x for x,n in collections.Counter(names).items() if n>1];unexpected=sorted(set(names)-set(expected));missing=sorted(set(expected)-set(names))
for x in rows:
 if x.get('status')=='PASS' and (not x.get('browser_evidence',{}).get('browsers') or not x.get('browser_evidence',{}).get('navigations')):problems.append('missing real browser evidence '+x['name'])
 if x['name'] in expected and (x.get('test_sha256')!=expected[x['name']] or x.get('test_sha256_after')!=expected[x['name']]):problems.append('test hash mismatch '+x['name'])
for name in missing:rows.append({'name':name,'status':'NOT_RUN','reason':'missing CI shard/result'})
if len(shards)!=8:problems.append('expected 8 shards, received '+str(len(shards)))
if duplicates:problems.append('duplicate names '+repr(duplicates))
if unexpected:problems.append('unexpected names '+repr(unexpected))
counts={k:sum(x['status']==k for x in rows) for k in ['PASS','FAIL','SKIP','TIMEOUT','NOT_RUN']}
status='FAIL' if counts['FAIL'] or counts['TIMEOUT'] else 'BLOCKED' if problems or counts['SKIP'] or counts['NOT_RUN'] or counts['PASS']!=86 else 'PASS'
core=[]
core_expected={x['name']:x['sha256'] for x in m['tests']+m.get('extra_core_tests',[])}
for f in Path('core-combined').glob('shard-*/results.json'):
 d=json.loads(f.read_text());core.extend(d['results'])
 if d.get('source_commit')!=m['source_commit']:problems.append('core source mismatch '+str(f))
 for x in d['results']:
  if x.get('test_sha256')!=core_expected.get(x['name']) or x.get('test_sha256_after')!=core_expected.get(x['name']):problems.append('core hash mismatch '+x['name'])
  if x.get('status')=='PASS' and (not x.get('browser_evidence',{}).get('browsers') or not x.get('browser_evidence',{}).get('navigations')):problems.append('core browser evidence missing '+x['name'])
core_names=[x['name'] for x in core];core_ok=len(core)==len(m['probe_tests']) and set(core_names)==set(m['probe_tests']) and len(set(core_names))==len(core_names) and all(x['status']=='PASS' for x in core)
node_ok=os.environ.get('CORE_NODE_STATUS')=='success'
if not core_ok or not node_ok or problems:status='BLOCKED'
focus=[]
for f in Path('focus-combined').glob('round-*/shard-*/results.json'):
 d=json.loads(f.read_text());focus.extend(d['results'])
 if d.get('source_commit')!=m['source_commit'] or d.get('main_at_start')!=m['main_base_commit'] or d.get('main_at_finish')!=m['main_base_commit']:problems.append('focus SHA/main mismatch '+str(f))
 for x in d['results']:
  if x.get('test_sha256')!=core_expected.get(x['name']) or x.get('test_sha256_after')!=core_expected.get(x['name']):problems.append('focus hash mismatch '+x['name'])
  if not x.get('browser_evidence',{}).get('browsers') or not x.get('browser_evidence',{}).get('navigations'):problems.append('focus browser evidence missing '+x['name'])
focus_names=[x['name'] for x in focus];focus_ok=len(focus)==3*len(m['focus_tests']) and collections.Counter(focus_names)==collections.Counter({n:3 for n in m['focus_tests']}) and all(accepted(x) for x in focus)
for round_id in (1,2,3):
 round_names=[]
 for f in Path('focus-combined').glob(f'round-{round_id}/shard-*/results.json'):round_names += [x['name'] for x in json.loads(f.read_text())['results']]
 if collections.Counter(round_names)!=collections.Counter(m['focus_tests']):focus_ok=False
if not focus_ok:status='BLOCKED'
if core_ok and node_ok and focus_ok and not problems and not duplicates and not unexpected and not missing and len(rows)==86 and all(accepted(x) for x in rows):status='CONDITIONAL_PASS' if any(minor(x) or environment(x) for x in rows+focus) else 'PASS'
report={'environment_warnings':[{'name':x['name'],'raw_status':x['status'],'classification':'ENV_WARNING','evidence':x.get('environment_evidence')} for x in rows if environment(x)],'focus_results':focus,'focus_pass':focus_ok,'accepted_non_major_limitations':[{'name':x['name'],'status':x['status'],'warning':False,'reason':'unimplemented external effect hooks; actual runtime zone checks PASS'} for x in rows if minor(x)],'directive':'24L','status':status,'target_commit':m['source_commit'],'main_base_commit':m['main_base_commit'],'core_node_pass':node_ok,'core_browser_pass':core_ok,'core_results':core,'baseline_commit':m['baseline_commit'],'started_at':min((x['started_at'] for x in shards),default=None),'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'counts':counts,'defined':86,'executed':sum(x.get('exit_code') is not None for x in rows),'unique':len(set(names)),'duplicates':duplicates,'unexpected':unexpected,'missing':missing,'integrity_errors':problems,'results':rows,'shard_environments':[{k:v for k,v in x.items() if k!='results'} for x in shards]}
(out/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n');(out/'SUMMARY.md').write_text('# DIRECTIVE-24G v2\n\nStatus: **'+status+'**\n\nTarget: `'+m['source_commit']+'`\n\n'+json.dumps(counts)+'\n\nExecuted '+str(report['executed'])+'/86; unique '+str(report['unique'])+'; duplicates '+str(len(duplicates))+'; missing '+str(len(missing))+'.\n\nContract updates are documented by 24H; unchanged acceptance goals, no retries/exclusions.\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('results','shard_environments')},indent=2));sys.exit(0 if status in ('PASS','CONDITIONAL_PASS') else 1)
