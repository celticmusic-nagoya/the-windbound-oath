#!/usr/bin/env python3
"""Verify a director-supplied Morwen master without modifying the input."""
import argparse
import hashlib
from pathlib import Path
import struct
import sys

EXPECTED_SHA = "47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638"
EXPECTED_SIZE = (1536, 1024)


def jpeg_dimensions(data):
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("not a JPEG")
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            raise ValueError("invalid JPEG marker")
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i >= len(data):
            break
        marker = data[i]
        i += 1
        if marker in (0xD9, 0xDA):
            break
        if marker in (0x01,) or 0xD0 <= marker <= 0xD7:
            continue
        if i + 2 > len(data):
            break
        length = struct.unpack_from(">H", data, i)[0]
        if length < 2 or i + length > len(data):
            raise ValueError("invalid JPEG segment length")
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            if length < 7:
                raise ValueError("invalid JPEG frame header")
            height, width = struct.unpack_from(">HH", data, i + 3)
            return width, height
        i += length
    raise ValueError("JPEG dimensions not found")


def verify(data, expected_sha=EXPECTED_SHA, expected_size=EXPECTED_SIZE):
    problems = []
    actual_sha = hashlib.sha256(data).hexdigest()
    if actual_sha != expected_sha:
        problems.append("SHA256_MISMATCH")
    try:
        actual_size = jpeg_dimensions(data)
        if actual_size != expected_size:
            problems.append("DIMENSION_MISMATCH")
    except ValueError:
        problems.append("INVALID_JPEG")
    return problems


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Director original file; read only")
    args = parser.parse_args()
    try:
        data = args.source.read_bytes()
    except OSError as exc:
        print(f"BLOCKED_SOURCE_UNAVAILABLE: {exc}")
        return 2
    issues = verify(data)
    if issues:
        print("FAIL: " + ", ".join(issues))
        return 1
    print("PASS: original JPEG bytes, SHA256 and dimensions verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
