# Aidan PLAYER QA display control follow-up

Start: `51c6d811ed944492f1d98a0df5a4e4567a75d8a4`.
Branch: `work/lind-step9-11-prep`. Main remains `51cf09258b36c47ba1b9dc8954f385cbeaf018d9`.

## Source / remote diagnosis

Direct `git ls-remote` and an explicit branch fetch confirmed all 20 A1 PNGs and the DEV actor implementation at the remote branch start commit. The initial stale tracking ref was misleading: `remote.origin.fetch` fetches main only. The existing toggle was implemented, rather than only described in the report, but was labelled `Aidan 正式` / `Aidan 仮表示`. Main has neither the field actor script inclusion nor A1 assets. A work branch push alone does not establish Pages publication.

The public Pages URL and repository Pages API both returned proxy tunnel 403. Consequently the actual Pages source branch and live deployment are NOT VERIFIED. Do not describe this as a browser-cache issue or assert a main-only Pages setting without further evidence. Previous PLAYER QA READY wording did not establish public availability.

## Change

DEV review now explicitly labels the existing actor control `プレイヤー表示`. Its button displays `Aidan A1（仮プレイヤーへ切替）` or `仮プレイヤー（Aidan A1へ切替）`, identifying both current actor and next action. During loading it says `Aidan A1 読込中`. Button press/tap switches the actual player without moving its navigation or collision anchor. No sprite files, movement code, battle code, main, story or Pages configuration were changed.

## Verification

The read-only PNG audit passed 20/20 including recorded SHA, RGBA and real alpha. Browser tests cover 1280×720, 844×390 and 390×844: all four idle directions, all sixteen rendered walking frames, actual mouse/touch toggle, keyboard facing, registered foot anchor and review/save lifecycle. Normal/Raider tests cover COMMAND, enemy motion followed by DEV instant kill, KO/Victory race protection and HP 1250. Test logs accompany this report. Zero image HTTP errors, JS exceptions or console errors in these local browser runs.

## Publication blocker

GitHub Pages remains NOT YET POSSIBLE to confirm from this environment. Required network domains `api.github.com` and `celticmusic-nagoya.github.io` were saved in an environment configuration draft; applying them requires reviewing/saving the environment settings and publishing the environment. This does not change repository Pages settings. If Pages deploys main, user approval is still required before integrating this work branch into main. No main merge or Pages source change was performed.

PLAYER QA READY on the work branch; public PLAYER QA is pending deployment verification.
