#!/usr/bin/env bash
# Historical successful sequence: run 44733016182 / commit 71e7c4f.
# Caller still must supply reviewed run-bound authority and private transport.
set -euo pipefail
umask 077
gui=$1
native=$2
out=$3
private_dir=$4
profile=$5
expected=acc7805b6a5b63913bccb7c28e30e1c9e4da6473ed083b5c0673f73cdca9e23a
scripts=$(cd -- "$(dirname -- "$0")" && pwd)
test -d "$private_dir" && test ! -L "$private_dir"
test ! -e "$private_dir/Morwen-transfer.vrm"
test ! -e "$private_dir/transfer-receipt.json"
test -f "$profile"
bash "$scripts/capture_transfer_views.sh" "$gui" "$native" "$out"
"${MORWEN_TRANSFER_PYTHON:-python3}" - "$gui" "$native" "$out" "$profile" "$private_dir" "$scripts" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from PIL import Image

SOURCE = "acc7805b6a5b63913bccb7c28e30e1c9e4da6473ed083b5c0673f73cdca9e23a"
REQUIRED_PRIVATE = {"avatarPermission": "onlyAuthor", "commercialUsage": "personalNonProfit",
                    "allowRedistribution": False, "modification": "allowModification",
                    "creditNotation": "required", "allowExcessivelyViolentUsage": False,
                    "allowExcessivelySexualUsage": False, "allowPoliticalOrReligiousUsage": False,
                    "allowAntisocialOrHateUsage": False}


def require(ok, why):
    if not ok:
        raise SystemExit(why)


def profile_metadata(profile):
    require(profile.get("app_version") == "2.16.0" and profile.get("source_sha256") == SOURCE
            and profile.get("license_review_ref") and profile.get("sequence") == "M01-44733016182-v1",
            "reviewed source-bound export profile required")
    meta = profile.get("expected_meta", {})
    for key, value in REQUIRED_PRIVATE.items():
        require(type(meta.get(key)) is type(value) and meta[key] == value, "private permission profile mismatch: " + key)
    require(re.fullmatch(r"Morwen-transfer-[A-Za-z0-9-]{1,48}", meta.get("name", "")) is not None,
            "unique reviewed transfer name required")
    require(re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,2}", meta.get("version", "")) is not None,
            "reviewed version required")
    authors = meta.get("authors", [])
    require(isinstance(authors, list) and len(authors) == 1 and isinstance(authors[0], str)
            and re.fullmatch(r"[A-Za-z0-9_. -]{1,64}", authors[0]) is not None,
            "one reviewed author required")
    return meta


def blue(image, x, y):
    r, g, b = image.getpixel((x, y))[:3]
    return r < 50 and 100 <= g <= 210 and b > 220


def state_ok(image, text, anchors):
    require(image.size == (1024, 768), "unqualified display dimensions")
    require("VRoid Studio 2.16.0 - Morwen-resume.vroid" in text,
            "source editor title not verified")
    require(all(anchor.casefold() in text.casefold() for anchor in anchors), "unexpected dialog state")


def main():
    gui, native, out, profile_path, private_dir, scripts = sys.argv[1:]
    native, out, private_dir = map(Path, (native, out, private_dir))
    profile = json.loads(Path(profile_path).read_bytes())
    meta = profile_metadata(profile)
    sys.path.insert(0, scripts)
    from verify_transfer_output import verify
    require(not private_dir.is_symlink() and private_dir.stat().st_mode & 0o077 == 0,
            "private run directory must be owner-only")
    docs = Path.home() / "Documents"
    require(docs.is_dir() and not docs.is_symlink(), "unqualified Documents directory")
    staged = docs / (meta["name"] + ".vrm")
    target = private_dir / "Morwen-transfer.vrm"
    receipt = private_dir / "transfer-receipt.json"
    require(not os.path.lexists(staged) and not os.path.lexists(target) and not os.path.lexists(receipt),
            "refuse to replace any existing output")
    def source_ok():
        require(native.is_file() and not native.is_symlink() and hashlib.sha256(native.read_bytes()).hexdigest() == SOURCE,
                "native source changed")
    def send(*args):
        subprocess.run([gui, *map(str, args)], check=True)
    def click(x, y):
        send("click", x / 1024, y / 768)
    def shot(name, *anchors):
        path = out / (name + ".png")
        send("screenshot", path)
        text = subprocess.check_output([gui, "ocr", str(path)], text=True)
        path.with_suffix(".txt").write_text(text)
        with Image.open(path) as im:
            im = im.convert("RGB")
        state_ok(im, text, anchors)
        return path, text, im
    source_ok()
    _, _, im = shot("export-editor", "Face", "Hairstyle", "Body", "Outfit")
    click(927, 77)
    time.sleep(5)
    p, _, _ = shot("export-menu", "Export as VRM", "Upload to VRoid Hub")
    send("click-label", p, "Export as VRM", "Export as VRM")
    time.sleep(10)
    p, t, _ = shot("vrm-options", "Export as VRM", "Export Info", "Reduce Polygons", "Reduce Materials", "Reduce Bones")
    require("VRM Settings" not in t and [s.strip() for s in t.split("|")].count("Export") == 1,
            "options Export is not unique")
    send("click-label", p, "Export", "Export Info")
    time.sleep(8)
    _, _, im = shot("vrm-metadata", "VRM Settings", "Export Format", "VRM1.0", "Avatar Name", "Creators")
    require(blue(im, 286, 189), "VRM1.0 selection not verified")
    for y, value in ((451, meta["name"]), (545, meta["version"]), (639, meta["authors"][0])):
        click(500, y)
        send("key", 0, "cmd")
        send("text", value)
        time.sleep(0.4)
    _, _, _ = shot("vrm-metadata-filled", "VRM Settings", meta["name"], meta["version"], meta["authors"][0])
    for _ in range(12):
        send("scroll", 650 / 1024, 650 / 768, -12, 0)
        time.sleep(0.15)
    time.sleep(2)
    p, _, _ = shot("vrm-metadata-bottom", "VRM Settings", "Redistribution", "Alterations allowed", "Attribution")
    send("click-label", p, "Alterations allowed", "Redistribution")
    time.sleep(2)
    _, _, im = shot("vrm-permissions", "VRM Settings", "Redistribution", "Alterations allowed", "Attribution", "Export", "Back")
    require(all(blue(im, x, y) for x, y in ((275, 148), (275, 290), (275, 395), (400, 594))),
            "private permission selections or foreground Export not verified")
    source_ok()
    click(505, 594)
    time.sleep(8)
    p, t, _ = shot("vrm-native-save", "Save As:", "Where:", meta["name"], "Documents", "Cancel", "Save")
    require("Replace" not in t and not os.path.lexists(staged), "unexpected overwrite dialog or existing file")
    send("click-label", p, "Save", "Save As:")
    for _ in range(30):
        if staged.is_file() and not staged.is_symlink() and staged.stat().st_size > 0:
            break
        time.sleep(2)
    require(staged.is_file() and not staged.is_symlink(), "expected new VRM missing")
    source_ok()
    (out / "native-after-export.txt").write_text(SOURCE + "\n")
    result = verify(out, staged, native, profile)
    actual = result["vrm_structure"]
    require(actual["version"] == "1.0" and all(type(actual["meta"].get(k)) is type(v) and actual["meta"][k] == v for k, v in meta.items()),
            "exported VRM metadata differs from reviewed profile")
    data = staged.read_bytes()
    require(hashlib.sha256(data).hexdigest() == result["vrm_sha256"], "staged bytes changed")
    with target.open("xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    require(hashlib.sha256(target.read_bytes()).hexdigest() == result["vrm_sha256"], "private copy mismatch")
    source_ok()
    with receipt.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
PY
