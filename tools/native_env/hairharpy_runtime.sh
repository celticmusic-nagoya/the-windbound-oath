#!/usr/bin/env bash
# HairHarpy v2.0.0 qualification on ubuntu-24.04: official assets + SHA (SUMS file and GitHub API digest),
# tag source identity, Linux runtime under Xvfb + Mesa lavapipe Vulkan, GUI start screen, Blender 5.3.0 bridge.
# License: source-available; use permitted, redistribution is not -> binaries stay in /tmp/hh-bin and are never uploaded.
set -euo pipefail
out="${1:?output dir}"
here="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$here/../.." && pwd)"
bin=/tmp/hh-bin
mkdir -p "$out" "$bin"
tag=v2.0.0
tag_commit=9d5eb9ddf6a325ffb89b02ee0c49877e2fca253a
bridge_sha=fd6954293c8258a01a3dc5c2aa107771f3427d0c0037b3c527ee70cac3b7a57a
asset=HairHarpy-2.0.0-linux-x86_64.tar.gz
base="https://github.com/Rackta/HairHarpy/releases/download/$tag"

sudo apt-get update -q >/dev/null
sudo apt-get install -y -q xvfb mesa-vulkan-drivers libvulkan1 libopengl0 libegl1 libfontconfig1 libxkbcommon-x11-0 \
  libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxcb-xinerama0 libxcb-randr0 libxcb-render-util0 \
  libxcb-image0 imagemagick >/dev/null

gh api "repos/Rackta/HairHarpy/releases/tags/$tag" --jq '{tag_name,published_at,assets:[.assets[]|{name,size,digest}]}' > "$out/release_assets.json"
curl -fsSL --retry 2 "$base/SHA256SUMS-linux.txt" -o "$out/SHA256SUMS-linux.txt"
curl -fsSL --retry 2 "$base/$asset" -o "$bin/$asset"
(cd "$bin" && grep " $asset\$" "$out/SHA256SUMS-linux.txt" | sha256sum -c -) | tee "$out/sha_check.txt"
got=$(sha256sum "$bin/$asset" | cut -d' ' -f1)
api=$(python3 -c "import json,sys;a=[x for x in json.load(open('$out/release_assets.json'))['assets'] if x['name']=='$asset'];print((a[0].get('digest') or 'none').removeprefix('sha256:'))")
echo "asset_sha256=$got api_digest=$api" | tee -a "$out/sha_check.txt"
[ "$api" = none ] || [ "$api" = "$got" ]

git clone -q --depth 1 --branch "$tag" https://github.com/Rackta/HairHarpy /tmp/hh-src
[ "$(git -C /tmp/hh-src rev-parse HEAD)" = "$tag_commit" ]
echo "$bridge_sha  /tmp/hh-src/resources/bridge/hmc_bridge_blender.py" | sha256sum -c - | tee -a "$out/sha_check.txt"
# License §2.1: share only by linking to the author repository; record its identity, do not copy it into artifacts.
echo "$(sha256sum /tmp/hh-src/LICENSE.md | cut -d' ' -f1)  https://github.com/Rackta/HairHarpy/blob/$tag_commit/LICENSE.md" > "$out/hairharpy_license_ref.txt"

mkdir -p "$bin/app" && tar -xzf "$bin/$asset" -C "$bin/app"
app="$bin/app/HairHarpy-2.0.0/AppRun"
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json HOME=/tmp/hh-home QT_QPA_PLATFORM=xcb
mkdir -p "$HOME"
set +e
timeout 150 xvfb-run -a -s "-screen 0 1600x1000x24" "$app" --shot "$out/viewport_shot.png" --size 1280x800 > "$out/shot_run.log" 2>&1
shot_exit=$?
Xvfb :91 -screen 0 1600x1000x24 >/dev/null 2>&1 & xv=$!
sleep 2
DISPLAY=:91 "$app" > "$out/gui_run.log" 2>&1 & gp=$!
sleep 12
DISPLAY=:91 import -window root "$out/gui_start_screen.png"
gui_alive=0; kill -0 $gp 2>/dev/null && gui_alive=1
kill $gp $xv 2>/dev/null
set -e
echo "shot_exit=$shot_exit gui_alive_after_12s=$gui_alive" | tee "$out/runtime.txt"

bash "$repo_root/tools/production_qa/install_blender_530.sh" /tmp/b530 > "$out/install_530.txt"
/tmp/b530/blender -b --factory-startup --python-exit-code 3 --python "$here/hairharpy_bridge_probe.py" -- \
  /tmp/hh-src/resources/bridge/hmc_bridge_blender.py "$out/bridge_received_530.blend" "$out/bridge_report.json" > "$out/bridge.log" 2>&1
python3 -m pip install -q --user pillow >/dev/null 2>&1 || true
python3 - "$out" "$shot_exit" "$gui_alive" <<'PY'
import json, sys
from pathlib import Path
from PIL import Image
out = Path(sys.argv[1])
def stat(p):
    im = Image.open(p).convert("L"); h = im.histogram(); n = sum(h)
    mean = sum(i * c for i, c in enumerate(h)) / n
    return {"size": im.size, "luma_mean": round(mean, 2), "luma_sd": round((sum(c * (i - mean) ** 2 for i, c in enumerate(h)) / n) ** .5, 2)}
b = json.loads((out / "bridge_report.json").read_text())
s = {"release": "v2.0.0", "asset_sha_verified": True, "tag_source_verified": True,
     "linux_runtime_shot_exit": int(sys.argv[2]), "viewport_shot": stat(out / "viewport_shot.png"),
     "gui_start_screen": stat(out / "gui_start_screen.png"), "gui_alive_after_12s": sys.argv[3] == "1",
     "bridge_530": b["result"], "bridge_payload": b["payload"],
     "not_run": ["HairHarpy hair authoring on a Morwen reference", "GUI Send from HairHarpy to Blender", "Windows build"],
     "redistribution": "binaries not uploaded (license section 2)"}
s["runtime_result"] = "ISOLATED_PASS" if s["linux_runtime_shot_exit"] == 0 and s["gui_alive_after_12s"] and s["gui_start_screen"]["luma_sd"] > 5 else "FAIL"
(out / "hairharpy_summary.json").write_text(json.dumps(s, indent=1))
print("TWO_HH_SUMMARY", json.dumps(s))
assert s["runtime_result"] == "ISOLATED_PASS" and b["result"] == "PASS"
PY
