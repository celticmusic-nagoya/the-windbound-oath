"""Isolated integration only; no production lease or native mutation."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from shared_session_contract import fingerprint, verified_file_hashes, FIELDS
from shared_session_controller import run
from bounded_operation import run_operation
from session_plan import sha

PIN = "b163511dcc5a6951bceb69c196578af3930db281"
ASSET = "MORWEN"

def main():
    common = Path(sys.argv[1]).resolve()
    if subprocess.check_output(["git","-C",str(common),"rev-parse","HEAD"],text=True).strip()!=PIN:
        raise RuntimeError("wrong common base")
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        remote=root/"isolated.git"
        work=root/"work"
        work.mkdir()
        def git(*args):
            return subprocess.check_output(["git","-C",str(work),*args],text=True).strip()
        git("init","--bare",str(remote))
        git("init")
        git("config","user.email","fixture@example.invalid")
        git("config","user.name","Isolated fixture")
        (work/"input").write_text("synthetic fixture, not VRoid")
        git("add","input")
        git("commit","-m","fixture")
        head=git("rev-parse","HEAD")
        git("push",str(remote),"HEAD:refs/heads/fixture")
        hashes=verified_file_hashes(work,{"input":sha(work/"input")})
        fields={k:hashes for k in FIELDS}
        stages=[dict(id="fixture",deps=[],qualified=True,seconds=30,fingerprint=fingerprint(ASSET,"fixture",fields))]
        def execute(stage,token,deadline):
            p=work/"fixture.txt"
            run_operation([sys.executable,"-c","from pathlib import Path; Path('fixture.txt').write_text('synthetic')"],deadline,cwd=work,grace=1)
            assert p.read_text()=="synthetic"
            return dict(path=p.name,sha256=sha(p),fingerprint=stage["fingerprint"],reopened=True)
        def persist(records,token,deadline):
            # Isolated local transport only: NOT native/off-runner qualification.
            if time.monotonic()>=deadline: return False
            p=work/"ledger.json"
            p.write_text(json.dumps(records,sort_keys=True))
            run_operation(["git","add","ledger.json",*[v["path"] for v in records.values()]],deadline,cwd=work,grace=1)
            if git("status","--porcelain","ledger.json"):
                run_operation(["git","commit","-m","fixture ledger"],deadline,cwd=work,grace=1)
                run_operation(["git","push",str(remote),"HEAD:refs/heads/fixture"],deadline,cwd=work,grace=1)
            observed=subprocess.check_output(["git","--git-dir",str(remote),"show","refs/heads/fixture:ledger.json"])
            if observed!=p.read_bytes(): return False
            import hashlib
            for record in records.values():
                data=subprocess.check_output(["git","--git-dir",str(remote),"show","refs/heads/fixture:"+record["path"]],timeout=max(0.01,deadline-time.monotonic()))
                if hashlib.sha256(data).hexdigest()!=record["sha256"]: return False
            return True
        completed={}
        previous=Path.cwd()
        os.chdir(work)
        try:
            assert run(str(remote),ASSET,head,work,stages,completed,execute,persist,budget=120,reserve=30)==["fixture"]
            assert run(str(remote),ASSET,head,work,stages,completed,execute,persist,budget=120,reserve=30)==[]
        finally:
            os.chdir(previous)
        print("ISOLATED_CONTRACT_PASS; NATIVE_AND_OFF_RUNNER_NOT_RUN")

if __name__=="__main__":
    main()
