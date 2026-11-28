"""One scoped public-runner recovery; reuse private Release transport.
Never print private bytes, exception text, URLs or credentials.
No model mutation, no public artifacts; exact W108 checkpoint only.
"""
import hashlib,io,json,os,re,stat,subprocess,sys,zipfile
from pathlib import Path
DEST='celticmusic-nagoya/the-windbound-oath-handoff'
BASE='https://api.github.com/repos/'+DEST
ORIGIN='celticmusic-nagoya/the-windbound-oath'
ARTIFACT=15243366155
RUN=46094016312
SOURCE_HEAD='bd0c6d252bc6d413ff5af8f795fa78ec34426000'
ARCHIVE_SHA='7a7c0ec7778dc642ffe1409b5e625f34facc4e66e909104ae328a65ba35272b2'
ARCHIVE_BYTES=13804535
NATIVE_SHA='9803ab697c5c902ce74785a3a38c6e6a75c7a4a232828dfb62a5769ce236de9a'
NATIVE_NAME='W108-new-front-not-adopted.vroid'
CAP=64*1024*1024
STAGE='IDENTITY'
def require(v):
    if not v:raise ValueError('recovery blocked')
def sha(b):return hashlib.sha256(b).hexdigest()
def stage(s):
    global STAGE
    STAGE=s
    print('RECOVERY_'+s,flush=True)
def identity(env):
    require(env.get('GITHUB_REPOSITORY')==ORIGIN and env.get('GITHUB_REF')=='refs/heads/main' and env.get('GITHUB_EVENT_NAME')=='push' and env.get('GITHUB_ACTOR_ID')=='315379131' and env.get('GITHUB_RUN_ATTEMPT')=='1')
    require(re.fullmatch(r'[0-9a-f]{40}',env.get('GITHUB_SHA','')) and re.fullmatch(r'[1-9][0-9]{0,19}',env.get('GITHUB_RUN_ID','')))
    require(env.get('MORWEN_PRIVATE_TRANSFER_APPROVED')=='true' and bool(env.get('DEST_TOKEN')))
def private(api,token):
    p=api(token,'GET',BASE)
    require(p.get('full_name')==DEST and p.get('private') is True and p.get('id')==1420925740)
    return p
def verify_inventory(z):
    rows=z.infolist();names=z.namelist()
    require(len(rows)==len(set(names)) and len(rows)>0 and len(rows)<=200)
    require(sum(i.file_size for i in rows)<=CAP and all(not i.flag_bits&1 and not i.is_dir() and not (stat.S_ISLNK(i.external_attr>>16)) and '/' not in i.filename and '\\' not in i.filename and i.filename not in ('.','..') for i in rows))
    require(z.testzip() is None)
def extract(raw):
    require(len(raw)==ARCHIVE_BYTES and sha(raw)==ARCHIVE_SHA)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        verify_inventory(z)
        rec=json.loads(z.read('W108-receipt.json'))
        require(rec.get('status')=='NEW_CUSTOM_FRONT_STRANDS_SAVED_REOPENED_NOT_ADOPTED' and rec.get('save_reopen') is True and rec.get('candidate_sha256')==NATIVE_SHA)
        require(rec.get('hairs')==['Hair '+str(i) for i in range(1,6)])
        require(len(rec.get('screenshots',{}))==33 and all(n in z.namelist() and sha(z.read(n))==v for n,v in rec['screenshots'].items()))
        model=z.read(NATIVE_NAME)
    require(sha(model)==NATIVE_SHA)
    with zipfile.ZipFile(io.BytesIO(model)) as z:
        require(len(z.infolist())==4 and set(z.namelist())=={'meta.json','v1model/meta.json','v1model/data.bin','thumbnails/thumbnail.jpg'} and sum(i.file_size for i in z.infolist())<=CAP and z.testzip() is None)
    return model
def check_active(api,token,public_token,run_id):
    # Same-asset public jobs and all private jobs must be inactive.
    for repo,cred in ((DEST,token),(ORIGIN,public_token)):
        for status in ('queued','in_progress','waiting','requested','pending'):
            stage(('PRIVATE' if repo==DEST else 'PUBLIC')+'_ACTIVE_'+status.upper())
            q=api(cred,'GET','https://api.github.com/repos/'+repo+'/actions/runs?per_page=100&status='+status)
            runs=q.get('workflow_runs',[])
            require(isinstance(runs,list) and q.get('total_count')==len(runs) and len(runs)<=100)
            for a in runs:
                require(repo==ORIGIN and (str(a.get('id'))==run_id or 'morwen' not in (str(a.get('name',''))+' '+str(a.get('head_branch',''))).lower()))
def restore(api,env,root):
    identity(env);token=env['DEST_TOKEN'];stage('PRIVATE_DESTINATION');private(api,token)
    stage('ACTIVE_JOB_CHECK');check_active(api,token,env['GH_TOKEN'],env['GITHUB_RUN_ID'])
    stage('SOURCE_ARTIFACT_METADATA')
    m=api(token,'GET',BASE+'/actions/artifacts/'+str(ARTIFACT))
    require(m.get('id')==ARTIFACT and m.get('expired') is False and m.get('digest')=='sha256:'+ARCHIVE_SHA and m.get('size_in_bytes')==ARCHIVE_BYTES)
    w=m.get('workflow_run',{})
    require(w.get('id')==RUN and w.get('head_sha')==SOURCE_HEAD and w.get('repository_id')==1420925740)
    stage('SOURCE_ARTIFACT_DOWNLOAD')
    # gh's authenticated artifact download follows the signed storage redirect.
    # Bounded file size, timeout and private stderr; no public response dump.
    archive=root/'source.zip'
    child={k:v for k,v in env.items() if k not in ('DEST_TOKEN','GH_TOKEN')}
    child['GH_TOKEN']=token
    import resource
    def limit():resource.setrlimit(resource.RLIMIT_FSIZE,(ARCHIVE_BYTES+1,ARCHIVE_BYTES+1))
    with archive.open('xb') as out,(root/'download.stderr').open('xb') as err:
        subprocess.run(['gh','api','repos/'+DEST+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],env=child,stdout=out,stderr=err,timeout=180,check=True,preexec_fn=limit)
    stage('SOURCE_BYTES')
    model=extract(archive.read_bytes())
    with (Path(env['RUNNER_TEMP'])/'Morwen-resume.vroid').open('xb') as out:out.write(model)
    stage('SOURCE_VERIFIED')
def preserve(api,env,root):
    identity(env);token=env['DEST_TOKEN'];stage('REOPEN_EVIDENCE')
    ev=root/'evidence';native=(Path(env['RUNNER_TEMP'])/'Morwen-resume.vroid').read_bytes()
    require(sha(native)==NATIVE_SHA and (ev/'input-model.vroid').read_bytes()==native and (Path(env['HOME'])/'Documents/Morwen-resume.vroid').read_bytes()==native)
    require((ev/'recovery-result.txt').read_text().strip()=='REOPENED_READONLY_SOURCE_UNCHANGED')
    require('Morwen-resume.vroid' in (ev/'resumed-editor.txt').read_text())
    shot=(ev/'resumed-editor.png').read_bytes()
    require(shot[:16]==b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' and len(shot)<8*1024*1024)
    source=(root/'source.zip').read_bytes();require(extract(source)==native)
    # Store original W108 evidence archive and actual reopen image only in private destination.
    members={'W108-original.zip':source,'reopened-editor.png':shot}
    members['receipt.json']=json.dumps({'status':'READONLY_REOPEN_VERIFIED_NOT_ADOPTED','source_sha256':NATIVE_SHA,'source_archive_sha256':ARCHIVE_SHA,'public_run_id':env['GITHUB_RUN_ID'],'source_artifact_id':ARTIFACT,'screenshots_sha256':sha(shot)},sort_keys=True).encode()
    members['SHA256SUMS.json']=json.dumps({k:sha(v) for k,v in members.items()},sort_keys=True).encode()
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as z:
        for name,data in members.items():
            info=zipfile.ZipInfo(name);info.external_attr=0o100600<<16;z.writestr(info,data)
    raw=buf.getvalue();require(0<len(raw)<=CAP)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:verify_inventory(z);require(all(z.read(n)==v for n,v in members.items()))
    publish_private(api,env,raw,'recovery')
def publish_private(api,env,raw,kind):
    # Both fixed routes use the same reviewed private Release protocol.
    identity(env);token=env['DEST_TOKEN']
    require(kind in ('recovery','front_trial') and 0<len(raw)<=CAP)
    prefix,name,body={
        'recovery':('morwen-native-recovery-run-','Morwen-native-recovery.zip','Read-only native recovery evidence. NOT_ADOPTED.'),
        'front_trial':('morwen-native-front-trial-run-','Morwen-native-front-trial.zip','Isolated native Front trial; independent design/art/technical QA pending. NOT_ADOPTED.')
    }[kind]
    stage('PRIVATE_DESTINATION_RECHECK');private(api,token);check_active(api,token,env['GH_TOKEN'],env['GITHUB_RUN_ID'])
    ref=api(token,'GET',BASE+'/git/ref/heads/main')
    target=ref.get('object',{}).get('sha','')
    require(ref.get('ref')=='refs/heads/main' and re.fullmatch(r'[0-9a-f]{40}',target))
    tag=prefix+env['GITHUB_RUN_ID']
    from release_transport import TransportError
    stage('PRIVATE_RELEASE_ABSENCE')
    for page in range(1,21):
        rows=api(token,'GET',BASE+'/releases?per_page=100&page='+str(page))
        require(isinstance(rows,list) and len(rows)<=100 and all(x.get('tag_name')!=tag for x in rows))
        if len(rows)<100:break
    else:raise ValueError('inventory')
    for endpoint in ('/releases/tags/'+tag,'/git/ref/tags/'+tag):
        try:api(token,'GET',BASE+endpoint)
        except TransportError as e:require(e.status==404)
        else:raise ValueError('exists')
    stage('PRIVATE_DRAFT_CREATE');private(api,token)
    rel=api(token,'POST',BASE+'/releases',json.dumps(dict(tag_name=tag,target_commitish=target,name=tag,body=body,draft=True,prerelease=True,make_latest='false')).encode())
    rid=rel.get('id');require(type(rid) is int and rid>0 and rel.get('draft') is True and rel.get('tag_name')==tag)
    stage('PRIVATE_ASSET_UPLOAD');private(api,token)
    asset=api(token,'POST','https://uploads.github.com/repos/'+DEST+'/releases/'+str(rid)+'/assets?name='+name,raw,'application/zip')
    aid=asset.get('id');require(type(aid) is int and aid>0 and asset.get('name')==name and asset.get('state')=='uploaded' and asset.get('size')==len(raw) and asset.get('digest')=='sha256:'+sha(raw))
    url=BASE+'/releases/assets/'+str(aid)
    stage('PRIVATE_DRAFT_READBACK');require(api(token,'GET',url,binary=True,limit=len(raw))==raw)
    stage('PRIVATE_RELEASE_FINALIZE');private(api,token)
    rel=api(token,'PATCH',BASE+'/releases/'+str(rid),json.dumps(dict(draft=False,prerelease=True,make_latest='false')).encode())
    require(rel.get('id')==rid and rel.get('draft') is False and rel.get('prerelease') is True and rel.get('tag_name')==tag)
    stage('PRIVATE_FINAL_READBACK');private(api,token);require(api(token,'GET',url,binary=True,limit=len(raw))==raw)
    stage('PRIVATE_READBACK_VERIFIED')
def main():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'private-preservation'))
    from release_transport import request
    env=os.environ.copy();root=Path(env['RUNNER_TEMP'])/'morwen-private-recovery'
    require(root.is_dir() and not root.is_symlink() and root.stat().st_mode&0o077==0)
    require(len(sys.argv)==2 and sys.argv[1] in ('restore','preserve'))
    (restore if sys.argv[1]=='restore' else preserve)(request,env,root)
if __name__=='__main__':
    try:main()
    except Exception as exc:
        # Report only a bounded numeric HTTP status, never exception content.
        code=getattr(exc,'status',0)
        suffix='_HTTP_'+str(code) if type(code) is int and 400<=code<=599 else ''
        print('RECOVERY_BLOCKED_AT_'+STAGE+suffix,flush=True)
        raise SystemExit(1) from None
