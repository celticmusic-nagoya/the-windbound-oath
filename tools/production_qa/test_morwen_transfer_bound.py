import os, subprocess, tempfile, pathlib, sys, time
from morwen_transfer_claim import reserve, claim, verify, await_bound
from shared_asset_lease import git
with tempfile.TemporaryDirectory() as tmp:
    base=pathlib.Path(tmp); remote=str(base/'remote.git'); work=base/'work'
    subprocess.run(['git','init','--bare',remote],check=True,capture_output=True)
    subprocess.run(['git','init',str(work)],check=True,capture_output=True)
    os.chdir(work)
    git('config','user.email','test@invalid'); git('config','user.name','Local test')
    git('commit','--allow-empty','-m','fixture'); rev=git('rev-parse','HEAD'); git('push',remote,'HEAD:refs/heads/main')
    asset='MORWEN_WAIT_TEST'; request='12345'; run='67890'
    cases=[]
    def reject(name, fn, expected=(ValueError,RuntimeError,TimeoutError,subprocess.CalledProcessError)):
        try: fn()
        except expected: cases.append(name); return
        raise AssertionError(name)
    reject('absent lease',lambda:await_bound(remote,asset,'a'*40,rev,request,run,'1',1))
    initial=reserve(remote,asset,rev,request)
    reject('unconsumed token timeout',lambda:await_bound(remote,asset,initial,rev,request,run,'1',1))
    reject('wrong request',lambda:await_bound(remote,asset,initial,rev,'12346',run,'1',1))
    reject('attempt 2',lambda:await_bound(remote,asset,initial,rev,request,run,'2',1))
    other=base/'other'; subprocess.run(['git','clone','--branch','main',remote,str(other)],check=True,capture_output=True)
    cmd='import time,sys; from morwen_transfer_claim import claim; time.sleep(0.7); print(claim(*sys.argv[1:]))'
    worker=subprocess.Popen([sys.executable,'-c',cmd,remote,asset,initial,rev,request,run,'1'],cwd=other,env=dict(os.environ,PYTHONPATH=str(pathlib.Path(__file__).resolve().parent)),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    token=await_bound(remote,asset,initial,rev,request,run,'1',10)
    out,err=worker.communicate(timeout=10); assert worker.returncode==0,err; assert token==out.strip(); cases.append('wait then verified real CAS handoff')
    verify(remote,asset,token,rev,request,run,'1'); cases.append('current bound token verified')
    assert await_bound(remote,asset,initial,rev,request,run,'1',3)==token; cases.append('already bound')
    reject('wrong original reservation',lambda:await_bound(remote,asset,'a'*40,rev,request,run,'1',3))
    reject('bound token supplied as reservation',lambda:await_bound(remote,asset,token,rev,request,run,'1',3))
    reject('other run',lambda:await_bound(remote,asset,initial,rev,request,'67891','1',3))
    reject('other revision',lambda:await_bound(remote,asset,initial,'0'*40,request,run,'1',3))
    reject('invalid timeout',lambda:await_bound(remote,asset,initial,rev,request,run,'1',121))
    print(f'{len(cases)}/{len(cases)} PASS',*cases,sep='\n')
