"""QA harness controls only, never product/browser PASS evidence."""
import copy,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from policy import NAME,LINE,REQUIRED,minor
h=Path(__file__).resolve().parent;m=json.loads((h/'manifest.json').read_text());digest=hashlib.sha256((h/'manifest.json').read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as d:
 root=Path(d);original=[]
 core=root/'core-combined'/'shard-0';core.mkdir(parents=True)
 expected={x['name']:x['sha256'] for x in m['tests']+m.get('extra_core_tests',[])}
 core_rows=[{'name':name,'status':'PASS','test_sha256':expected[name],'test_sha256_after':expected[name],'browser_evidence':{'browsers':[{'type':'chromium'}],'navigations':[{'url':'synthetic'}]}} for name in m['probe_tests']]
 (core/'results.json').write_text(json.dumps({'source_commit':m['source_commit'],'results':core_rows}))
 focus=root/'focus-combined'/'round-1'/'shard-0';focus.mkdir(parents=True)
 focus_rows=[{'name':name,'status':'PASS','test_sha256':expected[name],'test_sha256_after':expected[name],'browser_evidence':{'browsers':[{'type':'chromium'}],'navigations':[{'url':'synthetic'}]}} for name in m['focus_tests']]
 (focus/'results.json').write_text(json.dumps({'source_commit':m['source_commit'],'main_at_start':m['main_base_commit'],'main_at_finish':m['main_base_commit'],'results':focus_rows}))
 for round_id in (2,3):
  other=root/'focus-combined'/f'round-{round_id}'/'shard-0';other.mkdir(parents=True);(other/'results.json').write_text(json.dumps({'source_commit':m['source_commit'],'main_at_start':m['main_base_commit'],'main_at_finish':m['main_base_commit'],'results':focus_rows}))
 def bad_core(a):
  d=json.loads((core/'results.json').read_text());d['results'][0]['status']='FAIL';(core/'results.json').write_text(json.dumps(d))
 def bad_focus(a):
  d=json.loads((focus/'results.json').read_text());d['results'][0]['status']='FAIL';(focus/'results.json').write_text(json.dumps(d))
 def optional(a):
  row=next(x for d in a for x in d['results'] if x['name']==NAME)
  row.update(status='SKIP',exit_code=0,skip_lines=[LINE],failure_lines=[],reported_fails=[0],limitation_evidence={'all_current_checks_pass':True,'checked':list(REQUIRED),'errors':[]})
 def invalid_optional(a):
  optional(a);next(x for d in a for x in d['results'] if x['name']==NAME)['limitation_evidence']['all_current_checks_pass']=False
 for i in range(8):
  p=root/f'shard-{i}';p.mkdir();rows=[{'name':x['name'],'test_sha256':x['sha256'],'test_sha256_after':x['sha256'],'status':'PASS','exit_code':0,'browser_evidence':{'browsers':[{'type':'chromium','version':'synthetic control'}],'navigations':[{'url':'synthetic'}]}} for x in m['tests'][i::8]]
  original.append({'source_commit':m['source_commit'],'main_at_start':m['main_base_commit'],'main_at_finish':m['main_base_commit'],'manifest_sha256':digest,'started_at':'2026-01-01T00:00:00Z','results':rows})
 for name,mutate,want in [('complete',lambda a:None,'PASS'),('missing',lambda a:a[0]['results'].pop(),'BLOCKED'),('duplicate',lambda a:a[0]['results'].append(a[0]['results'][0]),'BLOCKED'),('fail',lambda a:a[0]['results'][0].update(status='FAIL'),'FAIL'),('skip',lambda a:a[0]['results'][0].update(status='SKIP'),'BLOCKED'),('timeout',lambda a:a[0]['results'][0].update(status='TIMEOUT'),'FAIL'),('missing_browser',lambda a:a[0]['results'][0].update(browser_evidence={}),'BLOCKED'),('wrong_sha',lambda a:a[0]['results'][0].update(test_sha256='bad'),'BLOCKED'),('main_moved',lambda a:a[0].update(main_at_finish='bad'),'BLOCKED'),('explicit_nonmajor_skip',optional,'CONDITIONAL_PASS'),('unproved_nonmajor_skip',invalid_optional,'BLOCKED'),('core_fail_blocks_full_pass',bad_core,'BLOCKED'),('focus_fail_blocks_full_pass',bad_focus,'BLOCKED')]:
  (core/'results.json').write_text(json.dumps({'source_commit':m['source_commit'],'results':core_rows}))
  (focus/'results.json').write_text(json.dumps({'source_commit':m['source_commit'],'main_at_start':m['main_base_commit'],'main_at_finish':m['main_base_commit'],'results':focus_rows}))
  a=copy.deepcopy(original);mutate(a)
  for i,x in enumerate(a):(root/f'shard-{i}'/'results.json').write_text(json.dumps(x))
  out=root/('out-'+name);p=subprocess.run([sys.executable,str(h/'aggregate.py'),str(root),str(out)],capture_output=True,text=True,cwd=root,env=dict(os.environ,CORE_NODE_STATUS='success'));result=json.loads((out/'SUMMARY.json').read_text());assert result['status']==want,(name,result['status']);assert (p.returncode==0)==(want in ('PASS','CONDITIONAL_PASS'));print('PASS harness control',name)
print('13 aggregate harness controls PASS; synthetic only, NOT browser QA')

# Scheduling classifier controls, using observed native RAF telemetry (not product PASS evidence).
from policy import idle_analysis,environment
observed=json.loads((h/'idle-policy-observation.json').read_text());assert idle_analysis(observed)
bad=copy.deepcopy(observed)
for record in bad['records']:record['samples']['gaps']=[16.6667]*400
assert idle_analysis(bad) is None
bad=copy.deepcopy(observed);bad['failure_names'].append('missing frames');assert idle_analysis(bad) is None
row={'name':'tests/battle/battle_idle6.py','status':'FAIL','exit_code':1,'skip_lines':[],'browser_evidence':{'browsers':[{'type':'synthetic classifier control'}],'navigations':[{'url':'synthetic'}]},'native_idle_timing':observed,'failure_lines':['FAIL '+n+' measured intervals' for n in observed['failure_names']]}
assert environment(row)
row['failure_lines'].append('FAIL visibility');assert not environment(row)
print('5 idle scheduling classifier controls PASS; NOT product/browser acceptance evidence')
