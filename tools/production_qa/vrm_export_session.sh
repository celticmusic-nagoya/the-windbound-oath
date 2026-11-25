#!/usr/bin/env bash
# Uses the approved editor session and existing macos_gui binary.
set -euo pipefail
gui=$1
native=$2
out=$3
private_dir=$4
profile=$5
expected=acc7805b6a5b63913bccb7c28e30e1c9e4da6473ed083b5c0673f73cdca9e23a
scripts=$(cd -- "$(dirname -- "$0")" && pwd)
test -d "$private_dir" && test ! -L "$private_dir"
test ! -e "$private_dir/Morwen-transfer.vrm"
test -f "$profile"
bash "$scripts/capture_transfer_views.sh" "$gui" "$native" "$out"

# F8 is the documented VRoid macOS export shortcut. Subsequent gestures are
# only allowed from the exact, independently reviewed dialog profile.
"$gui" key 100
sleep 3
"$gui" screenshot "$out/export-open.png"
"$gui" ocr "$out/export-open.png" > "$out/export-open.txt"
grep -Eiq 'Export|VRM' "$out/export-open.txt"
python3 - "$gui" "$out" "$profile" "$private_dir" <<'PY'
import json
from pathlib import Path
import subprocess
import sys
import time

gui, directory, profile, private_dir = sys.argv[1:]
directory = Path(directory)
profile = json.loads(Path(profile).read_bytes())
if profile["app_version"] != "2.16.0" or not profile["license_review_ref"]:
    raise SystemExit("Required approved export metadata missing")
allowed = {"Export", "Export VRM", "VRM1.0", "Save"}
steps = profile["steps"]
if not 1 <= len(steps) <= 12 or steps[-1]["label"] != "Save":
    raise SystemExit("Invalid reviewed export profile")
for number, step in enumerate(steps, 1):
    label, anchor = step["label"], step["anchor"]
    if label not in allowed or not anchor:
        raise SystemExit("Unqualified export control")
    shot = directory / f"export-state-{number}.png"
    subprocess.run([gui, "screenshot", str(shot)], check=True)
    ocr = subprocess.check_output([gui, "ocr", str(shot)], text=True)
    shot.with_suffix(".txt").write_text(ocr)
    labels = [part.strip() for part in ocr.split("|")]
    if labels.count(label) != 1 or not any(anchor in part for part in labels):
        raise SystemExit("Export dialog differs from the reviewed profile")
    if label == "Save":
        # Never accept an unverified folder, name, or replacement prompt.
        if not all(value in ocr for value in ("Morwen-transfer", Path(private_dir).name)):
            raise SystemExit("Expected private destination or filename not visible")
    subprocess.run([gui, "click-label", str(shot), label, anchor], check=True)
    time.sleep(3)
PY
for i in $(seq 1 15); do
  test -s "$private_dir/Morwen-transfer.vrm" && break
  sleep 2
done
test -s "$private_dir/Morwen-transfer.vrm"
test "$(shasum -a 256 "$native" | cut -d ' ' -f 1)" = "$expected"
printf '%s\n' "$expected" > "$out/native-after-export.txt"
"${MORWEN_TRANSFER_PYTHON:-python3}" "$scripts/verify_transfer_output.py" "$out" "$private_dir/Morwen-transfer.vrm" \
  "$native" "$profile" "$private_dir/transfer-receipt.json"
