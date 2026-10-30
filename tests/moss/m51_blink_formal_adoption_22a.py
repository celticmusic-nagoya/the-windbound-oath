"""22A: pin user-adopted PR93 expression-blink bytes without changing prior formal records."""
import json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];fails=[]
def check(ok,name):
 print(('ok   ' if ok else 'FAIL ')+name,flush=True)
 if not ok:fails.append(name)
LOCK='c4297d808ac988cc3ce013aa50da9f87ed291a69f934dc5a810c3bf29bd172bf';SOURCE='72c83eef1e3fef1c474a51f84e98f1bb3b3fbe45'
L=json.loads((ROOT/'docs/portraits/PHASE4_EXPRESSION_BLINK_FORMAL_22A.json').read_text());M=(ROOT/L['manifest']).read_bytes();rows=[s.split(maxsplit=1) for s in M.decode().splitlines()];locked={f:h for h,f in rows}
check(hashlib.sha256(M).hexdigest()==LOCK==L['manifest_sha256'] and L['source_commit']==SOURCE,'immutable120-file PR93-source lock digest; no silent PNG+JSON rebaselining')
check(L['status']=='APPROVED' and L['face_count']==15 and len(rows)==len(locked)==L['asset_count']==120,'user explicitly formally adopted15faces/120unique PNG')
check({a['file']:a['sha256'] for a in L['assets']}==locked and all(a['adoption_status']=='APPROVED' and a['formal_adoption_directive']=='DIRECTIVE-22A' for a in L['assets']),'formal ledger exact paths/SHA/approval basis')
check(all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in locked.items()),'all120 formal PNG bytes match immutable PR93 values')
js="""const fs=require('node:fs'),vm=require('node:vm'),ctx={window:{}};vm.runInNewContext(fs.readFileSync('js/field/portrait-registry.js','utf8'),ctx);let r=ctx.window.PortraitRegistry,out=[];for(const c of ['fiona','lou','emma'])for(const f of ['angry','sad','surprised','worried','determined'])for(const e of Object.values(r.blinkOf(c,f).eyes))out.push(...e.urls);console.log(JSON.stringify(out));"""
actual=json.loads(subprocess.check_output(['node','-e',js],cwd=ROOT));check(len(actual)==120 and set(actual)==set(locked),'actual15expression blink URLs exactly match adopted120paths')
reg=json.loads((ROOT/'docs/assets/ASSET_REGISTRY.json').read_text())['assets'];records={a['source_path']:a for a in reg if a['source_path'] in locked}
check(set(records)==set(locked) and all(a['approval_status']=='APPROVED' and a['qa_status']=='PASS' and a['android_status']=='PASS' and a['source_sha256']==locked[f] for f,a in records.items()),'central registry120formal/QA/Android PASS and SHA exact')
prior=json.loads((ROOT/'docs/portraits/PHASE4_FORMAL_ADOPTION_21A.json').read_text());check(hashlib.sha256((ROOT/'docs/portraits/PHASE4_ADOPTED_SHA256SUMS').read_bytes()).hexdigest()==prior['manifest_sha256']==L['prior_formal_manifest_sha256'],'prior21A46-file lock unchanged')
check(all(hashlib.sha256((ROOT/a['file']).read_bytes()).hexdigest()==a['sha256'] for a in prior['assets']+prior['other_protected_pngs']),'all prior110 formally adopted PNGs unchanged inclAidan54/CG10')
old=json.loads((ROOT/'docs/portraits/PHASE4_EXPRESSION_BLINK_21C.json').read_text());check(all(a['adoption_status']=='PROVISIONAL_ANDROID_QA' for a in old['assets']),'21C provisional source snapshot kept intact as adoption history')
check(not any('smile' in f or 'relieved' in f for f in locked),'no static4 or unadoptedLou smile/relieved mixed into blink adoption')
print('FAILS',len(fails));raise SystemExit(1 if fails else 0)
