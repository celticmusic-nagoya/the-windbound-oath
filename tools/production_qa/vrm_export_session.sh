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
import zipfile
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


METADATA_FIELDS = (
    ("name", 451, (267, 429, 743, 473)),
    ("version", 545, (267, 523, 743, 567)),
    ("creator", 639, (267, 617, 743, 663)),
)
DIALOG_BOX = (250, 65, 760, 675)
EDITOR_TITLE = "VRoid Studio 2.16.0 - Morwen-resume.vroid"


def dialog_flags(image, text):
    anchors = ("VRM Settings", "Avatar Name", "Version", "Creators")
    return (image.size == (1024, 768), EDITOR_TITLE in text,
            tuple(a.casefold() in text.casefold() for a in anchors))


def field_matches(ocr, value):
    return ocr.strip() == value


def write_diagnostic(private_dir, field, phase, flags, dialog, dialog_ocr, crop, field_ocr):
    path = private_dir / "Morwen-metadata-diagnostic.zip"
    with path.open("xb") as output, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("diagnostic.json", json.dumps(dict(field=field, phase=phase,
                         dimensions=flags[0], title=flags[1], anchors=flags[2],
                         source_sha256=SOURCE)))
        archive.writestr("dialog.png", dialog.read_bytes())
        archive.writestr("dialog.txt", dialog_ocr)
        if crop is not None:
            archive.writestr("field.png", crop.read_bytes())
            archive.writestr("field.txt", field_ocr)
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as env:
        env.write("MORWEN_METADATA_DIAGNOSTICS=true\n")


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
    def ocr(path):
        return subprocess.check_output([gui, "ocr", str(path)], text=True)
    def diagnostic_ocr(path):
        try:
            return ocr(path)
        except subprocess.CalledProcessError:
            return ""
    def observe(name, read_ocr=ocr):
        path = out / (name + ".png")
        send("screenshot", path)
        text = read_ocr(path)
        path.with_suffix(".txt").write_text(text)
        with Image.open(path) as im:
            im = im.convert("RGB")
        return path, text, im
    def shot(name, *anchors):
        path, text, im = observe(name)
        state_ok(im, text, anchors)
        return path, text, im
    def metadata_state(text, im):
        # Never log raw private OCR or click through an unknown modal.
        anchors = ("VRM Settings", "Export Format", "VRM1.0", "Avatar Name", "Creators")
        title = "VRoid Studio 2.16.0 - Morwen-resume.vroid" in text
        present = [a.casefold() in text.casefold() for a in anchors]
        options = (all(a in text for a in ("Export as VRM", "Export Info", "Reduce Polygons", "Reduce Materials", "Reduce Bones"))
                   and [s.strip() for s in text.split("|")].count("Export") == 1)
        qualified = title and im.size == (1024, 768)
        if qualified and all(present):
            return "METADATA", present
        if qualified and not any(present) and options and all(blue(im,x,250) for x in (780,820,930,970)):
            return "OPTIONS_STILL_VISIBLE", present
        return "UNRECOGNIZED", present
    def await_metadata():
        # The first run stopped after the options click. Observe before deciding
        # whether a different, historically verified button locator is safe.
        for phase in range(2):
            states = []
            for attempt in range(5):
                time.sleep(3)
                _, text, im = observe(f"vrm-metadata-{phase}-{attempt}")
                state, present = metadata_state(text, im)
                states.append(state)
                print("VRM_METADATA_OBSERVATION", phase, attempt, state,
                      "anchors", "".join("1" if v else "0" for v in present), flush=True)
                if state == "METADATA":
                    return im
            if phase == 0 and states == ["OPTIONS_STILL_VISIBLE"] * 5:
                source_ok()
                # Historical 1024x768 options screen: blue button x743..1008 y236..264.
                # Four blue samples + unique exact OCR label + no metadata anchors required.
                click(876, 250)
            else:
                break
        raise SystemExit("VRM_METADATA_NOT_VERIFIED_NO_FURTHER_INPUT")
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
    im = await_metadata()
    require(blue(im, 286, 189), "VRM1.0 selection not verified")
    values = dict(name=meta["name"], version=meta["version"], creator=meta["authors"][0])
    dialog = out / "metadata-dialog.png"
    im.crop(DIALOG_BOX).save(dialog)
    for field, y, region in METADATA_FIELDS:
        for phase in ("before", "after"):
            if phase == "after":
                click(500, y)
                send("key", 0, "cmd")
                send("text", values[field])
                # Blur on the non-interactive Avatar Information heading.
                click(320, 273)
                time.sleep(0.7)
            _, text, im = observe(f"metadata-{field}-{phase}", diagnostic_ocr)
            flags = dialog_flags(im, text)
            ready = flags[0] and flags[1] and all(flags[2]) and blue(im, 286, 189)
            crop = None
            field_ocr = ""
            matched = False
            if ready:
                im.crop(DIALOG_BOX).save(dialog)
                crop = out / f"metadata-{field}-{phase}-roi.png"
                im.crop(region).save(crop)
                if phase == "after":
                    field_ocr = diagnostic_ocr(crop)
                matched = phase == "before" or field_matches(field_ocr, values[field])
            print("VRM_METADATA_FIELD", field, phase, "dimensions", int(flags[0]),
                  "title", int(flags[1]), "anchors", "".join(str(int(v)) for v in flags[2]),
                  "match", int(matched), flush=True)
            if not matched:
                if dialog.is_file():
                    write_diagnostic(private_dir, field, phase, flags, dialog,
                                     diagnostic_ocr(dialog), crop, field_ocr)
                raise SystemExit(f"VRM_METADATA_FIELD_{field.upper()}_{phase.upper()}_BLOCKED")
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
