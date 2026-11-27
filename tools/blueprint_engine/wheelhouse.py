"""Isolated wheel archive reuse qualification, never restore installed executables.

A fresh official HTTPS metadata lookup supplies the expected SHA for each exact
wheel. This is not an immutable offline trust root or a production cache grant.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.request import urlopen

from blueprint_engine.ensure_runtime import LOCK, VERIFY, check_platform, child_env, mismatches

# Filenames observed in the successful V13 export run 45845779240.
WHEELS = {
    "bpy": "bpy-5.3.0-cp313-cp313-manylinux_2_28_x86_64.whl",
    "pillow": "pillow-12.3.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl",
    "attrs": "attrs-26.1.0-py3-none-any.whl",
    "cattrs": "cattrs-26.2.1-py3-none-any.whl",
    "certifi": "certifi-2026.11.20-py3-none-any.whl",
    "charset-normalizer": "charset_normalizer-3.5.3-cp313-cp313-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl",
    "cython": "cython-3.3.2-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl",
    "idna": "idna-3.20-py3-none-any.whl",
    "numpy": "numpy-2.5.5-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl",
    "requests": "requests-2.34.2-py3-none-any.whl",
    "typing-extensions": "typing_extensions-4.16.0-py3-none-any.whl",
    "urllib3": "urllib3-2.8.0-py3-none-any.whl",
    "zstandard": "zstandard-0.25.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
}
MAX_BYTES = 512 * 1024**2


def select_record(name, data):
    version = LOCK[name]
    if data.get("info", {}).get("version") != version:
        raise ValueError("unexpected upstream version")
    rows = [x for x in data["urls"] if x.get("filename") == WHEELS[name]]
    if len(rows) != 1:
        raise ValueError("exact wheel not uniquely available: " + name)
    row = rows[0]
    digest = row.get("digests", {}).get("sha256", "")
    size = row.get("size")
    if (row.get("yanked") is not False or row.get("packagetype") != "bdist_wheel"
            or not re.fullmatch(r"[a-f0-9]{64}", digest)
            or type(size) is not int or not 0 < size <= MAX_BYTES):
        raise ValueError("unsafe wheel metadata: " + name)
    return dict(name=name, version=version, filename=WHEELS[name], sha256=digest, size=size)


def official_record(name):
    url = f"https://pypi.org/pypi/{name}/{LOCK[name]}/json"
    with urlopen(url, timeout=10) as response:
        if response.geturl() != url:
            raise ValueError("unexpected metadata redirect")
        data = response.read(2 * 1024**2 + 1)
    if len(data) > 2 * 1024**2:
        raise ValueError("metadata too large")
    return select_record(name, json.loads(data))


def canonical(records):
    return (json.dumps(records, sort_keys=True, separators=(",", ":")) + "\n").encode()


def validate_records(records):
    if not isinstance(records, list) or len(records) != len(LOCK):
        raise ValueError("incomplete wheel lock")
    names = set()
    for row in records:
        name = row["name"]
        if (name in names or name not in LOCK or row["version"] != LOCK[name]
                or row["filename"] != WHEELS[name] or not re.fullmatch(r"[a-f0-9]{64}", row["sha256"])
                or type(row["size"]) is not int or not 0 < row["size"] <= MAX_BYTES):
            raise ValueError("invalid wheel lock entry")
        names.add(name)
    if sum(r["size"] for r in records) > MAX_BYTES:
        raise ValueError("wheel set exceeds byte budget")


def lock_key(records):
    validate_records(records)
    return "two-bpy-wheel-v1-" + hashlib.sha256(canonical(records)).hexdigest()


def verify_wheels(root, records):
    validate_records(records)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("unsafe wheel directory")
    if {p.name for p in root.iterdir()} != {r["filename"] for r in records}:
        raise ValueError("unexpected wheel inventory")
    for row in records:
        path = root / row["filename"]
        if path.is_symlink() or not path.is_file() or path.stat().st_size != row["size"]:
            raise ValueError("unsafe wheel file: " + path.name)
        with path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != row["sha256"]:
                raise ValueError("wheel SHA mismatch: " + path.name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["resolve", "download", "install"])
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    check_platform()
    started = time.monotonic()
    if args.mode == "resolve":
        with ThreadPoolExecutor(max_workers=4) as pool:
            records = list(pool.map(official_record, sorted(LOCK)))
        key = lock_key(records)
        args.lock.write_bytes(canonical(records))
        print(key)
        return
    records = json.loads(args.lock.read_text())
    key = lock_key(records)
    root = args.root
    if root is None:
        raise ValueError("wheel root required")
    requirements = args.lock.with_suffix(".requirements.txt")
    requirements.write_text("".join(f"{r['name']}=={r['version']} --hash=sha256:{r['sha256']}\n" for r in records))
    pip = [sys.executable, "-I", "-m", "pip", "--isolated"]
    options = ["--require-hashes", "--only-binary=:all:", "--no-deps", "-r", str(requirements)]
    if args.mode == "download":
        root.mkdir(exist_ok=False)
        subprocess.run(pip + ["download", "--index-url", "https://pypi.org/simple",
                              "--timeout", "30", "--retries", "0", "--dest", str(root)] + options,
                       check=True, timeout=180, env=child_env(), stdout=sys.stderr)
        verify_wheels(root, records)
    else:
        verify_wheels(root, records)
        subprocess.run(pip + ["install", "--no-index", "--find-links", str(root),
                              "--force-reinstall"] + options,
                       check=True, timeout=180, env=child_env(), stdout=sys.stderr)
        if mismatches():
            raise RuntimeError("locked runtime mismatch")
        subprocess.run([sys.executable, "-I", "-c", VERIFY], check=True,
                       timeout=30, env=child_env(), stdout=sys.stderr)
    print(json.dumps(dict(mode=args.mode, key=key, bytes=sum(r["size"] for r in records),
                          elapsed_seconds=round(time.monotonic()-started, 3), verified=True)))


if __name__ == "__main__":
    main()
