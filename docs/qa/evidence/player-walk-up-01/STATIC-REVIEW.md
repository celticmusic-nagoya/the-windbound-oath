# UP01 initial independent static review

Reviewed HEAD2221e25533199f1e786467414be7073f9f043240, AGENTS policy, DEV wrapper/common UI, Node and m65. No source edit/browser execution by reviewer. Runtime/exact-final-head QA is pending author handoff.

No blocking source-code issue found in this initial state. up-walk-qa.js returns before installation unless WINDBOUND_DEV and explicit upWalkQA=1 both hold. It wraps FieldWalkMotion in memory, leaving original bank/source objects and underlying shared phase/bob functions unchanged. Only Aidan/up/walk descriptors are cloned; idle, other directions/actors and A baseline return original descriptors. Conditions B/C select existing03/04/01/06, C/D scale bob, without PNG or movement/collision/SAVE writes. LOAD invalidation/pagehide reset selection to A. Continued field application after closing preview is intentional and visibly disclosed. DEV-only state is not serialized.

Spatial-cap UI is separate from playback rate and limited to opted-in Aidan-up. Source selector reuses existing preview pause/reset/load/layout path. Actual field wrapper will affect up-diagonal rendering where existing heading chooses up; it does not change input velocity or heading algorithm.

Node tests cover no URL opt-in, four exact orders/bob/rate, original-identity for other directions/Fiona/idle, bank immutability, invalid condition and reset hooks. Gap notified to author: fixture always sets WINDBOUND_DEV=true, so DEV=false with explicit query lacks independent double-gate branch coverage. Recommend that meaningful small negative case before freeze.

m65 exercises actual decoded preview URLs/order/cadence/bob, ordinary keyboard-only field motion straight/diagonals, return cleanup and protected gameplay state in3viewports. Paused-frame reset before each scale is a necessary fixture correction. Heading-transition filtering must retain raw rows and exclude only documented transient orientation, not hide sustained wrong-source errors. Final review must distinguish loaded actual image state and selector/heading transitions, and inspect all FAIL lines regardless exit.

No naturalness/actualAndroid/adoption conclusion is inferred from arithmetic tests. No main/Pages/asset adoption operation is included in this read-only review.

## Updated nonbrowser checks at4b2d3f82227f758990437a61d06a0d63255c9c9d

Own direct Node execution of all18 test files:PASS, logs and `node-independent.json` outside repo. New negative case verifies WINDBOUND_DEV=false with URLoptin returns without DOM installation or wrapper; initial coverage recommendation resolved. All1833 baselinePNG unchanged, all259 formalSHA match, all10 immutablePR147source/support files unchanged, productionfield/IMG/data/battle diff empty. Protection script reached only its clean-tree assertion because parent was assembling untracked QA evidence; this is preserved as a preliminary incomplete clean-state check, not a content mismatch or finalHEADPASS. Repeat at final frozen clean HEAD. No browser or source edits by this reviewer.
