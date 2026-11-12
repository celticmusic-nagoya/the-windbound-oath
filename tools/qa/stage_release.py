#!/usr/bin/env python3
"""UX-MOBILE-24: stage an explicitly prepared release directory, fail closed.

Usage: python tools/qa/stage_release.py SOURCE_DIR OUTPUT_DIR
Never uses the development repository root as an implicit release build.
"""
from pathlib import Path
import shutil
import sys
from check_release_ui import audit

def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: stage_release.py SOURCE_DIR OUTPUT_DIR", file=sys.stderr)
        return 2
    src, dst = (Path(p).resolve() for p in sys.argv[1:])
    if not src.is_dir() or not (src / "index.html").is_file():
        print("BLOCKED: source must contain index.html", file=sys.stderr)
        return 2
    if src == dst or src in dst.parents or dst in src.parents:
        print("BLOCKED: source and output must be separate, non-nested directories", file=sys.stderr)
        return 2
    if dst.exists():
        print("BLOCKED: output already exists; refusing overwrite", file=sys.stderr)
        return 2
    hits = audit((src / "index.html").read_text(encoding="utf-8"))
    if hits:
        print("BLOCKED: development hooks in release candidate: " + ", ".join(hits), file=sys.stderr)
        return 1
    shutil.copytree(src, dst, symlinks=False)
    print(f"STAGED: {dst} (HTML hook audit PASS; additional security and asset QA still required)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
