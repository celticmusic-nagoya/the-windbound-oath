"""Select a verified cached application or build into a separate work directory."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from manager import HERE, canonical, sha

PROOFS = {
    "two-env-v2-bbd0205f555b77b35aff404f409a56c3773d8091f53d6202d04113b91fa6de7c": (
        "blender-530-133-proof.json",
        "d044ff1d6f41b686e33733086ae3ac9d6c77092214d1c617f43e002a5cfa9b2c",
    ),
    "two-env-v2-ac7b2c3360e3ddee164fb959bc2f9ef3c67174e110da7fcb4104e854dae2e18d": (
        "blender-530-376-proof.json",
        "e3dc3d6cd26d3c5aca42fd83e7916bd8e2a89eee97473367e4cb899789cda37b",
    ),
}


def trusted_proof(key):
    item = PROOFS.get(key)
    if item is None:
        return None
    name, expected = item
    path = HERE / name
    if sha(path) != expected:
        raise ValueError("cold proof integrity check failed")
    proof = json.loads(path.read_text())
    if proof.get("key") != key:
        raise ValueError("cold proof key mismatch")
    return proof


def manager(*args, **kwargs):
    return subprocess.run([sys.executable, str(HERE / "manager.py"), *map(str, args)], **kwargs)


def ensure(cache, fallback, report, cache_hit):
    key = manager("key", stdout=subprocess.PIPE, text=True, check=True).stdout.strip()
    proof = trusted_proof(key)
    state = "MISS"
    if cache_hit and proof is not None:
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
    result.update(cache_state=state, trusted_manifest_match=(proof is not None and
                  result["manifest_sha256"] == proof["manifest_sha256"]), application_path=str((cache if state == "HIT" else fallback) / "app"))
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
