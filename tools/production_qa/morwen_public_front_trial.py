"""W117: exact W116 durable restore and scoped W110 native trial.
Only reviewed fixed source bytes; no protected data in public logs/artifacts.
The read-only recovery remains independently qualified; this trial is not D4/G2-G4.
"""
import base64,hashlib,io,json,os,re,sys,zipfile
from pathlib import Path
import morwen_public_recovery as r
REL=804317484
REL_SHA='07651177bdc4fe09d95efadc87691a6aa9c6d92c39ae26946c60100c23fd37ea'
REL_BYTES=14065998
OWNER_HEAD='df986c7e0549871940deb26f65f7a54f58658211'
WORKER_HEAD='cdb10057926fbe171358cb7e7a896065484ab0fd'
WORKER_BRANCH='candidate/morwen-private-blend-artifact-20261126'
PINS={
 'tools/author_vroid_W110.sh':'4e83be76cee5929c8b3fe0ebdaefef625cdbf4da',
 'tools/w112_material_survey.sh':'0e90418a1a51a608d97927661e3b1053341dce94',
 'tools/w107_brush.py':'f55d87a7138108df3cc830537b90ee5a8337cdee',
 'tools/w108_guide_fit.py':'675fc50e1e7ed5270100e00fe0a332b487ae7658',
 'tools/w109_visibility.py':'7aa46001f79349e1b1bfadf362c73ee7c867af3b',
 'tools/w110_camera_register.py':'1d0e41680f75b103745154aaf68a374064307cee',
 'tools/vroid_new_guide_guard_W31.py':'06c0252cd39087deb102071afe6d78b9dbc41516',
 'tools/vroid_hair_stroke_qualification_W31.swift':'b3cbdcee535b395ca4bb5d379ef197cc3ed9ab29',
 'tools/vroid_group_row_locator_W34.swift':'76893d5676f044585708de0cb90cdc3e8f24f5c4',
 'production/morwen/MORWEN_HAIR_BLANK_BLUEPRINT_W92_20261127.json':'3e71d075742a28397b5c02b0c66b22a940567274'
}
FIXTURE=('W108-F06-ready.png','W108-F06-ready.txt','W108-F06-ready-rows.json','W108-F05-ready.png','W108-F05-ready-rows.json','W108-face-registered.png','W108-face-registration.json')
def git_sha(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def gate(api,env):
    r.identity(env);r.private(api,env['DEST_TOKEN'])
    r.check_active(api,env['DEST_TOKEN'],env['GH_TOKEN'],env['GITHUB_RUN_ID'])
    owner=api(env['GH_TOKEN'],'GET','https://api.github.com/repos/'+r.ORIGIN+'/pulls/427')
    r.require(owner.get('state')=='open' and owner.get('head',{}).get('sha')==OWNER_HEAD)
    ref=api(env['DEST_TOKEN'],'GET',r.BASE+'/git/ref/heads/'+WORKER_BRANCH)
    r.require(ref.get('ref')=='refs/heads/'+WORKER_BRANCH and ref.get('object',{}).get('sha')==WORKER_HEAD)
def unpack_release(raw):
    r.require(len(raw)==REL_BYTES and r.sha(raw)==REL_SHA)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        r.verify_inventory(z)
        r.require(set(z.namelist())=={'W108-original.zip','reopened-editor.png','receipt.json','SHA256SUMS.json'})
        manifest=json.loads(z.read('SHA256SUMS.json'))
        r.require(set(manifest)==set(z.namelist())-{'SHA256SUMS.json'} and all(r.sha(z.read(n))==v for n,v in manifest.items()))
        rec=json.loads(z.read('receipt.json'))
        r.require(rec['status']=='READONLY_REOPEN_VERIFIED_NOT_ADOPTED' and rec['source_sha256']==r.NATIVE_SHA and rec['source_archive_sha256']==r.ARCHIVE_SHA and str(rec['public_run_id'])=='46139309085' and rec['source_artifact_id']==r.ARTIFACT and rec['screenshots_sha256']==r.sha(z.read('reopened-editor.png')))
        source=z.read('W108-original.zip')
    return source,r.extract(source)
def pinned_blob(api,token,path,pin):
    m=api(token,'GET',r.BASE+'/git/blobs/'+pin)
    r.require(m.get('sha')==pin and m.get('encoding')=='base64' and type(m.get('size')) is int and 0<m['size']<=65536)
    raw=base64.b64decode(''.join(m['content'].split()),validate=True)
    r.require(len(raw)==m['size'] and git_sha(raw)==pin)
    return raw
def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(raw)
def prepare(api,env,root):
    r.stage('FRONT_TRIAL_EXCLUSION');gate(api,env);token=env['DEST_TOKEN']
    url=r.BASE+'/releases/assets/'+str(REL)
    r.stage('FRONT_TRIAL_DURABLE_SOURCE')
    m=api(token,'GET',url)
    r.require(m.get('id')==REL and m.get('name')=='Morwen-native-recovery.zip' and m.get('size')==REL_BYTES and m.get('digest')=='sha256:'+REL_SHA and m.get('state')=='uploaded')
    source,native=unpack_release(api(token,'GET',url,binary=True,limit=REL_BYTES))
    put(root/'source.zip',source)
    put(Path(env['RUNNER_TEMP'])/'Morwen-resume.vroid',native)
    with zipfile.ZipFile(io.BytesIO(source)) as z:
        for name in FIXTURE:put(Path(env['RUNNER_TEMP'])/'W108-fixture'/name,z.read(name))
    r.stage('FRONT_TRIAL_PINNED_WORKER')
    for path,pin in PINS.items():put(root/path,pinned_blob(api,token,path,pin))
    r.stage('FRONT_TRIAL_SOURCE_READY')
def trial_members(root,env):
    ev=root/'evidence'
    immutable=(Path(env['RUNNER_TEMP'])/'Morwen-resume.vroid').read_bytes()
    r.require(r.sha(immutable)==r.NATIVE_SHA and (ev/'input-model.vroid').read_bytes()==immutable and r.extract((root/'source.zip').read_bytes())==immutable)
    # No final candidate without the real native save and reopen receipt.
    cand=(ev/'W110-new-front-not-adopted.vroid').read_bytes()
    rec=json.loads((ev/'W110-receipt.json').read_text())
    r.require(rec.get('status')=='NEW_CUSTOM_FRONT_STRANDS_SAVED_REOPENED_NOT_ADOPTED' and rec.get('save_reopen') is True and rec.get('source_sha256')==r.NATIVE_SHA and rec.get('candidate_sha256')==r.sha(cand) and r.sha(cand)!=r.NATIVE_SHA and rec.get('hairs')==['Hair '+str(i) for i in range(1,7)])
    r.require((ev/'model.vroid').read_bytes()==cand and (Path(env['HOME'])/'Documents/Morwen-c1.vroid').read_bytes()==cand)
    with zipfile.ZipFile(io.BytesIO(immutable)) as a,zipfile.ZipFile(io.BytesIO(cand)) as b:
        r.require(a.testzip() is None and b.testzip() is None and set(a.namelist())==set(b.namelist()) and a.read('v1model/data.bin')!=b.read('v1model/data.bin'))
        r.require(all(a.read(n)==b.read(n) for n in set(a.namelist())-{'v1model/data.bin','thumbnails/thumbnail.jpg'}))
    shots=rec.get('screenshots',{})
    r.require(isinstance(shots,dict) and len(shots)>=10 and len(shots)<=60 and {'W110-reopened-front.png','W110-reopened-oblique.png','W110-reopened-visible.png','W110-F06-after.png'}<=set(shots))
    result={'candidate.vroid':cand,'native-receipt.json':(ev/'W110-receipt.json').read_bytes()}
    for name,digest in shots.items():
        r.require(re.fullmatch(r'W110-[A-Za-z0-9-]+\.png',name) is not None)
        data=(ev/name).read_bytes()
        r.require(data.startswith(b'\x89PNG\r\n\x1a\n') and len(data)<8*1024*1024 and r.sha(data)==digest)
        result[name]=data
    for name in ('W110-camera-registration.json','W110-fit.json','W110-F06-stroke.json','W110-reopened-visible-eyes.json','W110-material-status.txt','W112-material-status.txt','W112-material-expanded.png','W112-material-before.png'):
        path=ev/name
        if path.is_file():result[name]=path.read_bytes()
    result['receipt.json']=json.dumps(dict(status='ISOLATED_NATIVE_CANDIDATE_NOT_ADOPTED',source_sha256=r.NATIVE_SHA,candidate_sha256=r.sha(cand),source_release_asset_id=REL,public_run_id=env['GITHUB_RUN_ID'],worker_head=WORKER_HEAD,design_gate='HOLD_PROVISIONAL_2D',independent_g2_g3_g4='NOT_RUN',material_edit='NOT_RUN'),sort_keys=True).encode()
    result['SHA256SUMS.json']=json.dumps({k:r.sha(v) for k,v in result.items()},sort_keys=True).encode()
    return result
def preserve(api,env,root):
    r.stage('FRONT_TRIAL_CANDIDATE_CHECK');members=trial_members(root,env)
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as z:
        for name,data in members.items():
            info=zipfile.ZipInfo(name);info.external_attr=0o100600<<16;z.writestr(info,data)
    raw=buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:r.verify_inventory(z);r.require(all(z.read(n)==v for n,v in members.items()))
    r.stage('FRONT_TRIAL_FINAL_EXCLUSION');gate(api,env)
    r.publish_private(api,env,raw,'front_trial')
def main():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'private-preservation'))
    from release_transport import request
    env=os.environ.copy();root=Path(env['RUNNER_TEMP'])/'morwen-private-recovery'
    r.require(root.is_dir() and not root.is_symlink() and root.stat().st_mode&0o077==0)
    r.require(len(sys.argv)==2 and sys.argv[1] in ('prepare','fence','preserve'))
    if sys.argv[1]=='fence':gate(request,env);return
    (prepare if sys.argv[1]=='prepare' else preserve)(request,env,root)
if __name__=='__main__':
    try:main()
    except Exception as exc:
        code=getattr(exc,'status',0);suffix='_HTTP_'+str(code) if type(code) is int and 400<=code<=599 else ''
        print('FRONT_TRIAL_BLOCKED_AT_'+r.STAGE+suffix,flush=True)
        raise SystemExit(1) from None
