#!/usr/bin/env python3
"""Generate a tiny original, noncanonical stone-medallion PNG for an AI3D pipeline test.

Uses only Python stdlib; not a game asset. Reproducible with no random seeds or
external services, files, fonts, reference images, or downloaded textures.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

WIDTH = HEIGHT = 192

def chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return (struct.pack(">I", len(payload)) + body +
            struct.pack(">I", zlib.crc32(body) & 0xffffffff))

def pixel(x: int, y: int) -> bytes:
    dx, dy = x - 96, y - 96
    # Rounded stone medallion with a gently bevelled carved face.
    r = math.hypot(dx / 0.94, dy / 1.05)
    if r >= 77:
        return bytes((0, 0, 0, 0))
    shade = 0.75 + 0.12 * (96 - x) / 96 + 0.1 * (96 - y) / 96
    shade += 0.035 * math.sin(x * 0.21 + y * 0.16)
    if r > 71:
        shade *= max(0.62, 1 - (r - 71) * 0.04)
    if 57 < r < 60:
        shade *= 0.62  # Engraved concentric rim
    # Three lobes around a central knot: wholly algorithmic motif.
    a = math.atan2(dy, dx)
    lobe = 31 + 7 * math.cos(3 * a + 0.5)
    if abs(r - lobe) < 1.45 and r < 49:
        shade *= 0.52
    if r < 8 and abs(dx * dy) < 24:
        shade *= 0.7
    return bytes((min(255, int(181 * shade)), min(255, int(188 * shade)),
                  min(255, int(180 * shade)), 255))

def make_png() -> bytes:
    rows = b"".join(b"\x00" + b"".join(pixel(x, y) for x in range(WIDTH))
                    for y in range(HEIGHT))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(rows, 9)) +
            chunk(b"IEND", b""))

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error("Refusing to overwrite a candidate or QA evidence")
    data = make_png()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(data)
    print("AI3D_SYNTHETIC_CANARY=" + json.dumps({
        "file": str(a.out), "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data), "width": WIDTH, "height": HEIGHT,
        "status": "SYNTHETIC_TEST_ONLY"}))

if __name__ == "__main__":
    main()
