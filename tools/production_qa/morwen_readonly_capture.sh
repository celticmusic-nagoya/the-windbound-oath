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

for direction in front left right back; do
  test ! -e "evidence/view-isolated-reopen-$direction.png" || return 1
done
views isolated-reopen 25 || return 1
for direction in front left right back; do
  test -s "evidence/view-isolated-reopen-$direction.png" || return 1
done
test "$(shasum -a 256 evidence/view-isolated-reopen-{front,left,right,back}.png | cut -d ' ' -f1 | sort -u | wc -l | tr -d ' ')" = 4 || return 1
shasum -a 256 evidence/view-isolated-reopen-{front,left,right,back}.png > evidence/reopen-view-sha256.txt || return 1
printf '%s  %s\n' "$MORWEN_EXPECTED_SHA256" "$MORWEN_READONLY_NATIVE" | shasum -a 256 -c || return 1
printf '%s\n' 'CAPTURED_REVIEW_REQUIRED' > evidence/readonly-reopen-status.txt
