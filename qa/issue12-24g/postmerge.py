"""Actual-main major regression. Full86 reused only under exact Git tree identity."""
import json,os,hashlib,sys,datetime,collections
from pathlib import Path
h=Path(__file__).resolve().parent
m=json.loads((h/'manifest.json').read_text())
md=hashlib.sha256((h/'manifest.json').read_bytes()).hexdigest()
out=Path('summary');out.mkdir(exist_ok=True)
errors=[];rows=[]
expected={x['name']:x['sha256'] for x in m['tests']+m.get('extra_core_tests',[])}
for p in Path('core-combined').glob('shard-*/results.json'):
 d=json.loads(p.read_text());rows+=d['results']
 if d.get('source_commit')!=m['source_commit'] or d.get('main_at_start')!=m['main_base_commit'] or d.get('main_at_finish')!=m['main_base_commit'] or d.get('manifest_sha256')!=md:errors.append('core source/main/manifest mismatch '+str(p))
names=[x['name'] for x in rows]
if len(rows)!=6 or len(set(names))!=6 or set(names)!=set(m['probe_tests']):errors.append('core six missing/duplicate/unexpected')
for r in rows:
 if r.get('status')!='PASS' or r.get('exit_code')!=0:errors.append('core nonPASS '+r['name'])
 if r.get('test_sha256')!=expected.get(r['name']) or r.get('test_sha256_after')!=expected.get(r['name']):errors.append('core test hash mismatch')
 if not r.get('browser_evidence',{}).get('browsers') or not r.get('browser_evidence',{}).get('navigations'):errors.append('missing real-browser evidence')
node=[]
try:
 node=json.loads(Path('node-combined/reports/qa-results.json').read_text())
 if len(node)!=37 or any(x['status']!='PASS' or x['exit']!=0 for x in node):errors.append('automatic regression nonPASS/missing')
 suites=[x for x in node if x['command'][0]=='node' and x['command'][1].endswith(('.test.cjs','.test.js'))]
 if len(suites)!=20:errors.append('Node suite count mismatch')
 if Path('node-combined/source.txt').read_text().strip()!=m['source_commit']:errors.append('node source mismatch')
 if Path('node-combined/tree.txt').read_text().strip()!=m['premerge_tree']:errors.append('merge tree differs from validated head')
except Exception as e:errors.append('missing automatic evidence: '+str(e))
if os.environ.get('CORE_NODE_STATUS')!='success':errors.append('automatic CI job not successful')
status='BLOCKED' if errors else 'PASS'
report={'directive':'24L_POSTMERGE','scope':'actual-main automatic37 and six real-browser core regressions; Full86 not rerun','status':status,'target_commit':m['source_commit'],'main_base_commit':m['main_base_commit'],'expected_tree':m['premerge_tree'],'reused_full86':m['premerge_full86'],'core_results':rows,'automatic_commands':len(node),'core_counts':dict(collections.Counter(r['status'] for r in rows)),'integrity_errors':errors,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(out/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'SUMMARY.md').write_text('# 24L post-merge major regression\n\n'+status+'\n\nFull86 reused under exact Git tree identity; see SUMMARY.json.\n')
print(json.dumps({k:v for k,v in report.items() if k!='core_results'},indent=2))
sys.exit(0 if status=='PASS' else 1)
