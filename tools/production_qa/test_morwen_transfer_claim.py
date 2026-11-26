import os, tempfile, subprocess, pathlib, concurrent.futures, sys
from morwen_transfer_claim import reserve, claim, verify
from shared_asset_lease import git
from shared_asset_reservation import ref_for
root=pathlib.Path(tempfile.mkdtemp(prefix='morwen-local-cas-'))
remote=str(root/'remote.git')
subprocess.run(['git','init','--bare',remote],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
work=root/'work'; subprocess.run(['git','init',str(work)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
os.chdir(work)
git('config','user.email','test@invalid'); git('config','user.name','Local test'); git('commit','--allow-empty','-m','fixture'); rev=git('rev-parse','HEAD'); git('push',remote,'HEAD:refs/heads/main')
asset='MORWEN_LOCAL_TEST'; req='12345'; run='67890'; cases=[]
def reject(name,fn):
    try: fn()
    except (ValueError,RuntimeError,subprocess.CalledProcessError): cases.append(name); return
    raise AssertionError(name)
token=reserve(remote,asset,rev,req); cases.append('reserve')
reject('duplicate reservation',lambda:reserve(remote,asset,rev,req))
reject('wrong request',lambda:claim(remote,asset,token,rev,'12346',run,'1'))
reject('wrong revision',lambda:claim(remote,asset,token,'0'*40,req,run,'1'))
reject('retry attempt',lambda:claim(remote,asset,token,rev,req,run,'2'))
# separate git work trees: no shared FETCH_HEAD in this race
workers=[]
for i in range(2):
    w=root/f'worker{i}'; subprocess.run(['git','clone','--no-checkout','--branch','main',remote,str(w)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); workers.append(w)
code='from morwen_transfer_claim import claim; import sys; print(claim(*sys.argv[1:]))'
def attempt(i):
    return subprocess.run([sys.executable,'-c',code,remote,asset,token,rev,req,str(int(run)+i),'1'],cwd=workers[i],env=dict(os.environ,PYTHONPATH=str(pathlib.Path(__file__).parent)),capture_output=True,text=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(attempt,range(2)))
winners=[(i,p.stdout.strip()) for i,p in enumerate(results) if p.returncode==0]; assert len(winners)==1,winners
cases.append('two simultaneous claims: exactly one winner')
i,owned=winners[0]; winning_run=str(int(run)+i)
verify(remote,asset,owned,rev,req,winning_run,'1'); cases.append('valid run verification')
reject('wrong run verification',lambda:verify(remote,asset,owned,rev,req,str(int(winning_run)+100),'1'))
reject('replay original token',lambda:claim(remote,asset,token,rev,req,run,'1'))
reject('claim token replay as reservation',lambda:claim(remote,asset,owned,rev,req,run,'1'))
assert git('ls-remote','--refs',remote,ref_for(asset))==f'{owned}\t{ref_for(asset)}'; cases.append('owner intact after failures')
print(f'{len(cases)}/{len(cases)} PASS'); print('\n'.join(cases))
