#!/usr/bin/env bash
# Run with reviewed private input and a private output directory.
set -euo pipefail
umask 077
source_file=$1
vrm_sha=$2
target=$3
scripts=$(cd -- "$(dirname -- "$0")" && pwd)
test -f "$source_file" && test ! -L "$source_file"
[[ "$vrm_sha" =~ ^[0-9a-f]{64}$ ]]
printf '%s  %s\n' "$vrm_sha" "$source_file" | sha256sum -c
mkdir -m 700 "$target"
target=$(cd "$target" && pwd)
work=$(mktemp -d)
export BLENDER_USER_CONFIG="$work/config" BLENDER_USER_SCRIPTS="$work/scripts"
bash "$scripts/install_blender_530.sh" "$work/blender"
addon="$work/vrm-extension.zip"
curl -fsSL --retry 1 --max-time 120 \
  https://github.com/saturday06/VRM-Addon-for-Blender/releases/download/v4.10.5/VRM_Addon_for_Blender-Extension-4_10_5.zip \
  -o "$addon"
printf '%s  %s\n' 5f0dd6a277f33961cc453ca401d36ae99272f6bcd06994e8c375d2b922b44bf1 "$addon" | sha256sum -c
"$work/blender/blender" --command extension install-file -r user_default -e "$addon"
"$work/blender/blender" -b --python-exit-code 1 --python "$scripts/import_vrm_transfer.py" -- \
  "$source_file" "$vrm_sha" "$target/Morwen-transfer.blend" "$target/transfer-receipt.json"
"$work/blender/blender" -b "$target/Morwen-transfer.blend" --python-exit-code 1 \
  --python "$scripts/render_transfer_views.py" -- "$target/views"
