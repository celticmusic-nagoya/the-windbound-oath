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
