#!/usr/bin/env bash
# Shared Blender 5.3.0 CI installer for character and map teams.
# Usage: bash tools/production_qa/install_blender_524.sh [installation-directory]
# Never changes system packages; verifies upstream SHA before extraction.
set -euo pipefail
destination="${1:-/tmp/two-blender/app}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
base=https://mirror.blender.org/release/Blender5.3
name=blender-5.3.0-linux-x64.tar.xz
curl --fail --location --retry 0 --connect-timeout 20 --max-time 90 "$base/blender-5.3.0.sha256" -o "$work/checksums"
python3 - "$work/checksums" "$work/expected.sha256" "$name" <<'PY'
import re, sys
from pathlib import Path
rows = Path(sys.argv[1]).read_text().splitlines()
target = sys.argv[3]
matches = []
for row in rows:
    if target in row:
        hashes = re.findall(r'(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])', row)
        if len(hashes) != 1:
            raise SystemExit('Invalid official checksum row')
        matches.append(hashes[0].lower())
if len(matches) != 1:
    raise SystemExit('Expected exactly one official checksum')
Path(sys.argv[2]).write_text(f'{matches[0]}  {target}\n')
PY
curl --fail --location --retry 0 --connect-timeout 20 --max-time 540 "$base/$name" -o "$work/$name"
(cd "$work" && sha256sum -c expected.sha256)
mkdir -p "$destination"
tar -xJf "$work/$name" -C "$destination" --strip-components=1
"$destination/blender" -b --factory-startup --python-exit-code 1 --python-expr 'import bpy; assert tuple(bpy.app.version)==(5,3,0); print("TWO_BLENDER_530_RUNTIME_PASS")'
sha256sum "$work/$name"
echo "TWO_BLENDER_530_PATH=$destination/blender"
