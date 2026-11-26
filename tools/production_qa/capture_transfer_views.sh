#!/usr/bin/env bash
# Run after an isolated native reopen and after the caller's Git fence check.
# The caller supplies the existing macos_gui binary and protected work-copy path.
set -euo pipefail
test "$(uname -s)" = Darwin
gui=$1
source=$2
out=$3
expected=acc7805b6a5b63913bccb7c28e30e1c9e4da6473ed083b5c0673f73cdca9e23a

check_source() {
  test -f "$source" && test ! -L "$source"
  test "$(shasum -a 256 "$source" | cut -d ' ' -f 1)" = "$expected"
}
check_source
mkdir "$out"
printf '%s\n' "$expected" > "$out/native-before.txt"
# Reuse the worker's existing measured frame-margin and bounded pan method.
frame_margin="$RUNNER_TEMP/frame-margin"
test -x "$frame_margin"
"$gui" vroid-shortcut face
"$gui" vroid-shortcut front
sleep 2
: > "$out/frame-margin.txt"
for view in front left4 left8 right4; do
  "$gui" vroid-shortcut front
  sleep 2
  case "$view" in
    left4) turn=turn-left; count=4 ;;
    left8) turn=turn-left; count=8 ;;
    right4) turn=turn-right; count=4 ;;
    front) count=0 ;;
  esac
  for ((i=0; i<count; i++)); do
    "$gui" vroid-shortcut "$turn"
    sleep 0.45
  done
  action=default; last_y=0; pan_used=0
  for attempt in 0 1 2 3; do
    sleep 2
    "$gui" screenshot "$out/$view.png"
    "$gui" ocr "$out/$view.png" > "$out/$view.txt"
    grep -Fq 'Morwen-resume.vroid' "$out/$view.txt"
    grep -Eq 'Face|Hairstyle|Body|Outfit' "$out/$view.txt"
    if grep -Eq 'Recently Edited|Texture Editor|Cancel' "$out/$view.txt"; then exit 1; fi
    if result=$("$frame_margin" "$out/$view.png"); then good=1; else good=0; fi
    read -r label xmin ymin xmax ymax foreground count margin_label margin <<< "$result"
    test "$label" = bbox && test "$foreground" = foreground_pixels && test "$margin_label" = margin
    for value in "$xmin" "$ymin" "$xmax" "$ymax" "$count" "$margin"; do
      [[ "$value" =~ ^[0-9]+$ ]] || exit 1
    done
    printf '%s %s %s %s %s %s %s %s %s %s\n' "$view" "$attempt" "$action" "$xmin" "$ymin" "$xmax" "$ymax" "$count" "$margin" "$good" >> "$out/frame-margin.txt"
    if [ "$good" = 1 ] || [ "$attempt" = 3 ]; then break; fi
    if [ "$pan_used" -lt 2 ] && [ "$ymax" -ge 693 ] && [ "$ymin" -ge 235 ] && { [ "$pan_used" = 0 ] || { [ "$action" = pan_up ] && [ "$((last_y-ymin))" -ge 30 ]; }; }; then
      last_y="$ymin"
      "$gui" pan 0.50 0.57 0.50 0.37 0.5
      pan_used=$((pan_used+1))
      action=pan_up
    elif [ "$action" = pan_up ] && [ "$ymin" -gt "$((last_y+10))" ]; then
      "$gui" pan 0.50 0.37 0.50 0.57 0.5
      action=undo_reversed_pan
    else
      break
    fi
  done
  # Frame margin is a heuristic, not proof of full feet, orientation or art acceptance.
  # Retain even HOLD captures privately to avoid blocking the technical export.
  check_source
done
"$gui" vroid-shortcut front
check_source
printf '%s\n' "$expected" > "$out/native-after-views.txt"
