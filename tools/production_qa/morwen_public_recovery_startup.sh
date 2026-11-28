# Reuse the qualified signed VRoid 2.16.0 GUI startup. Read-only recovery only.
set -euo pipefail
umask 077
app="$RUNNER_TEMP/VRoidStudio.app"
/usr/libexec/PlistBuddy -c 'Print CFBundleShortVersionString' "$app/Contents/Info.plist" > evidence/version.txt
exe="$(/usr/libexec/PlistBuddy -c 'Print CFBundleExecutable' "$app/Contents/Info.plist")"
file "$app/Contents/MacOS/$exe" > evidence/binary.txt
test "$(uname -m)" = arm64
# LaunchServices registers the app with the GUI session.
stat -f '%Su' /dev/console > evidence/console-user.txt
open -a "$app" --args -logFile "$RUNNER_TEMP/vroid-player.log"
sleep 15
osascript -e "tell application id \"net.pixiv.vroid.macosx\" to activate" > evidence/activate.txt 2>&1 || true
sleep 45
screencapture -x evidence/screen-60s.png || true
sleep 30
# Finder-only startup is not an editor failure; bounded activation recovery.
if ! osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true' | grep -qi VRoid; then
  osascript -e 'tell application id "net.pixiv.vroid.macosx" to activate' || true
  sleep 20
fi
# Verify the welcome screen text before issuing a bounded input event.
swift -e 'import Cocoa; import CoreGraphics; print(CGPreflightPostEventAccess()); print(CGDisplayPixelsWide(CGMainDisplayID()), CGDisplayPixelsHigh(CGMainDisplayID()))' > evidence/input-access.txt 2>&1
screencapture -x evidence/before-input.png
swift -e 'import Vision; import Foundation; let r = VNRecognizeTextRequest(); try VNImageRequestHandler(url:URL(fileURLWithPath:CommandLine.arguments[1])).perform([r]); for o in r.results ?? [] { print(o.topCandidates(1).first?.string ?? "") }' evidence/before-input.png > evidence/welcome-text.txt
if grep -qx true evidence/input-access.txt && grep -qx '1024 768' evidence/input-access.txt && grep -Fxq 'Get Started' evidence/welcome-text.txt; then
  swift -e 'import CoreGraphics; import Foundation; let p = CGPoint(x:512,y:578); let s = CGEventSource(stateID:.combinedSessionState); CGEvent(mouseEventSource:s,mouseType:.mouseMoved,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cgSessionEventTap); usleep(500000); for t in [CGEventType.leftMouseDown,.leftMouseUp] { if let e = CGEvent(mouseEventSource:s,mouseType:t,mouseCursorPosition:p,mouseButton:.left) { e.setIntegerValueField(.mouseEventClickState,value:1); e.post(tap:.cgSessionEventTap) }; usleep(250000) }'
  sleep 20
  screencapture -x evidence/after-get-started.png
  if cmp -s evidence/before-input.png evidence/after-get-started.png; then
    echo NO_SCREEN_CHANGE > evidence/gui-action.txt
  else
    echo SCREEN_CHANGED_REVIEW_REQUIRED > evidence/gui-action.txt
  fi
else
  echo INPUT_ACCESS_OR_DISPLAY_BLOCKED > evidence/gui-action.txt
fi
# Director explicitly authorized the agreement on 2026-11-20.
if [ -s evidence/after-get-started.png ] && grep -qx true evidence/input-access.txt; then
  swift -e 'import Vision; import Foundation; import CoreGraphics; let r = VNRecognizeTextRequest(); try VNImageRequestHandler(url:URL(fileURLWithPath:CommandLine.arguments[1])).perform([r]); let a = r.results ?? []; let strings = a.compactMap { $0.topCandidates(1).first?.string }; print(strings.joined(separator:" | ")); guard strings.contains(where:{$0.contains("Terms of Use")}), strings.contains(where:{$0.contains("Privacy Policy")}), strings.contains(where:{$0.contains("Guidelines")}), let o = a.first(where:{$0.topCandidates(1).first?.string == "Agree"}) else { print("AGREEMENT_SCREEN_NOT_VERIFIED"); exit(0) }; let p = CGPoint(x:o.boundingBox.midX * CGFloat(CGDisplayPixelsWide(CGMainDisplayID())),y:(1-o.boundingBox.midY)*CGFloat(CGDisplayPixelsHigh(CGMainDisplayID()))); let s = CGEventSource(stateID:.combinedSessionState); CGEvent(mouseEventSource:s,mouseType:.mouseMoved,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cgSessionEventTap); usleep(500000); for t in [CGEventType.leftMouseDown,.leftMouseUp] { if let e = CGEvent(mouseEventSource:s,mouseType:t,mouseCursorPosition:p,mouseButton:.left) { e.setIntegerValueField(.mouseEventClickState,value:1); e.post(tap:.cgSessionEventTap) }; usleep(250000) }; print("AGREEMENT_CLICK_SENT_REVIEW_REQUIRED")' evidence/after-get-started.png > evidence/agreement-status.txt
  sleep 25
  screencapture -x evidence/after-agreement.png
fi
cat > "$RUNNER_TEMP/vroid-click.swift" <<'SWIFT'
import Vision
import Foundation
import CoreGraphics
let r = VNRecognizeTextRequest()
try VNImageRequestHandler(url: URL(fileURLWithPath: CommandLine.arguments[1])).perform([r])
let a = r.results ?? []
let labels = a.compactMap { $0.topCandidates(1).first?.string }
print(labels.joined(separator:" | "))
guard labels.contains(where:{$0.contains(CommandLine.arguments[3])}), let o = a.first(where:{ let t = $0.topCandidates(1).first?.string.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""; return t == CommandLine.arguments[2] || (CommandLine.arguments[2] == "Open" && t == "• Open") }) else { print("SCREEN_NOT_VERIFIED"); exit(2) }
let d = CGDisplayBounds(CGMainDisplayID())
let offset: CGFloat = CommandLine.arguments[2] == "Fem" ? -116 : 0
let p = CGPoint(x:d.minX + o.boundingBox.midX*d.width,y:d.minY+(1-o.boundingBox.midY)*d.height+offset*d.height/768)
let s = CGEventSource(stateID:.combinedSessionState)
CGEvent(mouseEventSource:s,mouseType:.mouseMoved,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cgSessionEventTap)
usleep(500000)
for t in [CGEventType.leftMouseDown,.leftMouseUp] { if let e = CGEvent(mouseEventSource:s,mouseType:t,mouseCursorPosition:p,mouseButton:.left) { e.setIntegerValueField(.mouseEventClickState,value:1); e.post(tap:.cgSessionEventTap) }; usleep(250000) }
SWIFT
# Preserve immutable input before attempting any GUI action.
cp "$RUNNER_TEMP/Morwen-resume.vroid" evidence/input-model.vroid
shasum -a 256 evidence/input-model.vroid > evidence/input-model-sha256.txt
echo NATIVE_REOPEN_NOT_VERIFIED > evidence/reopen-status.txt
gui="$RUNNER_TEMP/two-gui"
capture_state() {
  "$gui" screenshot "evidence/$1.png" && "$gui" ocr "evidence/$1.png" > "evidence/$1.txt"
}
dialog_visible() {
  grep -Eiq 'Cancel' "evidence/$1.txt" && grep -Eiq 'Open|Choose' "evidence/$1.txt"
}
mkdir -p "$HOME/Documents"
test ! -e "$HOME/Documents/Morwen-resume.vroid"
cp "$RUNNER_TEMP/Morwen-resume.vroid" "$HOME/Documents/Morwen-resume.vroid"
cmp "$RUNNER_TEMP/Morwen-resume.vroid" "$HOME/Documents/Morwen-resume.vroid"
chmod a-w "$HOME/Documents/Morwen-resume.vroid"
reopen_native() {
  local attempt before after
  for attempt in 1 2 3; do
    before="home-attempt-$attempt"
    after="open-result-$attempt"
    capture_state "$before" || continue
    if dialog_visible "$before"; then return 0; fi
    if grep -Fq 'Recently Edited' "evidence/$before.txt"; then
      if [ "$attempt" -le 2 ]; then
        "$gui" click-label "evidence/$before.png" Open 'Recently Edited' > "evidence/open-click-$attempt.txt" 2>&1 || true
      else
        # Different method after two observations: standard macOS Open shortcut.
        "$gui" key 31 cmd || true
      fi
    else
      # Escape is reversible; never accept an unknown dialog.
      "$gui" key 53 || true
    fi
    sleep 4
    capture_state "$after" || continue
    if dialog_visible "$after"; then return 0; fi
    if ! grep -Fq 'Recently Edited' "evidence/$after.txt"; then
      "$gui" key 53 || true
      sleep 2
      capture_state "recovery-$attempt" || true
    fi
  done
  return 1
}
if [ -s evidence/after-agreement.png ] && grep -qx true evidence/input-access.txt; then
  swift "$RUNNER_TEMP/vroid-click.swift" evidence/after-agreement.png Skip 'Welcome to VRoid Studio' > evidence/skip-status.txt || true
  sleep 5
  if reopen_native; then
    capture_state open-dialog
    # The observed chooser defaults to Documents; avoid clipboard and Go to Folder.
    if grep -Fqi 'Documents' evidence/open-dialog.txt; then
      "$gui" click-label evidence/open-dialog.png 'Morwen-resume.vroid' 'Cancel' > evidence/file-click.txt 2>&1 || true
      sleep 2
      capture_state open-selected
      if dialog_visible open-selected && grep -Fqi 'Morwen-resume' evidence/open-selected.txt; then
        "$gui" key 36
        sleep 35
        capture_state resumed-editor
        if grep -Eiq 'Face|Hairstyle|Body|Outfit' evidence/resumed-editor.txt && ! dialog_visible resumed-editor; then
          echo NATIVE_REOPEN_REVIEW_REQUIRED > evidence/reopen-status.txt
        fi
      fi
    fi
  else
    echo BLOCKED_OPEN_SCREEN_NOT_VERIFIED > evidence/reopen-status.txt
  fi
fi
screencapture -x evidence/final-recovery-screen.png || true
grep -qx NATIVE_REOPEN_REVIEW_REQUIRED evidence/reopen-status.txt

grep -Fq 'Morwen-resume.vroid' evidence/resumed-editor.txt
if grep -Fq 'Morwen-resume.vroid*' evidence/resumed-editor.txt; then exit 1; fi
cmp "$RUNNER_TEMP/Morwen-resume.vroid" "$HOME/Documents/Morwen-resume.vroid"
cmp "$RUNNER_TEMP/Morwen-resume.vroid" evidence/input-model.vroid
echo REOPENED_READONLY_SOURCE_UNCHANGED > evidence/recovery-result.txt
