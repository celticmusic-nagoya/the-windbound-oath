# W128 (Claude, face/hair lead): independent new Freehand guide G2 on the exact W108 work copy.
# Mutates only the isolated Documents work copy. G1 (five W108 strands and its guide) is never
# selected for editing. F06/F01 are drawn in G2 only when the measured G2 guide supports them
# (r <= +2.0 px, W121A method). Every stroke is completion-audited; failed strokes are undone.
# Save uses the W125/W126 bounded observer (single click, no re-click). No credentials here.
set -euo pipefail
umask 077
test -z "${DEST_TOKEN:-}" && test -z "${GH_TOKEN:-}"
export MORWEN_EXPECTED_SHA256=9803ab697c5c902ce74785a3a38c6e6a75c7a4a232828dfb62a5769ce236de9a
cmp evidence/input-model.vroid "$MORWEN_READONLY_NATIVE"
test "$(shasum -a 256 evidence/input-model.vroid | cut -d ' ' -f1)" = "$MORWEN_EXPECTED_SHA256"
sed '/^case "\$MODE" in/,$d' qualified-vroid/tools/production_qa/morwen_vroid_session.sh > "$RUNNER_TEMP/session-helpers.sh"
bash -n "$RUNNER_TEMP/session-helpers.sh"
source "$RUNNER_TEMP/session-helpers.sh"
py="$RUNNER_TEMP/w31-venv/bin/python"
locator="$RUNNER_TEMP/w34-row-locator"
boxes="$RUNNER_TEMP/morwen-label-boxes"
w128="$GITHUB_WORKSPACE/tools/production_qa/morwen_w128_guide.py"
observer="$GITHUB_WORKSPACE/tools/production_qa/morwen_w125_save_return.py"
design=production/morwen/MORWEN_HAIR_BLANK_BLUEPRINT_W92_20261127.json
fixture="$RUNNER_TEMP/W108-fixture"
eye_reference="$fixture/W108-F06-ready.png"
status() { echo "$1" > evidence/W128-status.txt; echo "W128_$1"; }

open_front_editor() {
  local tag="$1" expected="$2"
  "$gui" vroid-shortcut hair
  sleep 2
  capture_state "$tag-tab"
  grep -Fq "$expected" "evidence/$tag-tab.txt"
  grep -Fq 'Hairstyle Sets' "evidence/$tag-tab.txt"
  "$gui" click 0.023 0.231
  sleep 2
  capture_state "$tag-category"
  grep -Fq 'Front' "evidence/$tag-category.txt"
  "$gui" click-label "evidence/$tag-category.png" 'Edit Hairstyle' 'Front'
  sleep 3
  capture_state "$tag-editor"
  grep -Fq 'Hair Groups' "evidence/$tag-editor.txt"
  grep -Fq 'Add Freehand Hair Guides' "evidence/$tag-editor.txt"
  grep -Fq "$expected" "evidence/$tag-editor.txt"
}
rows() { "$locator" "evidence/$1.png" > "evidence/$1-rows.json"; }
no_modal() {
  if grep -Eq 'Cancel|Discard|Close without saving|Do you want' "evidence/$1.txt"; then return 1; fi
}

status STARTED
open_front_editor W128-before Morwen-resume.vroid
rows W128-before-editor
"$py" - <<'PY'
import json;d=json.load(open('evidence/W128-before-editor-rows.json'))
assert [r['label'] for r in d['rows']]==['Freehand Group 1'],d
PY
"$gui" vroid-shortcut front
"$gui" zoom 0.50 0.49 12 0
sleep 3
"$gui" move 0.70 0.10
capture_state W128-framing
no_modal W128-framing

# 1. Independent new guide group. Unknown modal => fail closed (no confirmation click).
"$gui" click-label evidence/W128-framing.png 'Add Freehand Hair Guides' 'Hair Groups'
sleep 3
"$gui" move 0.70 0.10
capture_state W128-g2-added
no_modal W128-g2-added
grep -Fq 'Morwen-resume.vroid' evidence/W128-g2-added.txt
rows W128-g2-added
read -r g1x g1y g2x g2y <<< "$("$py" "$w128" groups evidence/W128-g2-added-rows.json)"
status G2_CREATED

# 2. Select G2, brush mode, register camera on the invariant jacket, measure the new guide.
"$gui" click "$g2x" "$g2y"
sleep 2
"$gui" vroid-shortcut hair-brush
sleep 2
"$gui" move 0.70 0.10
capture_state W128-g2-brush
no_modal W128-g2-brush
rows W128-g2-brush
"$py" tools/w110_camera_register.py register "$eye_reference" evidence/W128-g2-brush.png "$fixture/W108-face-registration.json" evidence/W128-registration.json
draw=$("$py" "$w128" guide evidence/W128-g2-brush.png evidence/W128-g2-brush-rows.json evidence/W128-registration.json "$design" evidence/W128-g2-guide.json)
echo "$draw" > evidence/W128-draw-plan.txt
status G2_GUIDE_MEASURED

# 4. Draw only eligible lanes into G2, outermost first; audit; undo truncated strokes.
prev=W128-g2-brush
ndrawn=0
for lane in $draw; do
  test "$lane" = NONE && break
  args=$("$py" "$w128" points evidence/W128-g2-guide.json "$lane")
  set -f; set -- $args; set +f
  "$gui" hair-stroke-qualification "$@" > "evidence/W128-$lane-dispatch.txt"
  grep -qx W31_SINGLE_CONTINUOUS_STROKE_SENT "evidence/W128-$lane-dispatch.txt"
  sleep 3
  "$gui" move 0.70 0.10
  capture_state "W128-$lane-after"
  no_modal "W128-$lane-after"
  "$py" "$w128" newlabel "evidence/$prev.txt" "evidence/W128-$lane-after.txt" > "evidence/W128-$lane-label.txt"
  if "$py" "$w128" complete "evidence/$prev.png" "evidence/W128-$lane-after.png" evidence/W128-registration.json "$design" "$lane" "evidence/W128-$lane-completion.json"; then
    ndrawn=$((ndrawn+1))
    echo "$lane DRAWN_COMPLETE_G2" >> evidence/W128-lanes.txt
    prev="W128-$lane-after"
  else
    "$gui" vroid-shortcut undo
    sleep 2
    "$gui" move 0.70 0.10
    capture_state "W128-$lane-undone"
    "$py" - "$prev" "W128-$lane-undone" <<'PY'
import collections,re,sys
c=lambda t:collections.Counter(re.findall(r'\bHair \d+\b',open('evidence/'+t+'.txt').read()))
assert c(sys.argv[1])==c(sys.argv[2]),'undo did not restore hair labels'
PY
    echo "$lane UNDONE_NOT_COMPLETE" >> evidence/W128-lanes.txt
  fi
done
touch evidence/W128-lanes.txt
status "STROKES_$ndrawn"

# 5. Pre-save views (G2 selected), then close editor and save the Front item once.
"$gui" vroid-shortcut hair-select
sleep 1
"$gui" move 0.70 0.10
capture_state W128-pre-save-g2
"$gui" vroid-shortcut front-right
sleep 2
capture_state W128-oblique-before-save
"$gui" vroid-shortcut front
sleep 1
"$gui" click 0.0234 0.0990
sleep 2
capture_state W128-save-dialog
grep -Fq 'Close Hairstyle Editor' evidence/W128-save-dialog.txt
close_shot=W128-save-dialog
"$RUNNER_TEMP/hair-save-guard" "evidence/$close_shot.png" > evidence/W128-save-selection.txt 2>evidence/W128-save-diag.txt || true
if grep -Fxq 'Front unchecked Back unchecked' evidence/W128-save-selection.txt; then
  "$gui" click 0.33984 0.47396
  sleep 1
  capture_state W128-save-front
  close_shot=W128-save-front
fi
"$RUNNER_TEMP/hair-save-guard" "evidence/$close_shot.png" > evidence/W128-save-selection-final.txt 2>evidence/W128-save-final-diag.txt
grep -Fxq 'Front checked Back unchecked' evidence/W128-save-selection-final.txt
"$gui" click-label "evidence/$close_shot.png" 'Save as new item' 'Close Hairstyle Editor'
# W125/W126 bounded observer replaces the failed fixed sleep 4 (no re-click).
"$py" "$observer" --gui "$gui" --evidence evidence --document Morwen-resume.vroid
grep -Fq 'Body' evidence/W110-save-return.txt
grep -Fq 'Outfit' evidence/W110-save-return.txt
if grep -Fq 'Close Hairstyle Editor' evidence/W110-save-return.txt || dialog_visible W110-save-return; then exit 1; fi
status FRONT_ITEM_SAVED
cmp evidence/input-model.vroid "$MORWEN_READONLY_NATIVE"
chmod u+w "$MORWEN_READONLY_NATIVE"
native_save
"$py" - <<'PY'
import pathlib,hashlib,zipfile,json
p=pathlib.Path('evidence');a=p/'input-model.vroid';b=p/'model.vroid'
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
assert sha(a)=='9803ab697c5c902ce74785a3a38c6e6a75c7a4a232828dfb62a5769ce236de9a' and sha(a)!=sha(b)
with zipfile.ZipFile(a) as x,zipfile.ZipFile(b) as y:
    assert x.testzip() is None and y.testzip() is None
    assert set(x.namelist())==set(y.namelist()) and x.read('v1model/data.bin')!=y.read('v1model/data.bin')
    for n in set(x.namelist())-{'v1model/data.bin','thumbnails/thumbnail.jpg'}:assert x.read(n)==y.read(n)
with (p/'W128-saved-unverified.vroid').open('xb') as f:f.write(b.read_bytes())
(p/'W128-checkpoint-receipt.json').write_text(json.dumps(dict(status='SAVED_REOPEN_PENDING',source_sha256=sha(a),candidate_sha256=sha(b)),indent=2))
PY
status SAVED_CHECKPOINT

# 6. Reopen the saved copy and verify G1+G2 and the G2 strand labels persisted.
reopen_copy
open_front_editor W128-reopened Morwen-c1.vroid
rows W128-reopened-editor
read -r r1x r1y r2x r2y <<< "$("$py" "$w128" groups evidence/W128-reopened-editor-rows.json)"
"$gui" click "$r2x" "$r2y"
sleep 2
"$gui" vroid-shortcut hair-select
sleep 1
"$gui" move 0.70 0.10
capture_state W128-reopened-g2
"$py" - <<'PY'
import collections,re
c=lambda t:collections.Counter(re.findall(r'\bHair \d+\b',open('evidence/'+t+'.txt').read()))
a,b=c('W128-pre-save-g2'),c('W128-reopened-g2')
assert a==b,(a,b)
t=open('evidence/W128-reopened-g2.txt').read()
assert 'Morwen-c1.vroid' in t and 'Morwen-c1.vroid*' not in t
PY
"$gui" vroid-shortcut front
"$gui" zoom 0.50 0.49 12 0
sleep 2
"$gui" move 0.70 0.10
capture_state W128-reopened-front
"$gui" vroid-shortcut front-right
sleep 2
capture_state W128-reopened-oblique
"$gui" vroid-shortcut front
cmp evidence/model.vroid evidence/W128-saved-unverified.vroid
mv evidence/W128-saved-unverified.vroid evidence/W128-new-guide-not-adopted.vroid
"$py" - <<'PY'
import pathlib,json,hashlib
p=pathlib.Path('evidence')
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
lanes=(p/'W128-lanes.txt').read_text().splitlines()
(p/'W128-receipt.json').write_text(json.dumps(dict(
  status='NEW_INDEPENDENT_GUIDE_SAVED_REOPENED_NOT_ADOPTED',source_sha256=sha(p/'input-model.vroid'),
  candidate_sha256=sha(p/'W128-new-guide-not-adopted.vroid'),groups=['Freehand Group 1','Freehand Group 2'],
  lanes=lanes,draw_plan=(p/'W128-draw-plan.txt').read_text().split(),save_reopen=True,
  screenshots={q.name:sha(q) for q in sorted(p.glob('W128-*.png'))},
  limitations=['G2 guide measured as 2D front proxy; no D4','G1 untouched incl. truncated W108 F01 stub','independent G2/G3/G4 pending']),indent=2))
PY
status NEW_GUIDE_SAVED_REOPENED
# 7. Observation only, on the reopened copy after the candidate is final (never saved again):
# locate G2's guide row and record the guide/control-mode screens for the next guide-fit run.
"$gui" click "$r2x" "$r2y"
sleep 2
"$gui" move 0.70 0.10
capture_state W128-obs-g2
"$boxes" evidence/W128-obs-g2.png '^(L )?Freehand Guides$' > evidence/W128-guide-rows.json
gxy=$("$py" - "$r2y" <<'PY'
import json,sys
g2y=float(sys.argv[1])*768
m=[r for r in json.load(open('evidence/W128-guide-rows.json'))['matches'] if g2y+5<r['y']<g2y+70]
print(f"{m[0]['x']/1024:.8f} {m[0]['y']/768:.8f}" if len(m)==1 else 'NONE')
PY
)
if test "$gxy" != NONE; then
  read -r gx gy <<< "$gxy"
  "$gui" click "$gx" "$gy"
  sleep 2
  "$gui" move 0.70 0.10
  capture_state W128-obs-guide-selected
  "$gui" vroid-shortcut hair-control
  sleep 2
  "$gui" move 0.70 0.10
  capture_state W128-obs-guide-control
  "$gui" vroid-shortcut hair-select
  echo GUIDE_ROW_OBSERVED_AFTER_FINAL_SAVE > evidence/W128-guide-observation.txt
else
  echo GUIDE_ROW_NOT_UNIQUE_NOT_CLICKED > evidence/W128-guide-observation.txt
fi
cmp evidence/model.vroid evidence/W128-new-guide-not-adopted.vroid
status NEW_GUIDE_SAVED_REOPENED_OBSERVED
