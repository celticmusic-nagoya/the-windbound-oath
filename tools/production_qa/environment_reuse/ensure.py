"""Select a verified cached application or build into a separate work directory."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from manager import HERE, canonical, sha

PROOF = HERE / "blender-530-proof.json"
PROOF_SHA256 = "0cfcb2dcec1bb1098908fdf37862d61c28ef96b1ed3961d17e005d536eb70cd7"


def manager(*args, **kwargs):
    return subprocess.run([sys.executable, str(HERE / "manager.py"), *map(str, args)], **kwargs)


def ensure(cache, fallback, report, cache_hit):
    if not sha(PROOF) == PROOF_SHA256:
        raise ValueError("cold proof integrity check failed")
    proof = json.loads(PROOF.read_text())
    key = manager("key", stdout=subprocess.PIPE, text=True, check=True).stdout.strip()
    state = "MISS"
    if cache_hit and key == proof["key"]:
        warm = manager("warm", "--root", cache, "--expected", proof["manifest_sha256"],
                       "--report", report, check=False)
        if warm.returncode == 0:
            state = "HIT"
    if state != "HIT":
        state = "REJECTED" if cache_hit else "MISS"
        if cache.resolve() == fallback.resolve() or fallback.exists() or fallback.is_symlink():
            raise ValueError("fallback requires an unused isolated directory")
        manager("cold", "--root", fallback, "--report", report, check=True)
    result = json.loads(report.read_text())
    result.update(cache_state=state, application_path=str((cache if state == "HIT" else fallback) / "app"))
    report.write_bytes(canonical(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--fallback", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--cache-hit", action="store_true")
    args = parser.parse_args()
    result = ensure(args.cache, args.fallback, args.report, args.cache_hit)
    print(json.dumps(result, sort_keys=True))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            print(f"blender={result['application_path']}/blender", file=output)
