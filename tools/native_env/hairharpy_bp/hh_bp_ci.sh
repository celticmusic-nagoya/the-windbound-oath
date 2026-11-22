#!/usr/bin/env bash
# CI wrapper: HairHarpy x blueprint x #468 session (run1 | run2). No HairHarpy binaries are uploaded.
set -euo pipefail
mode="${1:?run1|run2}"; out="${2:?output dir}"
here="$(cd "$(dirname "$0")" && pwd)"; repo="$(cd "$here/../../.." && pwd)"
mkdir -p "$out" /tmp/hh-bin
asset=HairHarpy-2.0.0-linux-x86_64.tar.gz
asset_sha=f8e6f398a2faa2e252e01d6e201c2aa8737fff456bfedabebe13be63e7ca2b3c
sudo apt-get update -q >/dev/null
sudo apt-get install -y -q xvfb fonts-inter mesa-vulkan-drivers libvulkan1 libopengl0 libegl1 libgl1-mesa-dri libglx-mesa0 \
  libgles2 libfontconfig1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxcb-xinerama0 \
  libxcb-randr0 libxcb-render-util0 libxcb-image0 >/dev/null
curl -fsSL --retry 2 "https://github.com/Rackta/HairHarpy/releases/download/v2.0.0/$asset" -o "/tmp/hh-bin/$asset"
echo "$asset_sha  /tmp/hh-bin/$asset" | sha256sum -c -
mkdir -p /tmp/hh-bin/app && tar -xzf "/tmp/hh-bin/$asset" -C /tmp/hh-bin/app
bash "$repo/tools/production_qa/install_blender_530.sh" /tmp/b530 > "$out/install_530.txt"
mkdir -p /tmp/hh-fc
cat > /tmp/hh-fc/fonts.conf <<'FC'
<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include>
<alias binding="strong"><family>Segoe UI</family><prefer><family>Inter</family></prefer></alias></fontconfig>
FC
export FONTCONFIG_FILE=/tmp/hh-fc/fonts.conf
Xvfb :91 -screen 0 1600x1000x24 >/dev/null 2>&1 &
sleep 2
args=(--engine "$repo/engine468/tools/production_qa" --blueprint "$here/qual_hair_blueprint_v1.json" --blender /tmp/b530/blender
      --display :91 --hh-sha "$asset_sha" --blender-version 5.3.0)
if [ "$mode" = v2 ]; then
  /tmp/b530/blender -b --factory-startup --python "$here/mk_qual_head.py" -- /tmp/qual_head.obj > /dev/null 2>&1
  python3 "$here/hh_volume_session.py" --root "$out/session/root" --head /tmp/qual_head.obj --engine "$repo/engine468v/tools/production_qa" \
    --blueprint "$here/qual_hair_blueprint_v2.json" --blender /tmp/b530/blender --display :91 --hh-sha "$asset_sha" --blender-version 5.3.0
elif [ "$mode" = run1 ]; then
  /tmp/b530/blender -b --factory-startup --python "$here/mk_qual_head.py" -- /tmp/qual_head.obj > /dev/null 2>&1
  python3 "$here/hh_session.py" --root "$out/session/root" --mode run1 --head /tmp/qual_head.obj "${args[@]}"
else
  python3 "$repo/tools/native_env/fetch_restore_tar.py" "$here/hh_bp_restore_request.json" "$out/restore"
  mkdir -p "$out/session" && tar -xzf "$out/restore/session.tgz" -C "$out/session"
  python3 "$here/hh_session.py" --root "$out/session/root" --mode run2 "${args[@]}"
fi
tar -czf "$out/session.tgz" -C "$out/session" root
sha256sum "$out/session.tgz" > "$out/session.tgz.sha256"
mkdir -p "$out/evidence"
cp "$out"/session/hh_session_summary_*.json "$out"/session/hhv_session_summary.json "$out/evidence/" 2>/dev/null || true
cp "$out"/session/root/ckpt/*.json "$out/evidence/" 2>/dev/null || true
cp "$out/restore/restore_provenance.json" "$out/evidence/" 2>/dev/null || true
for d in "$out"/session/root/factory-*/; do
  [ -d "$d/renders" ] && cp -r "$d/renders" "$out/evidence/renders_$(basename "$d")" || true
  for f in finish.json adapter_history.json hh_uv_session.log; do [ -f "$d/$f" ] && cp "$d/$f" "$out/evidence/$(basename "$d")_$f" || true; done
  for s in "$d"/w*_reopen/shot.png; do [ -f "$s" ] && cp "$s" "$out/evidence/$(basename "$d")_hairharpy_reopen_viewport.png" || true; done
done
[ -d "$out/session/root/ckpt/hq" ] && cp -r "$out/session/root/ckpt/hq" "$out/evidence/hq" || true
rm -rf "$out/session/root"
