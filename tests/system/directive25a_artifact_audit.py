"""Audit-only consistency gate: product findings may FAIL; evidence must not hide them."""
import collections,hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=R/'docs/qa/evidence/directive-25a';fails=[]
def ck(ok,s):
 print(('ok   ' if ok else 'FAIL ')+s)
 if not ok:fails.append(s)
for f in ['docs/qa/DIRECTIVE-25A.md','docs/planning/PHASE6_BACKLOG.md','docs/planning/ASSET_GAP_LIST.md']:
 ck((R/f).is_file(),'deliverable '+f)
m=json.loads((E/'audit-matrix.json').read_text());v=json.loads((E/'static-inventory.json').read_text());a=m['items']
ck(len(a)==m['total'] and dict(collections.Counter(x['status'] for x in a))==m['counts'],'matrix counts derive from actual rows')
ck(len({x['id'] for x in a})==len(a) and all(x['status'] in ['COMPLETE','PARTIAL','MISSING','BUG','BLOCKED'] for x in a),'unique IDs and requested status vocabulary')
ck(all(all(x.get(k) for k in ['target','reproduction','expected','actual','status','evidence','android']) for x in a),'every target has steps / expectation / observation / evidence / device limit')
ck(all((E/p).is_file() for x in a for p in x['evidence']),'every evidence reference exists')
locks=v['protected_pngs'];ck(len(locks)==len({x['file'] for x in locks})==259 and all(x['actual']==x['expected']==hashlib.sha256((R/x['file']).read_bytes()).hexdigest() for x in locks),'259 immutable formal PNG hashes')
manifest=(E/'runtime-SHA256SUMS').read_bytes();ck(hashlib.sha256(manifest).hexdigest()==v['runtime_manifest_sha256'],'product manifest digest pinned')
ck(all(hashlib.sha256((R/f).read_bytes()).hexdigest()==h for h,f in (s.split(maxsplit=1) for s in manifest.decode().splitlines())),'all1456 runtime files unchanged')
changed=subprocess.check_output(['git','diff','--name-only',m['base'],'--','index.html','js','css','data','img','assets','dev'],cwd=R,text=True).strip();ck(not changed,'no product/story/save/registry/asset changes from baseline')
node=json.loads((E/'node/results.json').read_text());ck(len(node)==14 and sum(x['exit_code']==0 for x in node)==12 and sum(x['exit_code']!=0 for x in node)==2,'original Node12 PASS /2 FAIL preserved separately from diagnostics')
ck('FAIL no asset is claimed Android-verified' in (E/'asset-regression.log').read_text(),'original asset-test failure preserved')
browser=json.loads((E/'browser/results.json').read_text())['results'];extra=json.loads((E/'probe/results.json').read_text())['results'];allruns=browser+extra
ck(all('exit_code' in r for r in allruns),'no uncollected browser result claimed complete')
bytest={r['test']:r for r in allruns}
ck(all(x['status']!='COMPLETE' or not x.get('test') or (bytest[x['test']]['exit_code']==0 and not bytest[x['test']].get('failure_lines') and not any(bytest[x['test']].get('reported_fails',[]))) for x in a),'COMPLETE test rows require exit0 and no printed FAIL')
ck(all(x['status']=='BLOCKED' for x in a if x['id'] in ['U04','T07']),'physical Android / long-run hardware results not invented')
ck('ルーsmile/relieved' in (R/'docs/planning/ASSET_GAP_LIST.md').read_text() and '未採用' in (R/'docs/planning/ASSET_GAP_LIST.md').read_text(),'excluded Lou expressions remain unadopted')
summary=json.loads((E/'summary.json').read_text());ck(summary['counts']==m['counts'] and summary['audit_items']==m['total'] and summary['product_qa']=='FAIL' and summary['overall']=='PARTIAL','summary preserves partial product findings and baseline FAIL')
priorities=collections.Counter(s.split('|')[2].strip() for s in (R/'docs/planning/PHASE6_BACKLOG.md').read_text().splitlines() if s.startswith('| P6-'));ck(all(priorities.get(k,0)==v for k,v in summary['priorities'].items()),'backlog severity totals agree with real issue rows')
ck('20 PASS;' in (E/'node/startup-adapter-diagnostic.log').read_text() and '37 PASS;' in (E/'node/continue-adapter-diagnostic.log').read_text(),'diagnostic case counts are real collected output')
print('FAILS',len(fails));raise SystemExit(bool(fails))
