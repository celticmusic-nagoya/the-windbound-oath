# Startup cancellation diagnosis (independent)

Exact baseline main3d1794340feb7210f209ae4beea2dc879034e92f and candidate1c5bda76a0f90854db606ec7b19cc5553741430a. Both cases use exact revision content for the only differing production files(index/DEVJS/CSS); all other production files were independently verified identical between revisions.

**Confirmed baseline startup resource replacement, not a WALK02-specific exception.** Own serial m55 at1c5 returnedFAIL solely for originalRaider still `goblin_raider_battle_idle.png` net::ERR_ABORTED; all1197functional slots passed. Own m56 returnedPASS/215checks. The original FAIL remains unchanged in independent-final-qa.

Boot-only deterministic HTTP probe delayed delivery of that original still3seconds. It did not call route.abort, inject scripts, openDEV, setflags or writeSAVE. Both main andcandidate canceled the old request naturally(main1500.47ms,candidate1034.94ms), while documentbecamecomplete and the real #raiderSprite img loaded replacementmotion idle02/03 withnaturalWidth584. No pageerror. Fulltimed request/response/failure events andDOMsnapshot inresults.json. ExistingDOMContentLoaded v54forceEnemyArt→BattleActorState.sync/paint→BattleMotion.start changes the still to installed idle frames; static code agrees with observed replacement.

A future test harness may classify ONLY this precisely evidenced canceled unused boot resource, with explicit replacement-loaded and beforeDEV checks; no broadERR_ABORTED filtering or dropping real image failures. This diagnosis is not itself a green rerun of m55 and does not erase the initial aggregate failure. Final requiredtest gate awaits repaired strict harness and independent exact-head confirmation.

Initial scratch attempt failed before diagnostic setup because local variable shadowed Python http module; source/log retained, corrected. Browser nowclosed. No production/main/PR changes performed.
