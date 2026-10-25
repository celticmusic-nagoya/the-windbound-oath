# Issue #20 STARTUP-RACE — DIRECTIVE-22A/B/C/D

Base: `6312ad79ca4f76ded8ed764a9bdb7cbe7db800bf`. Branch: `fix/issue20-startup-race-21b`.
Historical fix reused: `a2217208edadea71525b30123d535ab0b3814221` (active FieldTalk protection), adapted to current S2/coordinator APIs rather than importing obsolete runtime code.

## Ownership and final behavior

- LoadCoordinator remains the owner of boot/LOAD generations. RildeVillage.startOpening without an explicit owner uses boot; stale explicit owners are rejected before story mutations. Boot cancels an older pending map through the existing S2 mechanism.
- Initial map and optional narration use the existing S2 enterCount plus coordinator token. A new map/boot/LOAD invalidates the old delayed narration. Narration is no longer part of readiness: boot becomes ready after map commit, not after the optional existing 350ms narration timer. No new fixed wait was added; test-only ready gates are not the product fix.
- One dialogue revision in LoadCoordinator is advanced by actual say/closeDialogue/FieldTalk rendering. Startup narration yields to another dialogue, including one already closed, and checks active FieldTalk/body dialogue state.
- DEV reset without an owner explicitly supersedes boot/LOAD. Internal LOAD reset passes its owner token, validates it and retains ownership. PrologueProgress validates ownership before restoring progress and again at completion. The LOAD ownership check is not bypassed.
- The scheduled DOMContentLoaded initial boot is skipped after a newer DEV owner. Actual unload/pagehide invalidates old work; persisted bfcache retains the same page owner. Browser goto/reload create a separate page realm; tests simulate disposal/new realm, not real browser navigation.
- Booting rejects LOAD. LOADING rejects a second LOAD under the established coordinator exclusion contract; only the most recent *accepted* owner may commit. No concurrent-load queue or unconditional LOAD priority was introduced.
- Existing S2 rollback, explicit retry, map request rejection, original save-byte protection, Loading and COMMAND behavior remain covered by regression tests. Save schema/lore/balance are unchanged.

## Diagnosed failures (kept separate from final PASS)

1. 22A NEW GAME false: fixture omitted real PrologueProgress. Trace showed ReferenceError in flagsNow before map fetch. Production loads that module before the DOMContentLoaded startup callback. Fixture now loads the real module, not a success stub; isolated NEW GAME passed.
2. 22B normal LOAD false: **product-side regression in the unmerged change**. LOAD acquired token 2; internal devResetScreens superseded generation to 3; S2 rejected token 2 as Cancelled map entry. Fixed by explicit owner preservation. Normal LOAD isolated passed with unchanged expectations.
3. 22C devJump missing: fixture extracted the DEV block using the old argumentless reset signature. The actual changed declaration is devResetScreens(ownerToken); devJump itself still takes key. Extraction now matches declaration names independent of argument names/count, requires the block end and devJump declaration, and verifies the evaluated functions' source strings occur verbatim in the product source. Missing declarations fail clearly; no fallback success.

Raw historical FAIL logs and pre-change snapshots remain in independent QA directories; no evidence was overwritten. A local log-summary helper once matched the word FAILED inside a passing test name; this reporting-script error was corrected to check FAIL result lines. The product test process itself exited 0, and all 20 case outcomes are preserved.

## Executed QA in this environment

| Command | Result |
|---|---|
| STARTUP_TEST_FILTER='real devJump' node tests/startup_race.test.cjs | PASS 1/1 |
| node tests/startup_race.test.cjs | PASS 20/20, from the beginning |
| node tests/s2_transition_recovery.test.cjs | PASS 19/19 |
| node tests/common_loading.test.cjs | PASS 17/17 |
| node tests/loading_input.test.cjs | PASS 37/37 |
| node tests/loading_map_readiness.test.cjs | PASS 3/3 |
| node tests/issue51_command_lock.test.cjs | PASS 14/14 |
| node tests/issue54_coordinator.test.cjs | PASS |
| python tests/battle/battle_opening.py --self-test | PASS asset/classifier only |
| Changed JS + HTML inline syntax; git diff --check | PASS |

The 20 cases execute actual coordinator/RildeVillage/FieldTalk/PrologueProgress/S2 and HTML say/reset/DEV destination/LOAD/startAtHome code. They deliberately reverse pending map completion order. Coverage includes NEW GAME, narration priority, dialogue close, DEV vs boot, boot vs boot, LOAD during boot, LOAD vs scheduled narration, old boot reply during DEV then LOAD, unload/new realm, failure retry, fixture extraction integrity, internal reset token equality and stale-reset rejection, LOAD vs NEW GAME/second LOAD/DEV goto/reload, failed LOAD byte/map-flag preservation and retry, real DOMContentLoaded entry and pre-DOMContentLoaded DEV takeover. DOM/network/renderers/timers are simulated; they do not replace actual product state-machine logic. This does not certify every DEV scene or browser-native lifecycle behavior.

## NOT_RUN and residual risks

- Browser regression/rendered desktop/portrait/landscape: **NOT_RUN / ENV_BLOCKED**. Current loopback preflight: PermissionError: Operation not permitted.
- Android physical device: **NOT_RUN / ENV_BLOCKED** (no attached device).
- Historical full m6_talk/browser regressions and Android performance results are not promoted to PASS by the focused simulated FieldTalk close test.
- TITLE-01 remains a separate unmerged implementation; the current main starts from startAtHome, and no title UI was newly implemented/certified here.
- bfcache and real navigation teardown, latency, memory/LRU and long animation soak remain browser/device follow-up checks.

All required executable alternative QA passed, no new P0/P1 or unintended conflict found in this scope. Automatic integration is authorized by DIRECTIVE-22D after checking latest main/head/mergeability.
