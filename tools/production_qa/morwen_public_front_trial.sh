# Isolated F06 native trial. Existing W116 startup and W110 authoring, no credentials.
set -euo pipefail
umask 077
test -z "${DEST_TOKEN:-}" && test -z "${GH_TOKEN:-}"
cd "$RUNNER_TEMP/morwen-private-recovery"
test "$(git -C "$GITHUB_WORKSPACE/qualified-vroid" hash-object tools/production_qa/morwen_vroid_session.sh)" = 4221afd5df6282a07bbb370c2fe228892e1fa2f6
mkdir -p qualified-vroid/tools/production_qa
cp "$GITHUB_WORKSPACE/qualified-vroid/tools/production_qa/morwen_vroid_session.sh" qualified-vroid/tools/production_qa/
bash -n tools/author_vroid_W110.sh
bash -n tools/w112_material_survey.sh
swiftc tools/vroid_hair_stroke_qualification_W31.swift -o "$RUNNER_TEMP/two-gui-author"
swiftc tools/vroid_group_row_locator_W34.swift -o "$RUNNER_TEMP/w34-row-locator"
swiftc "$GITHUB_WORKSPACE/tools/production_qa/morwen_public_front_save_guard.swift" -o "$RUNNER_TEMP/hair-save-guard"
python3 -m venv "$RUNNER_TEMP/w31-venv"
py="$RUNNER_TEMP/w31-venv/bin/python"
"$RUNNER_TEMP/w31-venv/bin/pip" install 'Pillow==12.3.0'
"$py" -m py_compile tools/w107_brush.py tools/w108_guide_fit.py tools/w109_visibility.py tools/w110_camera_register.py
# Recheck actual historical W108 guide limitation and unchanged eye visibility.
"$py" - <<'PY'
import os,pathlib,sys
sys.path.insert(0,'tools')
from w109_visibility import eyes
from w108_guide_fit import measure
p=pathlib.Path(os.environ['RUNNER_TEMP'])/'W108-fixture'
ref=p/'W108-F06-ready.png';reg=p/'W108-face-registration.json';anchor=p/'W108-face-registered.png'
bp='production/morwen/MORWEN_HAIR_BLANK_BLUEPRINT_W92_20261127.json'
eyes(ref,p/'W108-F06-ready.txt',ref,5,0)
try:eyes(ref,p/'W108-F06-ready.txt',ref,5,4)
except ValueError:pass
else:raise AssertionError('negative visibility control failed')
base=measure(ref,p/'W108-F06-ready-rows.json',reg,anchor,bp)
prev=measure(p/'W108-F05-ready.png',p/'W108-F05-ready-rows.json',reg,anchor,bp)
assert base['lanes']['F06']['unsupported']==1 and base['lanes']['F06']['max_distance_px']==6 and prev['lanes']['F06']['ready']
PY
# Reuse read-only startup, then mutate only the isolated Documents work copy.
source "$GITHUB_WORKSPACE/tools/production_qa/morwen_public_recovery_startup.sh"
gui="$RUNNER_TEMP/two-gui-author"
MORWEN_READONLY_NATIVE="$HOME/Documents/Morwen-resume.vroid"
source tools/author_vroid_W110.sh
# Survey only: do not create a shared material or apply textures without qualification.
# The already-saved/reopened F06 trial must survive a survey failure.
set +e
(set -euo pipefail; source tools/w112_material_survey.sh) > evidence/W112-survey.log 2>&1
survey_rc=$?
set -e
if test "$survey_rc" = 0; then
  echo MATERIAL_CONTROLS_OBSERVED_NO_MUTATION > evidence/W112-material-status.txt
else
  echo MATERIAL_SURVEY_HOLD_NO_MUTATION > evidence/W112-material-status.txt
fi
cmp "$RUNNER_TEMP/Morwen-resume.vroid" evidence/input-model.vroid
test -s evidence/W110-new-front-not-adopted.vroid
echo FRONT_TRIAL_SAVED_REOPENED_NOT_ADOPTED
