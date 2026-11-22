"""Isolated multi-writer regression using a local bare Git remote, never production refs."""
import concurrent.futures
import subprocess
import tempfile
import os
from pathlib import Path
from shared_asset_lease import acquire, assert_owned, release

def main():
    with tempfile.TemporaryDirectory() as tmp:
        previous=os.getcwd()
        try:
            root=Path(tmp)
            remote=str(root/"remote.git")
            subprocess.run(["git","init","--bare",remote],check=True)
            work=root/"work"
            subprocess.run(["git","init",str(work)],check=True)
            os.chdir(work)
            subprocess.run(["git","-c","user.name=QA","-c","user.email=qa@invalid","commit","--allow-empty","-m","fixture"],check=True)
            head=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
            def attempt(key):
                try: return acquire(remote,key,head)
                except subprocess.CalledProcessError: return None
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                a,b,c=list(pool.map(attempt,["QA-MORWEN","QA-MORWEN","QA-LIND"]))
            assert (a is None)!=(b is None) and c is not None
            winner=a or b
            assert_owned(remote,"QA-MORWEN",winner)
            assert_owned(remote,"QA-LIND",c)
            release(remote,"QA-MORWEN",winner)
            next_token=acquire(remote,"QA-MORWEN",head)
            assert next_token!=winner
            try: release(remote,"QA-MORWEN",winner)
            except RuntimeError: pass
            else: raise AssertionError("stale release accepted")
            assert_owned(remote,"QA-MORWEN",next_token)
            release(remote,"QA-MORWEN",next_token)
            release(remote,"QA-LIND",c)
            print("ISOLATED_MULTI_WRITER_PASS")
        finally:
            os.chdir(previous)

if __name__=="__main__":
    main()
