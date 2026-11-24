"""Blueprint Source Adapter: register design/native sources with SHA and provenance.

Registration reads only bytes and safe metadata (no archive extraction, no
script execution). A mismatching expected SHA fails closed.
"""
import hashlib
import json
from pathlib import Path
import struct
import zipfile

from . import present
from .evidence import PROJECTIONS, ROLES

ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _png_meta(path):
    with open(path, "rb") as stream:
        head = stream.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError(f"{path}: not a PNG")
    width, height, depth, color = struct.unpack(">IIBB", head[16:26])
    return dict(format="png", size_px=[width, height], bit_depth=depth,
                has_alpha=color in (4, 6))


def _blend_meta(path):
    with open(path, "rb") as stream:
        head = stream.read(17)
    if head.startswith(ZSTD_MAGIC):
        return dict(format="blend", compression="zstd", header="UNREAD_COMPRESSED")
    if not head.startswith(b"BLENDER"):
        raise ValueError(f"{path}: not a .blend")
    return dict(format="blend", compression="none", header=head.decode("ascii", "replace"))


def _zip_manifest(path):
    with zipfile.ZipFile(path) as archive:
        entries = [dict(name=i.filename, size=i.file_size, crc32=f"{i.CRC:08x}")
                   for i in archive.infolist()]
    if any(e["name"].startswith("/") or ".." in e["name"].split("/") for e in entries):
        raise ValueError(f"{path}: unsafe archive member")
    return entries


def register_source(path, *, source_id, role, projection, coordinate_system, units,
                    provenance, license, expected_sha256=None, scale=None, view=None,
                    notes=None):
    """Return an immutable source record; fail closed on SHA or vocabulary mismatch."""
    path = Path(path)
    if role not in ROLES:
        raise ValueError(f"unknown source role {role!r}")
    if projection not in PROJECTIONS:
        raise ValueError(f"unknown projection {projection!r}")
    for name, value in (("source_id", source_id), ("coordinate_system", coordinate_system),
                        ("units", units), ("provenance", provenance), ("license", license)):
        if not present(value):
            raise ValueError(f"source {source_id!r}: {name} is required (use 'UNKNOWN')")
    sha = file_sha256(path)
    if expected_sha256 is not None and sha != expected_sha256:
        raise ValueError(f"source {source_id}: SHA mismatch {sha} != {expected_sha256}")
    suffix = path.suffix.lower()
    if suffix == ".png":
        meta = _png_meta(path)
    elif suffix == ".blend":
        meta = _blend_meta(path)
    elif suffix in (".vroid", ".vrm", ".zip") and zipfile.is_zipfile(path):
        meta = dict(format=suffix[1:], zip_manifest=_zip_manifest(path),
                    native_measurement="OPAQUE_NO_QUALIFIED_ADAPTER" if suffix == ".vroid" else None)
    elif suffix == ".json":
        json.loads(path.read_text())
        meta = dict(format="json")
    else:
        meta = dict(format=suffix.lstrip(".") or "unknown")
    return dict(source_id=source_id, file=path.name, sha256=sha, bytes=path.stat().st_size,
                role=role, projection=projection, dims=PROJECTIONS[projection],
                coordinate_system=coordinate_system, units=units, scale=scale, view=view,
                provenance=provenance, license=license, notes=notes, **meta)
