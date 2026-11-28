# W128 isolated native trial wrapper. Existing W116 startup, no credentials in this step.
set -euo pipefail
umask 077
test -z "${DEST_TOKEN:-}" && test -z "${GH_TOKEN:-}"
cd "$RUNNER_TEMP/morwen-private-recovery"
test "$(git -C "$GITHUB_WORKSPACE/qualified-vroid" hash-object tools/production_qa/morwen_vroid_session.sh)" = 4221afd5df6282a07bbb370c2fe228892e1fa2f6
test "$(git -C "$GITHUB_WORKSPACE" hash-object tools/production_qa/morwen_w125_save_return.py)" = f927d3f5e510bb9c76607178a086cf26d4476a59
mkdir -p qualified-vroid/tools/production_qa
cp "$GITHUB_WORKSPACE/qualified-vroid/tools/production_qa/morwen_vroid_session.sh" qualified-vroid/tools/production_qa/
bash -n "$GITHUB_WORKSPACE/tools/production_qa/morwen_w128_new_guide.sh"
swiftc tools/vroid_hair_stroke_qualification_W31.swift -o "$RUNNER_TEMP/two-gui-author"
swiftc tools/vroid_group_row_locator_W34.swift -o "$RUNNER_TEMP/w34-row-locator"
swiftc "$GITHUB_WORKSPACE/tools/production_qa/morwen_public_front_save_guard.swift" -o "$RUNNER_TEMP/hair-save-guard"
swiftc "$GITHUB_WORKSPACE/tools/production_qa/morwen_label_boxes.swift" -o "$RUNNER_TEMP/morwen-label-boxes"
python3 -m venv "$RUNNER_TEMP/w31-venv"
py="$RUNNER_TEMP/w31-venv/bin/python"
"$RUNNER_TEMP/w31-venv/bin/pip" install --only-binary=:all: 'Pillow==12.3.0' 'numpy>=2.0,<3'
"$py" -m py_compile tools/w107_brush.py tools/w108_guide_fit.py tools/w110_camera_register.py "$GITHUB_WORKSPACE/tools/production_qa/morwen_w128_guide.py" "$GITHUB_WORKSPACE/tools/production_qa/morwen_w125_save_return.py"
# Real-fixture preflight of the W128 measurement on the exact W108 F06-ready screen.
"$py" - <<'PY'
import json,os,pathlib,sys
sys.path.insert(0,os.environ['GITHUB_WORKSPACE']+'/tools/production_qa')
import morwen_w128_guide as w
p=pathlib.Path(os.environ['RUNNER_TEMP'])/'W108-fixture'
bp=json.load(open('production/morwen/MORWEN_HAIR_BLANK_BLUEPRINT_W92_20261127.json'))
reg=json.load(open(p/'W108-face-registration.json'))
wire=w.guide_mask(w.rgb(p/'W108-F05-ready.png'));sil,_,_=w.silhouette(wire)
d={l:float(max(w.signed_distance_at(sil,w.lane_path(bp,l,reg)[0]))) for l in ('F05','F06','F01')}
assert d['F05']<0 and 4.0<d['F06']<5.0 and 5.2<d['F01']<6.2,d
PY
source "$GITHUB_WORKSPACE/tools/production_qa/morwen_public_recovery_startup.sh"
gui="$RUNNER_TEMP/two-gui-author"
MORWEN_READONLY_NATIVE="$HOME/Documents/Morwen-resume.vroid"
source "$GITHUB_WORKSPACE/tools/production_qa/morwen_w128_new_guide.sh"
cmp "$RUNNER_TEMP/Morwen-resume.vroid" evidence/input-model.vroid
test -s evidence/W128-new-guide-not-adopted.vroid
echo W128_SAVED_REOPENED_NOT_ADOPTED
