# Aidan PLAYER QA display control follow-up

Start: `51c6d811ed944492f1d98a0df5a4e4567a75d8a4`.
Branch: `work/lind-step9-11-prep`. Main remains `51cf09258b36c47ba1b9dc8954f385cbeaf018d9`.

## Source / remote diagnosis

Direct `git ls-remote` and an explicit branch fetch confirmed all 20 A1 PNGs and the DEV actor implementation at the remote branch start commit. The initial stale tracking ref was misleading: `remote.origin.fetch` fetches main only. The existing toggle was implemented, rather than only described in the report, but was labelled `Aidan 正式` / `Aidan 仮表示`. Main has neither the field actor script inclusion nor A1 assets. A work branch push alone does not establish Pages publication.

Initial public/API requests returned proxy tunnel 403. After network configuration propagation, both returned HTTP 200. Pages API confirms legacy deployment from `main` at `/`, status `built`; public HTML is byte-for-byte identical to `origin/main:index.html` and does not include `aidan-field-actor.js`. ROOT CAUSE: Aidan implementation/assets are pushed to the work branch, but Pages publishes main. Previous PLAYER QA READY wording incorrectly implied public availability. This is not a missing work-branch implementation or a cache diagnosis.

## Change

DEV review now explicitly labels the existing actor control `プレイヤー表示`. Its button displays `Aidan A1（仮プレイヤーへ切替）` or `仮プレイヤー（Aidan A1へ切替）`, identifying both current actor and next action. During loading it says `Aidan A1 読込中`. Button press/tap switches the actual player without moving its navigation or collision anchor. No sprite files, movement code, battle code, main, story or Pages configuration were changed.

## Verification

The read-only PNG audit passed 20/20 including recorded SHA, RGBA and real alpha. Browser tests cover 1280×720, 844×390 and 390×844: all four idle directions, all sixteen rendered walking frames, actual mouse/touch toggle, keyboard facing, registered foot anchor and review/save lifecycle. Normal/Raider tests cover COMMAND, enemy motion followed by DEV instant kill, KO/Victory race protection and HP 1250. Test logs accompany this report. Zero image HTTP errors, JS exceptions or console errors in these local browser runs.

## Publication blocker

GitHub Pages: NOT YET POSSIBLE for Aidan PLAYER QA. Pages definitively deploys main. User approval is required before integrating the work branch into main; no main merge or Pages source change was performed. Network destinations were saved through the setup skill and subsequently became reachable; no remaining network blocker was observed. UI implementation commit: `6cb7ee9442442b27802ec1939734456a9a319fe3`, normally pushed and verified against remote.

PLAYER QA READY on the work branch; public PLAYER QA awaits user-authorized integration/deployment.

Navigation suite passed all three viewports: 20 rendered bridge crossings per viewport, actual click/tap destinations, arrows/WASD, cancellation, wall/corner handling, NPC interactions and save isolation. No app errors.
