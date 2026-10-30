"""21A: pin the user-adopted PR91 bytes; current registry must resolve ONLY those approved files."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];fails=[]
def check(ok,label):
 print(('ok   ' if ok else 'FAIL ')+label,flush=True)
 if not ok:fails.append(label)
PR91='bdf6a6dd50a26183daa181342d1fa546f5873418'
LOCK='f6c497673372365f986b0a4456796d8f6abf98521d3299a1a2c992de8dfe9b02'
OTHER_LOCK='dacfe9152d1641bf6251699dd6013dad19f429e37fe0173ddb961c5f4bbcf5bd'
ledger=json.loads((ROOT/'docs/portraits/PHASE4_FORMAL_ADOPTION_21A.json').read_text())
manifest=(ROOT/'docs/portraits/PHASE4_ADOPTED_SHA256SUMS').read_bytes()
check(hashlib.sha256(manifest).hexdigest()==LOCK==ledger['manifest_sha256'],'immutable PR91-derived46-file lock digest (updating PNG+ledger cannot silently bless changed art)')
entries=[line.split(maxsplit=1) for line in manifest.decode().splitlines()];locked={file:digest for digest,file in entries}
check(len(entries)==len(locked)==46 and ledger['source_commit']==PR91 and ledger['status']=='APPROVED','46 unique formally adopted runtime paths, exact PR91 source commit')
check(all((ROOT/f).is_file() and hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in locked.items()),'all46 adopted PNG bytes match protected SHA')
check({a['file']:a['sha256'] for a in ledger['assets']}==locked and all(a['approval_status']=='APPROVED' and a['adoption_basis']=='ユーザーAndroid実機QA全4項目PASS — DIRECTIVE-21A (2026-10-30)' for a in ledger['assets']),'formal ledger exact set/SHA/user four-item Android QA basis')
counts=ledger['counts'];check(counts=={'expression_pngs_including_normal':22,'normal_already_formal':3,'newly_formal_expression_differences':19,'normal_blink_pngs':24,'newly_promoted_pngs':43,'total_adopted_pngs':46},'22 expressions +24blink,43 promoted and3 prior formal normals retained')
script="""const vm=require('node:vm'),fs=require('node:fs');let ctx={window:{}};vm.runInNewContext(fs.readFileSync('js/field/portrait-registry.js','utf8'),ctx);const r=ctx.window.PortraitRegistry,out=[];for(const c of ['fiona','lou','emma']){const b=r.blinkOf(c,'normal');out.push({id:c,faces:r.get(c).faces,files:[...r.get(c).faces.map(f=>r.imageUrl(c,f)),...Object.values(b.eyes).flatMap(e=>e.urls)],normalOnly:r.get(c).faces.every(f=>Boolean(r.blinkOf(c,f))===(f==='normal'))})}console.log(JSON.stringify(out));"""
actual=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT))
expected={'fiona':['normal','smile','angry','sad','surprised','worried','determined','relieved'],'lou':['normal','angry','sad','surprised','worried','determined'],'emma':['normal','smile','angry','sad','surprised','worried','determined','relieved']}
check({f for a in actual for f in a['files']}==set(locked) and all(a['faces']==expected[a['id']] and a['normalOnly'] for a in actual),'actual runtime URLs/faces match46 locked files, no Lou smile/relieved, blink normal only')
for c,revision in [('fiona','provisional-20e'),('lou','provisional-20e'),('emma','provisional-20c')]:
 check(all('/'+revision+'/' in a['file'] for a in ledger['assets'] if a['character']==c and not(a['kind']=='expression' and a['expression']=='normal')),c+': exactly the QA-passed live revision; no old handoff substitution')
reg=json.loads((ROOT/'docs/assets/ASSET_REGISTRY.json').read_text())['assets'];byfile={a['source_path']:a for a in reg if a['source_path'] in locked}
check(set(byfile)==set(locked) and all(a['approval_status']=='APPROVED' and a['qa_status']=='PASS' and a['android_status']=='PASS' and a['source_sha256']==locked[f] for f,a in byfile.items()),'central ledger and actual46 files agree: APPROVED, QA/Android PASS and exactSHA')
formal={a['source_path'] for a in reg if a['category']=='portrait' and a['character'] in expected and a['approval_status']=='APPROVED'}
check(formal==set(locked),'no other Fiona/Lou/Emma portrait material accidentally promoted')
byid={a['asset_id']:a for a in reg}
check(all(byid[a['asset_id']]['approval_status']==a['approval_status'] for a in ledger['nonadopted_portrait_statuses']),'every excluded/superseded portrait approval status preserved')
protected=ledger['other_protected_pngs'];other=''.join(a['sha256']+'  '+a['file']+'\n' for a in sorted(protected,key=lambda a:a['file']))
check(len(protected)==64 and hashlib.sha256(other.encode()).hexdigest()==OTHER_LOCK and all(hashlib.sha256((ROOT/a['file']).read_bytes()).hexdigest()==a['sha256'] for a in protected),'Aidan54 +eventCG10 bytes unchanged, independently pinned PR91 protection list')
print('FAILS',len(fails));raise SystemExit(1 if fails else 0)
