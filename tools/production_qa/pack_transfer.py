"""Pack only verified transfer outputs for the existing private handoff Release.
No network, credentials, publication or native modification.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

SOURCE = "acc7805b6a5b63913bccb7c28e30e1c9e4da6473ed083b5c0673f73cdca9e23a"
VIEWS = ("front", "left4", "left8", "right4")


def require(ok, why):
    if not ok:
        raise ValueError(why)


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), "regular file required: " + path.name)
    require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected), "invalid expected digest")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, "digest mismatch: " + path.name)
    return raw


def pack(root, output, expected_source=SOURCE):
    """The production CLI always uses SOURCE; override only for isolated fixtures."""
    root, output = Path(root), Path(output)
    require(root.is_dir() and not root.is_symlink(), "regular private root required")
    require(root.stat().st_mode & 0o077 == 0, "private root must be owner-only")
    require(output.parent.resolve() == root.resolve(), "output must stay inside private root")
    require(output.suffix == ".zip", "ZIP output required")
    receipt_path = root / "transfer-receipt.json"
    require(receipt_path.is_file() and not receipt_path.is_symlink(), "receipt required")
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    require(receipt.get("scope") == "PRIVATE_TRANSFER_CANDIDATE_REVIEW_REQUIRED", "not a private transfer receipt")
    require(receipt.get("native_sha256") == expected_source, "source binding mismatch")
    require(receipt.get("vrm_structure", {}).get("version") == "1.0", "VRM1.0 required")
    views = root / "views"
    require(views.is_dir() and not views.is_symlink(), "regular views directory required")
    captures = receipt.get("capture_sha256", {})
    require(set(captures) == set(VIEWS) and len(set(captures.values())) == len(VIEWS), "capture inventory mismatch")
    files = {"transfer-receipt.json": receipt_bytes,
             "Morwen-transfer.vrm": checked(root / "Morwen-transfer.vrm", receipt.get("vrm_sha256"))}
    for name in VIEWS:
        files["views/" + name + ".png"] = checked(views / (name + ".png"), captures[name])
    manifest = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
    files["SHA256SUMS.json"] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    with output.open("xb") as handle, zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, raw in files.items():
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o100600 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, raw)
    with zipfile.ZipFile(output) as z:
        require(z.testzip() is None and set(z.namelist()) == set(files), "ZIP readback mismatch")
        for name, raw in files.items():
            require(z.read(name) == raw, "ZIP member readback mismatch: " + name)
    return {"sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "bytes": output.stat().st_size,
            "members": len(files), "scope": "LOCAL_PACKAGE_ONLY_NOT_UPLOADED"}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: pack_transfer.py PRIVATE_ROOT NEW_ZIP")
    print(json.dumps(pack(sys.argv[1], sys.argv[2])))
