# shellcheck shell=bash
# Morwen native VRoid authoring session (ChatGPT lease, PR #427).
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


# ---- edit helpers (Claude lease) ------------------------------------------
face_cat() { face_tab; "$gui" click 0.023 "$1"; sleep 2; }
CAT_IRIS=0.293; CAT_BROW=0.479; CAT_LINER=0.603; CAT_LASH=0.668; CAT_FACESET=0.169

# set_hex TAG ROW_Y HEX : method v3 = colour-wheel geometry.
# v1 (single-click field, run 44873786133) and v2 (double-click field / popup
# hex field + synthetic unicode text, run 44874797940) did not edit: Unity text
# fields ignored the synthetic input. The popup wheel/SV square is pointer-only.
# Geometry measured on hex-iris-picker.png (1024x768): popup hex label box ->
# wheel centre (-42,+137) px, ring radius 96 px, hue 0 at top, clockwise;
# SV square origin (-100,+79) px, side 117 px, S left->right, V top->bottom.
hex_ok() { grep -Fqi "#${2#\#}" "evidence/$1.txt"; }
set_hex() {
  local tag="$1" y="$2" hex="${3#\#}" box pts
  "$gui" click 0.742 "$y"; sleep 2
  capture_state "hex-$tag-picker"
  box=$(swift -e 'import Vision; import Foundation; let r=VNRecognizeTextRequest(); try VNImageRequestHandler(url:URL(fileURLWithPath:CommandLine.arguments[1])).perform([r]); for o in r.results ?? [] { if let t=o.topCandidates(1).first?.string, t.range(of:"^#?[0-9A-Fa-f]{6}$",options:.regularExpression) != nil, o.boundingBox.midX < 0.75 { print(o.boundingBox.midX*1024, (1-o.boundingBox.midY)*768); exit(0) } }; exit(2)' "evidence/hex-$tag-picker.png") || box=""
  if [ -z "$box" ]; then echo "$tag PICKER_NOT_VERIFIED" >> evidence/face-edits.txt; "$gui" key 53; return 1; fi
  pts=$(python3 - $box "$hex" <<'PY2'
import sys, colorsys, math
bx, by, h = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
r, g, b = (int(h[i:i+2], 16)/255 for i in (0, 2, 4))
H, S, V = colorsys.rgb_to_hsv(r, g, b)
cx, cy = bx-42, by+137
a = H*2*math.pi
hx, hy = cx+96*math.sin(a), cy-96*math.cos(a)
sx, sy = bx-100+S*117, by+79+(1-V)*117
print(f"{hx/1024:.4f} {hy/768:.4f} {sx/1024:.4f} {sy/768:.4f}")
PY2
)
  read -r hx hy sx sy <<< "$pts"
  echo "$tag picker-box $box -> hue $hx $hy sv $sx $sy" >> evidence/face-edits.txt
  "$gui" click "$hx" "$hy"; sleep 1
  "$gui" click "$sx" "$sy"; sleep 1
  capture_state "hex-$tag-b"
  "$gui" key 53; sleep 1
  capture_state "hex-$tag"
  grep -Eo '#[0-9A-Fa-f]{6}' "evidence/hex-$tag-b.txt" | head -1 | sed "s/^/$tag picked /" >> evidence/face-edits.txt || true
  if ! grep -Fqi '#9E6233' "evidence/hex-$tag.txt" && grep -Eqi '#[0-9A-F]{6}' "evidence/hex-$tag.txt"; then
    echo "$tag HEX_WHEEL_APPLIED target $hex" >> evidence/face-edits.txt; return 0
  fi
  echo "$tag HEX_NOT_VERIFIED $hex" >> evidence/face-edits.txt; return 1
}

# slider_to TAG PATTERN DELTA_FRACTION : uses face-row locator from the workflow.
slider_by() {
  local tag="$1" pattern="$2" delta="$3" hit v x y v2
  capture_state "$tag-loc"
  hit=$("$row" "evidence/$tag-loc.png" "$pattern") || {
    echo "$tag CONTROL_NOT_VERIFIED" >> evidence/face-edits.txt; return 1; }
  read -r v x y <<< "$hit"
  "$gui" slider "$x" "$y" "$(awk -v a="$x" -v d="$delta" 'BEGIN{print a+d}')" "$y" 0.5
  sleep 1
  capture_state "$tag-after"
  hit=$("$row" "evidence/$tag-after.png" "$pattern") || { echo "$tag VALUE_NOT_VERIFIED" >> evidence/face-edits.txt; return 1; }
  read -r v2 x y <<< "$hit"
  echo "$tag $v $v2" >> evidence/face-edits.txt
  [ "$v" != "$v2" ]
}

saved_differs() {
  python3 - "$1" <<'PY2'
import sys, zipfile, hashlib
def digest(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if 'thumbnail' not in n.lower()}
a, b = digest("evidence/input-model.vroid"), digest(sys.argv[1])
changed = sorted(n for n in set(a) | set(b) if a.get(n) != b.get(n))
open("evidence/saved-diff.txt", "w").write("\n".join(changed) + "\n")
sys.exit(0 if changed else 1)
PY2
}

native_save() {
  local working="$HOME/Documents/Morwen-resume.vroid"
  capture_state save-before
  "$gui" key 1 cmd
  sleep 6
  capture_state save-shortcut
  if ! saved_differs "$working"; then
    "$gui" click 0.027 0.100; sleep 2
    capture_state save-menu
    grep -Fq 'Save As' evidence/save-menu.txt || { "$gui" key 53; return 1; }
    "$gui" click 0.03125 0.14583; sleep 6
    capture_state save-menu-result
    saved_differs "$working" || return 1
  fi
  cp "$working" evidence/model.vroid
  shasum -a 256 evidence/model.vroid > evidence/model-sha256.txt
}

reopen_copy() {
  local copy="$HOME/Documents/Morwen-c1.vroid"
  test ! -e "$copy"
  cp evidence/model.vroid "$copy"
  "$gui" click 0.027 0.100; sleep 2
  capture_state reopen-menu
  "$gui" click-label evidence/reopen-menu.png 'Back to model selection' 'Save As'
  sleep 6
  reopen_native || return 1
  capture_state checkpoint-open-dialog
  dialog_visible checkpoint-open-dialog || return 1
  if ! "$gui" click-label evidence/checkpoint-open-dialog.png 'Morwen-c1.vroid' 'Cancel'; then
    grep -Eiq 'Morwen-c1.*Morwen-resume' evidence/checkpoint-open-dialog.txt || return 1
    "$gui" click 0.340 0.286
  fi
  sleep 2
  capture_state checkpoint-open-selected
  grep -Eiq 'Morwen-c1' evidence/checkpoint-open-selected.txt || return 1
  "$gui" key 36
  sleep 30
  capture_state checkpoint-reopened
  grep -Eiq 'VRoid Studio.*Morwen-c1' evidence/checkpoint-reopened.txt || return 1
  cmp "$copy" evidence/model.vroid
}

face_batch_3() {
  face_cat "$CAT_IRIS";  capture_state cat-iris;  set_hex iris  "$(hex_row_y cat-iris)"  7A3E92 || true
  face_cat "$CAT_LASH";  capture_state cat-lash;  set_hex lash  "$(hex_row_y cat-lash)"  2A1730 || true
  face_cat "$CAT_LINER"; capture_state cat-liner; set_hex liner "$(hex_row_y cat-liner)" 2B1631 || true
  face_cat "$CAT_BROW";  capture_state cat-brow;  set_hex brow  "$(hex_row_y cat-brow)"  4A2B4E || true
  face_cat "$CAT_FACESET"
}

# y fraction of the first '#XXXXXX' OCR box in the right panel.
hex_row_y() {
  swift -e 'import Vision; import Foundation; let r=VNRecognizeTextRequest(); try VNImageRequestHandler(url:URL(fileURLWithPath:CommandLine.arguments[1])).perform([r]); for o in r.results ?? [] { if let t=o.topCandidates(1).first?.string, t.range(of:"^#[0-9A-Fa-f]{6}",options:.regularExpression) != nil, o.boundingBox.midX > 0.75 { print(1-o.boundingBox.midY); exit(0) } }; print("0.449")' "evidence/$1.png"
}

case "$MODE" in
  survey)
    views std 25
    views close 8
    survey_face_categories
    survey_hair
    echo SURVEY_COMPLETE_NO_EDIT_NO_SAVE > evidence/authoring-status.txt
    ;;
  edit)
    views before 25
    views beforeclose 6
    # Batch5: restore intended iris dimensions, preserving Batch4 chin.
    face_cat "$CAT_IRIS"
    slider_by iris-x '^Iris Size \(X\)$' 0.017 || exit 1
    slider_by iris-y '^Iris Size \(Y\)$' 0.022 || exit 1
    awk '$1=="iris-x" && $3+0>$2+0 {x=1} $1=="iris-y" && $3+0>$2+0 {y=1} END {exit !(x&&y)}' evidence/face-edits.txt || exit 1
    "$gui" zoom 0.50 0.42 -6 0
    views after 0
    views afterclose 6
    "$gui" zoom 0.50 0.42 -6 0
    if ! native_save; then echo BLOCKED_NATIVE_SAVE_NOT_VERIFIED > evidence/authoring-status.txt; exit 1; fi
    echo NATIVE_SAVED_REOPEN_PENDING > evidence/authoring-status.txt
    if ! reopen_copy; then echo SAVED_REOPEN_NOT_VERIFIED > evidence/authoring-status.txt; exit 1; fi
    "$gui" zoom 0.50 0.42 25 0
    views reopened 0
    views reopenedclose 6
    face_cat "$CAT_IRIS"; capture_state reopened-iris
    if ! grep -Fqi '793F91' evidence/reopened-iris.txt; then echo IRIS_COLOUR_REOPEN_REVIEW_REQUIRED >> evidence/face-edits.txt; fi
    echo NATIVE_FACE_BATCH5_SAVED_REOPENED_ART_QA_REQUIRED > evidence/authoring-status.txt
    ;;
  *)
    echo "BLOCKED_UNKNOWN_MODE $MODE" > evidence/authoring-status.txt
    exit 1
    ;;
esac
