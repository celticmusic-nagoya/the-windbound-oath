"""Local bare Git regression; no hosted refs or native files are touched."""
import os
import pathlib
import subprocess
import tempfile
import time
from morwen_transfer_claim import binding, reserve, claim, read_binding, await_bound, verify
from shared_asset_reservation import ref_for

def git(w, *args):
    return subprocess.run(["git", "-C", str(w), *args], text=True, check=True, capture_output=True).stdout.strip()

def reject(name, operation, cases):
    try:
        operation()
    except (RuntimeError, ValueError, subprocess.CalledProcessError):
        cases.append(name)
    else:
        raise AssertionError(name)

def main():
    previous_cwd = os.getcwd()
    previous_scope = os.environ.pop("MORWEN_TRANSFER_GIT_DIR", None)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            bare, author, root, full = (p / n for n in ("remote.git", "author", "root", "full"))
            bare.mkdir(); author.mkdir()
            git(bare, "init", "--bare")
            git(author, "init", "-b", "main")
            git(author, "config", "user.name", "Local QA")
            git(author, "config", "user.email", "qa@invalid")
            revs = []
            for i in range(30):
                (author / "payload").write_text(str(i))
                git(author, "add", "payload")
                git(author, "commit", "-m", str(i))
                revs.append(git(author, "rev-parse", "HEAD"))
            git(author, "branch", "legacy", revs[4])
            remote = bare.as_uri()
            git(author, "push", remote, "main", "legacy")
            git(p, "clone", "--depth=1", "--branch", "legacy", remote, str(root))
            work = root / "transfer-control"
            git(root, "clone", "--depth=1", "--branch", "main", remote, str(work))
            git(p, "clone", "--branch", "main", remote, str(full))
            asset, req, run, rev = "MORWEN_LOCAL_TEST", "12345", "67890", revs[-1]
            os.chdir(author)
            parent = reserve(remote, asset, rev, req)
            token = claim(remote, asset, parent, rev, req, run, "1")
            expected = binding(asset, rev, req, run, "1")
            ref = ref_for(asset)
            os.chdir(root)
            old_head = git(root, "rev-parse", "HEAD")
            old_refs = git(work, "show-ref")
            cases = []
            def read(w, tok=token, exp=expected, reservation=parent):
                os.environ["MORWEN_TRANSFER_GIT_DIR"] = str(w)
                read_binding("origin", asset, tok, exp, time.monotonic()+10, reservation)
                assert pathlib.Path.cwd() == root
            read(work); cases.append("scoped shallow binding")
            assert git(root, "rev-parse", "HEAD") == old_head
            assert git(work, "show-ref") == old_refs
            assert git(work, "rev-list", "--count", "HEAD") == "1"
            cases.append("root and shallow history unchanged")
            read(full)
            assert git(full, "rev-parse", "--is-shallow-repository") == "false"
            assert git(full, "rev-list", "--count", "HEAD") == "30"
            cases.append("full history unchanged")
            reject("wrong token", lambda: read(work, tok="c"*40), cases)
            reject("wrong parent", lambda: read(work, reservation="c"*40), cases)
            reject("wrong run", lambda: read(work, exp=dict(expected, run="67891")), cases)
            reject("wrong revision", lambda: read(work, exp=dict(expected, revision=revs[0])), cases)
            reject("wrong request", lambda: read(work, exp=dict(expected, request="12346")), cases)
            reject("wrong checkout", lambda: read(root), cases)
            os.environ["MORWEN_TRANSFER_GIT_DIR"] = str(work)
            assert await_bound("origin", asset, parent, rev, req, run, "1", 10) == token
            verify("origin", asset, token, rev, req, run, "1")
            cases.append("await and verify through scoped checkout")
            os.environ.pop("MORWEN_TRANSFER_GIT_DIR")
            os.chdir(full)
            verify("origin", asset, token, rev, req, run, "1")
            cases.append("default checkout compatibility")
            assert git(author, "ls-remote", "--refs", remote, ref) == f"{token}\t{ref}"
            cases.append("remote fence preserved")
            os.chdir(previous_cwd)
            print(f"{len(cases)}/{len(cases)} PASS", *cases, sep="\n")
    finally:
        os.chdir(previous_cwd)
        os.environ.pop("MORWEN_TRANSFER_GIT_DIR", None)
        if previous_scope is not None:
            os.environ["MORWEN_TRANSFER_GIT_DIR"] = previous_scope

if __name__ == "__main__":
    main()
