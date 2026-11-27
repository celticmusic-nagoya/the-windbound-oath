"""Bounded, version-locked bpy preparation for existing Linux Python QA routes.

This is not the CLI Blender installer or a cross-run executable cache.
Reuse only the already installed, matching environment of the current job.
"""
import importlib.metadata
import json
import os
import platform
from pathlib import Path
import re
import subprocess
import sys
import time

# Actual successful #364 run 45845779240, Python 3.13/Linux x64 wheel set.
LOCK = {
    "bpy": "5.3.0",
    "pillow": "12.3.0",
    "attrs": "26.1.0",
    "cattrs": "26.2.1",
    "certifi": "2026.11.20",
    "charset-normalizer": "3.5.3",
    "cython": "3.3.2",
    "idna": "3.20",
    "numpy": "2.5.5",
    "requests": "2.34.2",
    "typing-extensions": "4.16.0",
    "urllib3": "2.8.0",
    "zstandard": "0.25.0",
}
REQUIREMENTS = Path(__file__).with_name('requirements-bpy-linux-x64-py313.txt')


def verified_requirements():
    rows = {}
    for line in REQUIREMENTS.read_text().splitlines():
        match = re.fullmatch(r'([a-z0-9-]+)==([0-9.]+) --hash=sha256:([a-f0-9]{64})', line)
        if not match or match[1] in rows:
            raise RuntimeError('invalid bpy requirements lock')
        rows[match[1]] = match[2]
    if rows != LOCK:
        raise RuntimeError('bpy requirements lock version mismatch')
    return REQUIREMENTS


VERIFY = """import bpy, PIL
if bpy.app.version_string != '5.3.0' or bpy.app.build_hash.decode() != '02f0899d78e3' or PIL.__version__ != '12.3.0':
    raise RuntimeError('unexpected bpy build or Pillow version')
"""


def check_platform():
    if sys.version_info[:2] != (3, 13) or sys.platform != "linux" or platform.machine() != "x86_64":
        raise RuntimeError("bpy runtime lock requires Python 3.13 Linux x86_64")


def mismatches():
    out = {}
    for name, expected in LOCK.items():
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        if actual != expected:
            out[name] = actual
    return out


def child_env():
    # Acquisition and runtime probes do not need GitHub or private transfer tokens.
    return {k: v for k, v in os.environ.items()
            if not k.startswith(("PYTHON", "PIP_")) and k not in
            {"GH_TOKEN", "GITHUB_TOKEN", "HANDOFF_TOKEN", "TWO_HANDOFF_READ_TOKEN"}}


def prepare():
    check_platform()
    started = time.monotonic()
    requirements = verified_requirements()
    missing = mismatches()
    env = child_env()
    calls = 0
    if missing:
        calls = 1
        print("bpy runtime: installing pinned wheel set once", file=sys.stderr, flush=True)
        subprocess.run([sys.executable, "-I", "-m", "pip", "--isolated", "install",
                        "--index-url", "https://pypi.org/simple", "--only-binary=:all:",
                        "--timeout", "30", "--retries", "0",
                        "--require-hashes", "--no-deps", "-r", str(requirements)],
                       check=True, timeout=180, env=env, stdout=sys.stderr)
        # importlib metadata is read again in the current process.
        if mismatches():
            raise RuntimeError("installed runtime does not match locked versions")
    subprocess.run([sys.executable, "-I", "-c", VERIFY], check=True,
                   timeout=30, env=env, stdout=sys.stderr)
    return dict(status="VERIFIED", route="INSTALLED" if calls else "REUSED",
                pip_install_calls=calls, elapsed_seconds=round(time.monotonic() - started, 3),
                blender_version="5.3.0", build="02f0899d78e3", versions=LOCK)


if __name__ == "__main__":
    try:
        print(json.dumps(prepare(), sort_keys=True), flush=True)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps(dict(status="FAILED", error_type=type(exc).__name__)), flush=True)
        raise
