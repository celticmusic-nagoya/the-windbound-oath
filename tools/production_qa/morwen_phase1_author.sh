# Sourced inside qualified native session. Candidate trials, not adopted shape.
set -o pipefail
# Fail closed before any edits if the restored checkpoint is not the intended native original.
printf "%s  %s\n" 9aba397dc080af510cc299cde1459accc83f468fa6bfa139229fe7e720887574 evidence/input-model.vroid | shasum -a 256 -c || { echo BLOCKED_WRONG_INPUT > evidence/authoring-status.txt; exit 1; }
printf 'stage\tstatus\n' > evidence/phase1-stages.tsv
record() { printf '%s\t%s\n' "$1" "$2" >> evidence/phase1-stages.tsv; }
trial() {
  local tag="$1" cat="$2" label="$3" delta="$4"
  face_cat "$cat"
  if [ "$tag" = brow-arch ]; then "$gui" scroll 0.89 0.60 -12 0; sleep 1; fi
  if slider_by "$tag" "$label" "$delta"; then
    record "$tag" EDITED_REVIEW_REQUIRED
  else
    record "$tag" BLOCKED_CONTROL_OR_RESPONSE
  fi
}
views phase1-before 25
# Provisional small reversible trials: strengthen nose relief and widen mouth.
# The exact native slider-to-projection mapping is not yet calibrated.
record nose-size PRESERVED_PRIOR_CHECKPOINT
record mouth-width PRESERVED_PRIOR_CHECKPOINT
record brow-arch PRESERVED_PRIOR_CHECKPOINT
views phase1-after 0
# Hair editor and body controls are not qualified for shape changes. Preserve them.
"$gui" vroid-shortcut hair; sleep 2
# Separate category from hairstyle sets; capture evidence without replacing any preset.
"$gui" click 0.023 0.231; sleep 2
capture_state phase2-hair-category
if grep -Fq 'Edit Hairstyle' evidence/phase2-hair-category.txt && grep -Fq 'Front' evidence/phase2-hair-category.txt; then
  record hair BLOCKED_STRAND_EDITOR_UNQUALIFIED
else
  record hair BLOCKED_WRONG_PANEL
fi
capture_state phase2-before-body
if "$gui" click-label evidence/phase2-before-body.png Body Outfit; then
  sleep 2
  capture_state phase2-body-top
  if grep -Fq 'Whole Body' evidence/phase2-body-top.txt; then
    "$gui" scroll 0.89 0.81 -12 0; sleep 2
    capture_state phase2-body-parameters
    record body BLOCKED_PROJECTION_AND_CONTROLS_UNQUALIFIED
  else
    record body BLOCKED_WRONG_PANEL
  fi
else
  record body BLOCKED_TAB_NOT_FOUND
fi
if ! grep -q EDITED_REVIEW_REQUIRED evidence/phase1-stages.tsv; then
  cp evidence/input-model.vroid evidence/model.vroid
  shasum -a 256 evidence/model.vroid > evidence/model-sha256.txt
  record checkpoint UNCHANGED_INPUT_REUSED
elif ! native_save; then
  echo BLOCKED_NATIVE_SAVE_NOT_VERIFIED > evidence/authoring-status.txt
  exit 1
fi
if ! reopen_copy; then
  echo BLOCKED_NATIVE_REOPEN_NOT_VERIFIED > evidence/authoring-status.txt
  exit 1
fi
verify_trial() {
  local tag="$1" cat="$2" label="$3" actual expected
  expected=$(awk -v t="$tag" '$1==t {print $3}' evidence/face-edits.txt)
  if [ -z "$expected" ]; then return 0; fi
  face_cat "$cat"; if [ "$tag" = brow-arch ]; then "$gui" scroll 0.89 0.60 -12 0; sleep 1; fi; capture_state "phase1-reopen-$tag"
  actual=$("$row" "evidence/phase1-reopen-$tag.png" "$label" | awk '{print $1}') || actual=UNKNOWN
  if [ "$actual" = "$expected" ]; then record "$tag" REOPEN_VALUE_MATCH; else record "$tag" REOPEN_VALUE_MISMATCH; fi
}
printf 'nose-size 0.106 0.194\nmouth-width -0.097 -0.026\nbrow-arch 0.000 0.053\n' >> evidence/face-edits.txt
verify_trial nose-size 0.729 '^Nose Size$'
verify_trial mouth-width 0.792 '^Mouth Width$'
verify_trial brow-arch "$CAT_BROW" '^Eyebrows Arch$'
face_cat "$CAT_IRIS"; capture_state phase1-reopen-iris
for axis in x y; do
  case "$axis" in x) pattern='^Iris Size \(X\)$'; expected=0.141;; y) pattern='^Iris Size \(Y\)$'; expected=0.194;; esac
  actual=$("$row" evidence/phase1-reopen-iris.png "$pattern" | awk '{print $1}') || actual=UNKNOWN
  if [ "$actual" = "$expected" ]; then record "iris-$axis" PRESERVED; else record "iris-$axis" REOPEN_VALUE_MISMATCH; fi
done
views phase1-reopened 25
echo PARTIAL_NATIVE_FACE_CANDIDATE_ART_QA_REQUIRED_HAIR_BODY_BLOCKED > evidence/authoring-status.txt
if grep -q REOPEN_VALUE_MISMATCH evidence/phase1-stages.tsv; then exit 1; fi
# Partial production must not be reported as a complete phase.
exit 2
