#!/usr/bin/env python3
"""Read-only metadata gate for Morwen rig source selection."""
import json
from pathlib import Path
import sys

EXPECTED = {
    "name": "7374.png",
    "actualMime": "image/jpeg",
    "width": 1536,
    "height": 1024,
    "sha256": "47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638",
    "binaryInGitHub": False,
    "status": "DESIGN_REFERENCE_APPROVED",
}
EXPECTED_SPRITE_STATUS = "BLOCKED_NOT_YET_CREATED"


def inspect(data):
    errors = []
    canon = data.get("canonical", {})
    for key, expected in EXPECTED.items():
        if canon.get(key) != expected:
            errors.append(f"canonical.{key}: mismatch")
    if data.get("productionSpriteStatus") != EXPECTED_SPRITE_STATUS:
        errors.append("productionSpriteStatus: unexpected promotion")
    if data.get("characterId") != "morwen":
        errors.append("characterId: mismatch")
    if data.get("keepLegacySourceUnchanged") is not True:
        errors.append("keepLegacySourceUnchanged must be true")
    return errors


def main():
    path = Path("data/morwen-design-canonical.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FAIL: cannot read metadata: {exc}")
        return 1
    errors = inspect(data)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    print("PASS: main design-lock metadata matches expected values")
    print("BLOCKED_CANON_BINARY: source bytes not verified by this check")
    print("BLOCKED_NOT_YET_CREATED: no production sprite approval")
    return 0


if __name__ == "__main__":
    sys.exit(main())
