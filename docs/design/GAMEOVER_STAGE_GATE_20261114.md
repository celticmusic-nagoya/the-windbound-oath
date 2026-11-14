# GAMEOVER-01 — Stage-gated defeat handling (director-approved design, implementation pending)

Status: DESIGN ONLY / NOT IMPLEMENTED / QA NOT RUN
Date: 2026-11-14

## Director-approved behavior
- Before village attack: wooden training and village-outskirts introductory encounters do not cause GAME OVER; retain safe retry/recovery.
- Beginning at village attack and continuing through Moss Forest, ancient altar and later: party wipe causes GAME OVER.
- GAME OVER actions: load last valid save; return to title. No automatic resurrection.
- Create a pre-attack autosave only after verifying safe save/restore conditions and old SAVE compatibility.
- Preserve canon: Aidan/Fiona/Morwen age 18; prologue ends on fortress arrival; Liam recruitment conversation on hold.

## Current implementation findings (main, checked 2026-11-14)
- js/prologue-combat.js: ordinary defeat recovers party HP (source-findings QA report).
- js/battle-loading.js: Raider rematch directly restarts the same battle after Lou's rewind.
- docs/qa/evidence/directive-25a/source-findings.md: confirms existing recovery behavior.
- AGENTS.md: canonical source is private handoff main, not public repository; do not overwrite protected narrative or balance.

## Required implementation investigation
1. Read current private canon v5.0, CANON_ADDENDUM and CANON_STATUS; identify story stage / attack start flag and any Lou-specific mandatory story event.
2. Trace all defeat paths and map-entry / save-load APIs; identify old save schema and valid checkpoints.
3. Introduce pure stage-gate decision function based on existing canonical progression state, not new guessed numeric story stages.
4. Route eligible party wipes to a single terminal state; stop timers, disable battle inputs, and prevent duplicate event dispatch.
5. Add responsive GAME OVER UI with two functional actions; ensure reload is transactional and title return cleans up state.
6. Regression test pre-attack recovery, attack and Moss Forest wipes, Raider-specific override, old saves, no-save state, double wipe, mobile touch and accessibility.

## Conflict to resolve before gameplay code change
The currently implemented Raider rewind is incompatible with unconditional GAME OVER from village attack. Director's later explicit instruction takes precedence, but review canon and ensure the narrative Lou sequence is preserved without silently inventing replacement dialogue.

## Gates
G1 canon and scenario compatibility; G2 UI quality; G3 save/load and state integrity; G4 browser and Android behavior. Do not merge or publish until PASS.

## 2026-11-14 follow-up: save/title API audit (verified)
- `js/save-continue.js`: `SaveContinue.start()` only works in `phase==='TITLE'`. Calling it directly from an active GAME OVER battle returns false. A transition to title or a dedicated transactional reload API is mandatory.
- `js/title-screen.js`: `TitleScreen.begin(cb)` initializes the title UI and `TitleScreen.dismiss()` hides it. No public `show()` or `returnToTitle()` API exists; do not call private functions from the battle layer.
- `SaveContinue.inspect()` checks existing save validity without overwriting it. It does not itself create an autosave.
- `js/prologue-combat.js`: normal recovery currently fires when **either** ally is at HP 0, not when the whole party is wiped. New GAME OVER must test both allies down, respecting the solo `attackGob1` encounter.
- Raider defeat currently rewinds on either ally at HP 0; director-approved GAME OVER requires an explicit precedence rule and regression test. Do not silently remove Lou's canonical support/faint narrative.
- `js/gameover-screen.js` and CSS exist as isolated components but are not loaded by `index.html`. No live UI claim is justified.

## Safe next implementation gate
Implement a public, tested title-return/reload transaction first. Only then wire the game-over UI and normal/Raider defeat paths, with battle-generation cancellation, input locking, no-save fallback, and a pre-attack save checkpoint. No destructive save rewrite or speculative title API.
