#!/usr/bin/env bash
# Isolated, official SHA256-verified Blender 5.3.0 installer; never touches 5.2.4.
set -euo pipefail
destination="${1:-/tmp/two-blender-530/app}"
mode="${2:-verify-runtime}"
case "$mode" in
  verify-runtime|extract-only) ;;
  *) echo "Unknown Blender install mode" >&2; exit 2 ;;
esac
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
base=https://mirror.blender.org/release/Blender5.3
name=blender-5.3.0-linux-x64.tar.xz
curl --fail --location --retry 1 --connect-timeout 20 --max-time 120 "$base/blender-5.3.0.sha256" -o "$work/checksums"
python3 - "$work/checksums" "$work/expected.sha256" "$name" <<'PY'
import re,sys
from pathlib import Path
rows=Path(sys.argv[1]).read_text().splitlines()
matches=[]
for row in rows:
 if sys.argv[3] in row:
  h=re.findall(r'(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])',row)
  if len(h)!=1: raise SystemExit("INVALID_OFFICIAL_CHECKSUM_ROW")
  matches.append(h[0].lower())
if len(matches)!=1: raise SystemExit("OFFICIAL_CHECKSUM_NOT_UNIQUE")
Path(sys.argv[2]).write_text(matches[0]+"  "+sys.argv[3]+chr(10))
PY
if [[ -n "${TWO_BLENDER_ARCHIVE_SHA256:-}" ]]; then
    read -r official_sha _ < "$work/expected.sha256"
    test "$official_sha" = "$TWO_BLENDER_ARCHIVE_SHA256"
fi
curl --fail --location --retry 1 --connect-timeout 20 --max-time 600 "$base/$name" -o "$work/$name"
(cd "$work" && sha256sum -c expected.sha256)
mkdir -p "$destination"
tar -xJf "$work/$name" -C "$destination" --strip-components=1
if [[ "$mode" == verify-runtime ]]; then
    "$destination/blender" -b --factory-startup --python-exit-code 1 --python-expr 'import bpy; assert tuple(bpy.app.version)==(5,3,0); print("TWO_BLENDER_530_RUNTIME_PASS")'
fi
echo "TWO_BLENDER_530_PATH=$destination/blender"
