#!/usr/bin/env bash
# HairHarpy v2.0.0 real authoring -> GUI Send -> Blender 5.3.0 save -> reopen -> shape/UV/material QA.
# Authoring: HairHarpy Crown tool (+continuation) on a neutral qualification head (NOT a Morwen candidate), Convert,
# GUI Bridge "Send now" and GUI Export, all through gui_locate.py (OCR label locator + postconditions, Xvfb).
# UV: HairHarpy Topology room unfold/pack (app's own command script), OBJ+FBX export.
# HairHarpy binaries stay in /tmp/hh-bin and are never uploaded (license section 2). No paid services.
set -euo pipefail
out="${1:?output dir}"
here="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$here/../.." && pwd)"
bin=/tmp/hh-bin; mkdir -p "$out/shots" "$bin"
asset=HairHarpy-2.0.0-linux-x86_64.tar.gz
asset_sha=f8e6f398a2faa2e252e01d6e201c2aa8737fff456bfedabebe13be63e7ca2b3c   # verified in run 45039748645
bridge_sha=fd6954293c8258a01a3dc5c2aa107771f3427d0c0037b3c527ee70cac3b7a57a
B=${BLENDER530:-/tmp/b530/blender}
if [ "${SKIP_SETUP:-0}" != 1 ]; then
  sudo apt-get update -q >/dev/null
  sudo apt-get install -y -q xvfb xdotool imagemagick tesseract-ocr mesa-vulkan-drivers libvulkan1 libopengl0 libegl1 \
    libgl1-mesa-dri libglx-mesa0 libgles2 libfontconfig1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 \
    libxcb-shape0 libxcb-xinerama0 libxcb-randr0 libxcb-render-util0 libxcb-image0 >/dev/null
  curl -fsSL --retry 2 "https://github.com/Rackta/HairHarpy/releases/download/v2.0.0/$asset" -o "$bin/$asset"
  git clone -q --depth 1 --branch v2.0.0 https://github.com/Rackta/HairHarpy /tmp/hh-src
  bash "$repo_root/tools/production_qa/install_blender_530.sh" /tmp/b530 > "$out/install_530.txt"
fi
echo "$asset_sha  $bin/$asset" | sha256sum -c - > "$out/sha_check.txt"
echo "$bridge_sha  /tmp/hh-src/resources/bridge/hmc_bridge_blender.py" | sha256sum -c - >> "$out/sha_check.txt"
rm -rf "$bin/app"; mkdir -p "$bin/app"; tar -xzf "$bin/$asset" -C "$bin/app"
app="$bin/app/HairHarpy-2.0.0/AppRun"
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json QT_QPA_PLATFORM=xcb

# neutral qualification head (ellipsoid, metres, Y-up OBJ)
cat > /tmp/hh_mkhead.py <<'PY'
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.1)
h = bpy.context.active_object; h.name = "QUAL_head_neutral"; h.scale = (0.82, 0.95, 1.18)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.wm.obj_export(filepath=sys.argv[-1], export_selected_objects=True, forward_axis='NEGATIVE_Z', up_axis='Y', export_materials=False)
PY
"$B" -b --factory-startup --python /tmp/hh_mkhead.py -- "$out/qual_head.obj" > /dev/null 2>&1

# Blender 5.3.0 receiver (real add-on code, real HTTP) waits for the GUI Send
"$B" -b --factory-startup --python-exit-code 3 --python "$here/hairharpy_bridge_receiver.py" -- \
  /tmp/hh-src/resources/bridge/hmc_bridge_blender.py "$out/received_530.blend" "$out/receiver.json" 600 > "$out/receiver.log" 2>&1 &
rcv=$!
D=:91
Xvfb $D -screen 0 1600x1000x24 >/dev/null 2>&1 & xv=$!
sleep 2
HOME=/tmp/hh-home1 DISPLAY=$D "$app" --shot "$out/shots/session1_viewport_end.png" --size 1500x810 \
  --events "room hair;importhead $out/qual_head.obj;wait 1500;winshot $out/shots/session1_head.png;wait 420000" > "$out/session1.log" 2>&1 &
hh=$!
sleep 10
G="python3 $here/gui_locate.py"
C="--display $D --ledger $out/gui_steps.jsonl --shots $out/shots"
RP=1248,290,1500,740   # right panel
$G click $C --name 01_crown_tool --at 1388,157 --expect "Create" --expect-region $RP
$G step  $C --name 02_continuation --label "With a continuation" --region $RP
$G step  $C --name 03_create --label "Create" --region $RP --expect "continuation" --expect-region 212,50,520,740
$G step  $C --name 04_select_crown --label "Crown 1" --region 0,150,212,320 --expect "Vertical loops" --expect-region $RP
$G step  $C --name 05_convert --label "Convert" --line-exact --region 1248,520,1500,740 --scroll-at 1370,650 \
           --expect "Crown 1 mesh" --expect-region 0,50,212,320
$G step  $C --name 06_select_mesh --label "Crown 1 mesh" --region 0,50,212,320 --expect "Vertices" --expect-region $RP
$G step  $C --name 07_bridge --label "Bridge" --region 340,0,440,28 --expect "Program" --expect-region 350,28,740,280
$G step  $C --name 08_program --label "choose" --region 420,30,740,60 --expect "Blender (live)" --expect-region 420,30,740,140
$G step  $C --name 09_blender_live --label "Blender (live)" --region 420,55,740,140 --expect "Send now" --expect-region 350,28,740,280
$G step  $C --name 10_send --label "Send now" --region 350,240,740,280 --expect "sent 1" --expect-region 350,170,740,200 --timeout 40
DISPLAY=$D xdotool key Escape
$G step  $C --name 11_export --label "Export" --region 280,0,350,28 --expect "Format" --expect-region 540,290,1060,720
$G step  $C --name 12_path --label "Path" --region 540,295,600,325 --offset 200,0 --type "$out/hh_gui_crown.obj"
$G step  $C --name 13_export_go --label "Export" --region 980,670,1060,705 --expect-file "$out/hh_gui_crown.obj"
wait $rcv || true
kill $hh 2>/dev/null || true; sleep 1
DISPLAY=$D import -window root "$out/shots/session1_final_screen.png" || true

# HairHarpy Topology room: UV unfold/pack of the GUI-exported crown, OBJ/FBX export, native project save
HOME=/tmp/hh-home2 DISPLAY=$D timeout 180 "$app" --shot "$out/shots/session2_uv_viewport.png" --size 1500x810 \
  --events "room topo;import $out/hh_gui_crown.obj;wait 400;tree;select 3;uv open;wait 300;uv angle 50;uv unfoldall;uv packall;uv checks;exportf obj $out/hh_crown_uv.obj;exportf fbx $out/hh_crown_uv.fbx;save $out/hh_topology_uv.hairmesh" \
  > "$out/session2.log" 2>&1 || true
kill $xv 2>/dev/null || true

# Blender 5.3.0 QA, then independent reopen in a new process
"$B" -b "$out/received_530.blend" --factory-startup --python-exit-code 3 --python "$here/hairharpy_roundtrip_qa.py" -- \
  qa "$out/hh_crown_uv.obj" "$out/hh_crown_uv.fbx" "$out/hh_roundtrip_530.blend" "$out/roundtrip.json" "$out/renders" > "$out/roundtrip.log" 2>&1
"$B" -b "$out/hh_roundtrip_530.blend" --factory-startup --python-exit-code 3 --python "$here/hairharpy_roundtrip_qa.py" -- \
  measure "$out/reopen.json" > "$out/reopen.log" 2>&1
python3 - "$out" <<'PY'
import json, sys, hashlib
from pathlib import Path
o = Path(sys.argv[1])
r, m, rc = (json.loads((o / n).read_text()) for n in ("roundtrip.json", "reopen.json", "receiver.json"))
a = r["bridge_mesh_after"]
same = all(m[k] == a[k] for k in ("vertices", "faces", "quads", "uv_layers", "materials", "dimensions", "uv_coverage", "uv_overlap_samples"))
steps = [json.loads(l) for l in (o / "gui_steps.jsonl").read_text().splitlines()]
s = {"gui_steps": {x["name"]: x["result"] for x in steps}, "uv_session": (o / "hh_crown_uv.obj.txt").exists() or None,
     "receiver": rc["result"], "received": rc["received_payloads"], "roundtrip": r["result"], "checks": r["checks"],
     "reopen_equal": same and m["material_group"] == "TWO_PBR_Factory" and m["source_sha256"] == r["output_blend_sha256"],
     "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(o.glob("*")) if p.suffix in (".blend", ".obj", ".fbx", ".hairmesh")},
     "scope": "qualification hairstyle on a neutral head; not a Morwen candidate; art QA NOT_RUN"}
s["result"] = "PASS" if rc["result"] == "PASS" and r["result"] == "PASS" and s["reopen_equal"] and all(v == "PASS" for v in s["gui_steps"].values()) else "FAIL"
(o / "hairharpy_roundtrip_summary.json").write_text(json.dumps(s, indent=1))
print("TWO_HH_GUI_ROUNDTRIP", json.dumps(s))
assert s["result"] == "PASS"
PY
