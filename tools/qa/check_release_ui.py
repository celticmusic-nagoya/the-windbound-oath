#!/usr/bin/env python3
"""UX-MOBILE-21: fail closed when development hooks enter a release HTML artifact.

Usage:
  python tools/qa/check_release_ui.py path/to/release/index.html

This is a release-artifact guard, NOT proof that all debug code is absent.
Do not run against the development index.html as a passing release test.
"""
from pathlib import Path
import re
import sys

PATTERNS = {
    "dev menu": r"""id=["']dev(?:Btn|Panel)["']""",
    "instant-kill command": r"""id=["'](?:nDevKill|rbDevKill)["']""",
    "instant-kill binding": r"PrologueCombat\.instantKill\s*\(",
    "development event jump": r"\bdevJump\s*\(",
    "release-preview flag": r"releasePreview",
}

def audit(html: str) -> list[str]:
    return [name for name, pattern in PATTERNS.items() if re.search(pattern, html)]

def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_release_ui.py RELEASE_INDEX_HTML", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"RELEASE_AUDIT_FAIL: missing artifact: {path}", file=sys.stderr)
        return 2
    hits = audit(path.read_text(encoding="utf-8"))
    if hits:
        print("RELEASE_AUDIT_FAIL: development hooks detected: " + ", ".join(hits))
        return 1
    print("RELEASE_AUDIT_PASS: no known development UI hooks detected")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
