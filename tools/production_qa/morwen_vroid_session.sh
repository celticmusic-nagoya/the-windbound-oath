# shellcheck shell=bash
# Morwen native VRoid authoring session (Claude lease, PR #427).
# Sourced by .github/workflows/morwen-vroid-macos-probe.yml after the resume
# checkpoint is open in the editor. Relies on: gui, capture_state, evidence/.
# MODE=survey : non-destructive UI map + high-zoom matched views, no save.

MODE="${MORWEN_SESSION_MODE:-survey}"
echo "MODE $MODE" > evidence/session.txt

face_tab() { "$gui" click 0.095 0.099; sleep 1; }

views() {
  # $1 stage, $2 zoom wheel count (relative to the editor default)
  local stage="$1" z="$2" n
  "$gui" vroid-shortcut face
  sleep 1
  "$gui" vroid-shortcut front
  sleep 1
  "$gui" zoom 0.50 0.42 "$z" 0
  sleep 2
  capture_state "view-$stage-front"
  for n in 1 2 3; do "$gui" vroid-shortcut turn-left; done
  sleep 1
  capture_state "view-$stage-left"
  "$gui" vroid-shortcut front
  for n in 1 2 3; do "$gui" vroid-shortcut turn-right; done
  sleep 1
  capture_state "view-$stage-right"
  "$gui" vroid-shortcut front
  for n in 1 2 3 4 5 6; do "$gui" vroid-shortcut turn-left; done
  sleep 1
  capture_state "view-$stage-back"
  "$gui" vroid-shortcut front
  sleep 1
}

survey_face_categories() {
  local i y
  # Observed icon centres (px of 768) in the Face tab left column.
  local ys=(0.169 0.230 0.293 0.354 0.419 0.479 0.540 0.603 0.668 0.729 0.792 0.855)
  for i in "${!ys[@]}"; do
    y="${ys[$i]}"
    face_tab
    "$gui" click 0.023 "$y"
    sleep 2
    capture_state "survey-face-$i-top"
    "$gui" scroll 0.89 0.60 -12 0
    sleep 1
    capture_state "survey-face-$i-mid"
    "$gui" scroll 0.89 0.60 -12 0
    sleep 1
    capture_state "survey-face-$i-end"
    echo "face-$i y=$y" >> evidence/session.txt
  done
  # Icons hidden below the window edge, if any.
  face_tab
  "$gui" scroll 0.023 0.60 -12 0
  sleep 1
  capture_state "survey-face-iconcolumn-scrolled"
}

survey_hair() {
  "$gui" vroid-shortcut hair
  sleep 3
  capture_state survey-hair-top
  "$gui" scroll 0.89 0.60 -12 0
  sleep 1
  capture_state survey-hair-mid
  "$gui" vroid-shortcut face
  sleep 2
}

case "$MODE" in
  survey)
    views std 25
    views close 30
    survey_face_categories
    survey_hair
    echo SURVEY_COMPLETE_NO_EDIT_NO_SAVE > evidence/authoring-status.txt
    ;;
  *)
    echo "BLOCKED_UNKNOWN_MODE $MODE" > evidence/authoring-status.txt
    exit 1
    ;;
esac
