"""Exercise completion with actual local bare Git CAS, no hosted mutation."""
import os, pathlib, subprocess, tempfile
from morwen_transfer_claim import reserve, claim, complete, verify
from shared_asset_lease import git, ref_for

with tempfile.TemporaryDirectory() as td:
    base=pathlib.Path(td); remote=str(base/'remote.git'); work=base/'work'
    subprocess.run(['git','init','--bare',remote],check=True,capture_output=True)
    subprocess.run(['git','init',str(work)],check=True,capture_output=True)
    os.chdir(work)
    git('config','user.email','test@invalid'); git('config','user.name','Local QA')
    git('commit','--allow-empty','-m','fixture'); rev=git('rev-parse','HEAD'); git('push',remote,'HEAD:refs/heads/main')
    asset='MORWEN_TEST'; request='12345'; run='67890'; producer='a'*64
    initial=reserve(remote,asset,rev,request)
    token=claim(remote,asset,initial,rev,request,run,'1')
    receipt=dict(scope='PRIVATE_CANDIDATE_READBACK_VERIFIED',adoption='NOT_ADOPTED',kind='blend',revision=rev,source_archive_sha256=producer,run_id=run,request_id=request,sha256='b'*64,release_id=1,asset_id=2,bytes=1234)
    cases=[]
    def invoke(r=receipt,reservation=initial,run_id=run,attempt='1'):
        return complete(remote,asset,reservation,rev,request,run_id,attempt,producer,r)
    def reject(name,fn):
        try: fn()
        except (ValueError,RuntimeError,TimeoutError,subprocess.CalledProcessError): pass
        else: raise AssertionError(name)
        verify(remote,asset,token,rev,request,run,'1')
        cases.append(name)
    for k,v in [('scope','NOT_RUN'),('kind','vrm'),('revision','0'*40),('source_archive_sha256','0'*64),('run_id','67891'),('request_id','12346'),('sha256','bad'),('release_id',0),('asset_id',True),('bytes',128*1024*1024+1),('adoption','ADOPTED')]:
        reject(k,lambda k=k,v=v:invoke(dict(receipt,**{k:v})))
    reject('wrong reservation',lambda:invoke(reservation='0'*40))
    reject('attempt 2',lambda:invoke(attempt='2'))
    invoke(); assert not git('ls-remote','--refs',remote,ref_for(asset)); cases.append('exact completion released')
    newer=reserve(remote,asset,rev,'12346'); successor=claim(remote,asset,newer,rev,'12346','67891','1')
    try: invoke()
    except (ValueError,RuntimeError,TimeoutError,subprocess.CalledProcessError): pass
    else: raise AssertionError('stale replay')
    verify(remote,asset,successor,rev,'12346','67891','1'); cases.append('stale completion cannot release new owner')
    print(f'{len(cases)}/{len(cases)} PASS',*cases,sep='\n')
