"""W128 (Claude): exact W116 durable restore, independent new guide G2 trial, private preservation.
Reuses the reviewed W117 gate/restore/pinned-worker/private Release protocol unchanged
(morwen_public_front_trial); only the candidate/quarantine member selection is W128-specific.
No protected data in public logs or artifacts. Not D4/G2-G4, not adopted.
"""
import io,json,os,re,sys,zipfile
from pathlib import Path
import morwen_public_recovery as r
import morwen_public_front_trial as ft

OBSERVER_BLOB='f927d3f5e510bb9c76607178a086cf26d4476a59'
NAME=re.compile(r'(W128-[A-Za-z0-9-]+|W125-save-poll-[0-9]{2}|W110-save-return)\.(png|json|txt)')
NAME_EXTRA=('W125-save-poll.jsonl','W125-observer-error.json','gui.log','reopen-status.txt','recovery-result.txt','resumed-editor.png','checkpoint-reopened.png')

def trial_members(root,env):
    ev=root/'evidence'
    immutable=(Path(env['RUNNER_TEMP'])/'Morwen-resume.vroid').read_bytes()
    r.require(r.sha(immutable)==r.NATIVE_SHA and (ev/'input-model.vroid').read_bytes()==immutable and r.extract((root/'source.zip').read_bytes())==immutable)
    cand=(ev/'W128-new-guide-not-adopted.vroid').read_bytes()
    rec=json.loads((ev/'W128-receipt.json').read_text())
    r.require(rec.get('status')=='NEW_INDEPENDENT_GUIDE_SAVED_REOPENED_NOT_ADOPTED' and rec.get('save_reopen') is True and rec.get('source_sha256')==r.NATIVE_SHA and rec.get('candidate_sha256')==r.sha(cand) and r.sha(cand)!=r.NATIVE_SHA and rec.get('groups')==['Freehand Group 1','Freehand Group 2'])
    r.require((ev/'model.vroid').read_bytes()==cand and (Path(env['HOME'])/'Documents/Morwen-c1.vroid').read_bytes()==cand)
    with zipfile.ZipFile(io.BytesIO(immutable)) as a,zipfile.ZipFile(io.BytesIO(cand)) as b:
        r.require(a.testzip() is None and b.testzip() is None and set(a.namelist())==set(b.namelist()) and a.read('v1model/data.bin')!=b.read('v1model/data.bin'))
        r.require(all(a.read(n)==b.read(n) for n in set(a.namelist())-{'v1model/data.bin','thumbnails/thumbnail.jpg'}))
    shots=rec.get('screenshots',{})
    r.require(isinstance(shots,dict) and 8<=len(shots)<=80 and {'W128-g2-brush.png','W128-reopened-front.png','W128-reopened-oblique.png','W128-reopened-g2.png'}<=set(shots))
    result={'candidate.vroid':cand,'native-receipt.json':(ev/'W128-receipt.json').read_bytes()}
    for p in sorted(ev.iterdir()):
        if p.is_symlink() or not p.is_file() or not (NAME.fullmatch(p.name) or p.name in NAME_EXTRA):continue
        data=p.read_bytes()
        if p.name in shots:r.require(r.sha(data)==shots[p.name])
        if 0<len(data)<=4*1024*1024 and sum(map(len,result.values()))+len(data)<=40*1024*1024:result[p.name]=data
    r.require(all(n in result for n in shots))
    result['receipt.json']=json.dumps(dict(status='ISOLATED_NATIVE_CANDIDATE_NOT_ADOPTED',trial='W128_NEW_INDEPENDENT_GUIDE',source_sha256=r.NATIVE_SHA,candidate_sha256=r.sha(cand),source_release_asset_id=ft.REL,public_run_id=env['GITHUB_RUN_ID'],worker_head=ft.WORKER_HEAD,lanes=rec.get('lanes'),design_gate='HOLD_PROVISIONAL_2D',independent_g2_g3_g4='NOT_RUN'),sort_keys=True).encode()
    result['SHA256SUMS.json']=json.dumps({k:r.sha(v) for k,v in result.items()},sort_keys=True).encode()
    return result

def quarantine_members(root,env):
    ev=root/'evidence'
    native=r.extract((root/'source.zip').read_bytes())
    r.require((Path(env['RUNNER_TEMP'])/'Morwen-resume.vroid').read_bytes()==native)
    result={}
    for p in sorted(ev.iterdir()):
        if p.is_symlink() or not p.is_file() or not (NAME.fullmatch(p.name) or p.name in NAME_EXTRA):continue
        if 0<p.stat().st_size<=2*1024*1024 and sum(map(len,result.values()))+p.stat().st_size<=28*1024*1024:result[p.name]=p.read_bytes()
    saved=ev/'W128-saved-unverified.vroid';receipt=ev/'W128-checkpoint-receipt.json'
    if saved.is_file() and receipt.is_file() and not saved.is_symlink() and 0<saved.stat().st_size<=16*1024*1024:
        data=saved.read_bytes();rec=json.loads(receipt.read_text())
        if rec.get('status')=='SAVED_REOPEN_PENDING' and rec.get('source_sha256')==r.NATIVE_SHA and rec.get('candidate_sha256')==r.sha(data) and r.sha(data)!=r.NATIVE_SHA:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                r.require(z.testzip() is None and set(z.namelist())=={'meta.json','v1model/meta.json','v1model/data.bin','thumbnails/thumbnail.jpg'})
            result['quarantined-native.vroid']=data
    r.require(bool(result))
    result['receipt.json']=json.dumps(dict(status='QUARANTINED_FAILED_TRIAL_NOT_ADOPTED',trial='W128_NEW_INDEPENDENT_GUIDE',source_sha256=r.NATIVE_SHA,public_run_id=env['GITHUB_RUN_ID'],native_reopen='NOT_VERIFIED',candidate_present='quarantined-native.vroid' in result),sort_keys=True).encode()
    result['SHA256SUMS.json']=json.dumps({k:r.sha(v) for k,v in result.items()},sort_keys=True).encode()
    return result

def main():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'private-preservation'))
    from release_transport import request
    env=os.environ.copy();root=Path(env['RUNNER_TEMP'])/'morwen-private-recovery'
    r.require(root.is_dir() and not root.is_symlink() and root.stat().st_mode&0o077==0)
    r.require(len(sys.argv)==2 and sys.argv[1] in ('prepare','fence','preserve','quarantine'))
    if sys.argv[1]=='fence':ft.gate(request,env);return
    if sys.argv[1]=='prepare':ft.prepare(request,env,root);return
    # Same reviewed packing, final exclusion and private Release protocol as W117/W120.
    ft.trial_members=trial_members;ft.quarantine_members=quarantine_members
    ft.preserve(request,env,root,quarantine=sys.argv[1]=='quarantine')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        code=getattr(exc,'status',0);suffix='_HTTP_'+str(code) if type(code) is int and 400<=code<=599 else ''
        print('W128_BLOCKED_AT_'+r.STAGE+suffix,flush=True)
        raise SystemExit(1) from None
