"""Reproducible, read-only Blender binary integrity audit. Requires stdlib + zstd CLI.
Usage: python audit_blend_container.py path/to/source.blend [expected_sha256]
Checks Zstandard stream, Blender header, BHead framing, and ENDB terminator.
This does NOT validate mesh topology or artistic quality.
"""
import collections
import hashlib
import json
import pathlib
import shutil
import struct
import subprocess
import sys

def audit(path, expected=None):
    path = pathlib.Path(path)
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if expected and sha != expected:
        raise ValueError(f"source SHA mismatch: {sha}")
    if raw.startswith(b"\\x28\\xb5\\x2f\\xfd"):
        if not shutil.which("zstd"):
            raise RuntimeError("zstd executable required to inspect compressed .blend")
        blob = subprocess.run(["zstd", "-dc", str(path)], check=True, capture_output=True).stdout
    else:
        blob = raw
    if len(blob) < 12 or not blob.startswith(b"BLENDER"):
        raise ValueError("invalid Blender header")
    pointer = blob[7:8]
    endian = blob[8:9]
    if pointer not in (b"-", b"_") or endian not in (b"v", b"V"):
        raise ValueError("unsupported Blender pointer/endian flags")
    ptr64 = pointer == b"-"
    fmt = ("<" if endian == b"v" else ">") + ("4sIQII" if ptr64 else "4sIIII")
    hsize = struct.calcsize(fmt)
    offset = 12
    codes = collections.Counter()
    end_seen = False
    while offset < len(blob):
        if offset + hsize > len(blob):
            raise ValueError("truncated BHead")
        code, length, _old, _sdna, _count = struct.unpack_from(fmt, blob, offset)
        if offset + hsize + length > len(blob):
            raise ValueError("BHead payload overflow")
        codes[code.rstrip(b"\\0").decode("ascii", errors="replace")] += 1
        offset += hsize + length
        if code == b"ENDB":
            end_seen = True
            break
    if not end_seen or offset != len(blob):
        raise ValueError("missing ENDB or trailing unexpected data")
    return {"source_sha256": sha, "source_bytes": len(raw),
            "blender_header": blob[:12].decode("ascii"),
            "decompressed_bytes": len(blob), "bhead_blocks": sum(codes.values()),
            "datablock_code_counts": dict(sorted(codes.items())),
            "container_integrity": "PASS",
            "mesh_topology_qa": "NOT_RUN", "art_qa": "NOT_RUN"}

if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit("Usage: audit_blend_container.py source.blend [expected_sha256]")
    print(json.dumps(audit(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None), indent=2))
