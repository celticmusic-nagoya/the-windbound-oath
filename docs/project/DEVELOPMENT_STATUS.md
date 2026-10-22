# THE WINDBOUND OATH — DEVELOPMENT STATUS

Status: **PROPOSED — Claude-reviewed revision of the ChatGPT draft.**
**Snapshot only. As of 2026-10-22 (JST), checked against GitHub that day.** Refresh from GitHub before any decision. This file is not an automatic source of truth and authorizes no merge, deletion or implementation. Tags are defined in `PROJECT_MASTER.md` §0; QA vocabulary in `AI_COLLABORATION.md` §4.

## 1. Verified main
| Item | Value |
|---|---|
| Game repository | `celticmusic-nagoya/the-windbound-oath` |
| `main` HEAD | `081111ed848a54e4c0b70894a1c41205cf6642f3` — merge of PR #44 (2026-10-22 05:32:55Z, merged through the owner's account) |
| Open PRs | 0 |
| Open Issues | #5, #7–#13, #15–#21, #37 |
| Branches | 267 on 2026-10-22 (266 at the time of the classification, plus one new) |
| Branch protection / required checks | none. The only check-runs on the `main` HEAD (`build`, `deploy`, `report-build-status`) appear to be the GitHub Pages deployment, not game tests |
| Recently merged into `main` | PR #42 (F-E2 village ↔ Sunlit Path) at `900e5387`, PR #43 (protocol ACTIVE), PR #44 (height Phase 2 design docs) |
| Closed **unmerged** on 2026-10-22 (tidy-up; branches kept) | PR #41 (Fiona idle v3), PR #36 (Lou-only faint), PR #14 (protocol v2) |

## 2. Workstreams
| Workstream | State | Tag | Evidence and next action |
|---|---|---|---|
| Height Phase 2 design | Docs merged. Runtime pieces, manifest, maps and assets: not approved | design `CONFIRMED` (spec header: author approval 2026-10-21 23:10); merge `IMPLEMENTED` | PR #44. No independent (Codex) QA record on the PR; who approved the merge is not recorded on the PR (`UNKNOWN`). Android real-device check `NOT_RUN` |
| Fiona idle v3 | **HOLD — independent FAIL unresolved. Do not merge** | `IN_PROGRESS` | Codex independently reported two 320 s soak FAILs at `320ba8ca…` with a stall of about 7.9 s. The Codex report itself was not found in the handoff repository when this was written (`UNKNOWN` link). Diagnostic branch `feature/fiona-idle-v3-reqa-fix2-20261022`, head `64a8dac75295139835bafaa53a68d29ffd0e36ec` (tested code SHA `09bca93c…`; head adds two documentation files). Claude's own runs pass and could not reproduce the stall, so the cause is unknown. Hand-off comment: PR #41, comment 6334738480. **Next: Codex independent retest of `64a8dac7…`** (320 s soak at least twice; the stall layer W/T/R/D that the soak now prints; strict negatives) |
| Fiona trace analyzer (stall vs state skip) | Candidate for independent QA | `IN_PROGRESS` | In the same branch. Verify strict mode and the 7/7 negatives on the fixed SHA |
| `ally_motion_p3` | Intermittent. Cause found: the first use of single still images (e.g. Lou heal) loads late under load and races a fixed +250 ms sample (4 of 16 runs failed under load; 0 of 28 without) | `IN_PROGRESS` | `docs/battle/qa/fiona-v3-stall/README.md` in the branch above. Preloading those images is a **proposal** needing approval; the test assertions and timeouts are unchanged |
| BG (battle backgrounds) | BG-01 main background is on `main` (PR #1). The WIP commit `be030c4` (BG-01 fore, BG-02, BG-03 adoption, Raider wiring; commit message "WIP (local only)", 22 files, no QA) is only backed up | `IN_PROGRESS`, not integrated | `backup/bg-adopt-be030c4-20261022` = `be030c405d4a36e0f3da72abf2d1401a0d100f9c`; `backup/bg-adopt-uncommitted-20261022` = `c2e9a0c1c065bb071b899910996fceb4ff835edf` (adds the uncommitted `tests/battle/bg02_bg03_background.py` change). Review the diff, assets and rollback before any integration; the base is 26 commits behind `main` |
| Aidan idle v1 | Branch exists | `IN_PROGRESS` | `work/aidan-idle-v1` (1 commit ahead, 14 behind). Visual approval and QA state were not found (`UNKNOWN`) |
| Title screen (Issue #17) | Independent QA **FAIL**, no merge | `IN_PROGRESS` | `feature/title-01-new-title-screen` at `7b724c10…`: 80 PASS / 6 FAIL on the original TITLE-01 test; regression suspects; unchanged since 2026-10-19 |
| Emma portrait (#19), Fiona/Lou portraits (#16), startup race (#20) | Each independently **CONDITIONAL**; none merged. Review separately, no blanket PASS | `IN_PROGRESS` | #19 `f4456a82…`; #16 `5d915ed9…`; #20 `a2217208…` |
| Scene lifecycle 03 (Issue #12) | Integration **BLOCKED**; latest independent QA CONDITIONAL (stage 15 local feature PASS, one UI regression FAIL) | `IN_PROGRESS` | `fix/scene-lifecycle-03-stage15-load` at `cc3aad4c…`. Verify the latest state before acting |
| CONTINUE / SAVE-LOAD (Issue #21) | Design done, implementation not started; the failing pending test `m36_continue_cold_restore.py` shows 10 FAIL (red test, expected) | `IN_PROGRESS` | `feature/continue-save-restore-design` at `d02045be…`. The save format must not change |
| Aidan expressions v1 (Issue #15) | Independent QA CONDITIONAL; asset adoption and UI implementation not approved | `PROPOSED` | Issue #15 |
| Boy swordsman NPC (Issue #18) | Merged early by user instruction (PR #22, 2026-10-19). Independent QA stayed CONDITIONAL; Android real device `UNVERIFIED` | `IMPLEMENTED`; QA verdict CONDITIONAL | Issue #18 |
| F-E2 village ↔ Sunlit Path (PR #42) | Merged on 2026-10-22 under a per-PR author exception. The independent QA verdict **stayed CONDITIONAL** (not changed to PASS) | `IMPLEMENTED` | PR #42 comment of 2026-10-22 03:50Z; Android real device and CI: none |
| Lou-only faint | Canon adopted (ADD-001). Code PR #36 closed unmerged; difficulty impact unapproved (past 50-battle comparison: main 50 wins / 0 losses, PR 26 / 24) | canon `CONFIRMED`; code `IN_PROGRESS` | `feature/lou-faint-recovery` at `d7725abd…` (3 ahead, 22 behind). Needs a difficulty decision, a new PR and independent QA. General stun/faint stays `PROPOSED` (not adopted) |
| AI handoff protocol | v1 is ACTIVE (PR #43). v2 (PR #14) closed unmerged: it changes authority and automation gates and needs manual approval | v1 `CONFIRMED`; v2 `SUPERSEDED` as a merge candidate | Do not apply v2 text as it stands; compare with the current files first. Issue #13 (auto-approval intent, 2026-10-18) is still open |
| Official lore registry (Issue #37) | v5.0 master and the addenda are registered in the private repository; the hash `e6f7331b…bf49` matches | `CONFIRMED` | `CANON_STATUS.md` is dated 2026-10-20 and partly stale (see `PROJECT_MASTER.md` §6) |
| Android real-device QA | Not performed | `NOT_RUN` | Emulation or desktop must not be reported as physical verification |

## 3. Branch inventory (stale baseline)
- The Claude classification of 266 rows: A 128 (integrated into `main`), B 12 (unmerged candidates), C 10 (decision pending), D 29 (QA), E 80 (rollback), F 7 (in use). It was prepared **before PR #44 merged** and before the newest branches; it must be recomputed against the current `main`.
- Within A, 98 branches are estimated to be Claude-owned and 30 await owner confirmation. Ownership is an estimate: Codex also pushes under the owner's account.
- A category does not prove ownership, absence of dependencies or safety to delete. **Do not delete any branch** without explicit authorization and a preservation check. Keep `rollback/*`, `backup/*`, QA, Codex, asset and unique-commit branches.
- Open question for the author: how long rollback branches are kept.

## 4. Next priorities (proposals, not instructions)
1. Codex independent QA of the Fiona diagnostic head `64a8dac7…`: 320 s soak at least twice, the printed stall layer, strict negatives, and the first-use image race. Then the author decides whether Fiona may integrate.
2. Review the BG backup against the current `main` (diff, dependencies, assets, rollback, tests, order). Review only; no merge without the gates.
3. Reconcile the stale project documents listed in `PROJECT_MASTER.md` §6, in separate docs-only PRs. The private lore files belong to the handoff repository.
4. Recompute the branch classification on the current `main`, resolve owners and unique commits, then ask the author before any deletion.
5. Decide the open questions: Lou-faint difficulty, `ally_motion_p3` (preload in the product, or change the test premise), whether the Issue #13 cleanup approval still stands, and whether docs-only follow-up commits may keep a QA verdict.

## 5. Reporting requirements
Every status update gives: the as-of time, the `main` SHA checked, the fixed feature SHA (and the tested code SHA if different), the QA author and environment, the approvals with their evidence, and the unresolved blockers. A PASS in one environment does not cancel a FAIL in another.
