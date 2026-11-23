# Source after the verified VRoid Open dialog has loaded the SHA-pinned copy.
# The existing macOS harness supplies gui, capture_state and evidence/.
: "${MORWEN_READONLY_NATIVE:?absolute path to the isolated native copy}"
: "${MORWEN_EXPECTED_SHA256:?SHA-256 of the isolated native copy}"
: "${gui:?existing macOS GUI helper required}"
declare -F capture_state >/dev/null || return 1
test -f "$MORWEN_READONLY_NATIVE" && test ! -L "$MORWEN_READONLY_NATIVE" || return 1
chmod a-w "$MORWEN_READONLY_NATIVE" || return 1
printf '%s  %s\n' "$MORWEN_EXPECTED_SHA256" "$MORWEN_READONLY_NATIVE" | shasum -a 256 -c || return 1
sed -n '/^views() {/,/^}/p' tools/production_qa/morwen_vroid_session.sh > "$RUNNER_TEMP/morwen-views.sh"
test -s "$RUNNER_TEMP/morwen-views.sh" || return 1
source "$RUNNER_TEMP/morwen-views.sh"

# Calibration mode intentionally reuses the already SHA-verified captures from run
# 45117436032; do not regenerate the four views in this diagnostic run.
case "${MORWEN_CAPTURE_MODE:-full}" in
  full)
    for direction in front left right back; do
      test ! -e "evidence/view-isolated-reopen-$direction.png" || return 1
    done
    views isolated-reopen 25 || return 1
    for direction in front left right back; do
      test -s "evidence/view-isolated-reopen-$direction.png" || return 1
    done
    test "$(shasum -a 256 evidence/view-isolated-reopen-{front,left,right,back}.png | cut -d ' ' -f1 | sort -u | wc -l | tr -d ' ')" = 4 || return 1
    shasum -a 256 evidence/view-isolated-reopen-{front,left,right,back}.png > evidence/reopen-view-sha256.txt || return 1
    ;;
  rear-only)
    test ! -e evidence/reopen-view-sha256.txt || return 1
    "$gui" vroid-shortcut face || return 1
    sleep 1
    "$gui" vroid-shortcut front || return 1
    sleep 1
    "$gui" zoom 0.50 0.42 25 0 || return 1
    sleep 2
    ;;
  *)
    echo "BLOCKED_UNKNOWN_CAPTURE_MODE" > evidence/readonly-reopen-status.txt
    return 1
    ;;
esac
printf '%s  %s\n' "$MORWEN_EXPECTED_SHA256" "$MORWEN_READONLY_NATIVE" | shasum -a 256 -c || return 1
# Diagnostic only: measure rear orientation without overwriting existing captures.
# The shortcut's angle per press has not been calibrated.
for steps in 5 6 7 8; do
  "$gui" vroid-shortcut front || return 1
  sleep 1
  for ((i=0; i<steps; i++)); do
    "$gui" vroid-shortcut turn-left || return 1
  done
  sleep 1
  test ! -e "evidence/rear-calibration-$steps.png" || return 1
  capture_state "rear-calibration-$steps" || return 1
  test -s "evidence/rear-calibration-$steps.png" || return 1
done
"$gui" vroid-shortcut front || return 1
shasum -a 256 evidence/rear-calibration-{5,6,7,8}.png > evidence/rear-calibration-sha256.txt || return 1
printf '%s  %s\n' "$MORWEN_EXPECTED_SHA256" "$MORWEN_READONLY_NATIVE" | shasum -a 256 -c || return 1
printf '%s\n' 'CAPTURED_REVIEW_REQUIRED_REAR_SWEEP_NOT_YET_CALIBRATED' > evidence/readonly-reopen-status.txt
