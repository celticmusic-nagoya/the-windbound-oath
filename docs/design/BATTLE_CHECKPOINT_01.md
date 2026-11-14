# BATTLE-CHECKPOINT-02 — dual hidden auto slots (approved design; restoration NOT implemented)

## Storage
- Manual SLOT 01–20: untouched, visible only in manual SAVE/LOAD.
- Hidden AUTO SLOT 21: last **verified recoverable safe point** (not merely any map-load event).
- Hidden RETRY SLOT 22: pre-battle snapshot, optional; only if the exact battle entry state and field context can be restored.
- Never place either hidden slot in the ordinary manual list. Do not reuse or overwrite numbered manual keys.
- Persist with separate versioned keys and validate before replacing a previous known-good record. Invalid snapshots must fail closed.

## Safe-point gate
- No battle in progress, no pending forced encounter, map/scene load completed, no active transition.
- Player can move away, heal, change equipment, or access an alternate route; reject unavoidable encounter loops.
- Safe-point must have enough recoverability to escape a fatal state. If no such state is available, retain the prior valid safe-point.
- Map entry alone does not prove safety. Avoid writing on every map load.
- Never auto-heal without separate game-balance approval.

## Game Over UX
1. RETRY: SLOT 22 prebattle (optional; may repeat dangerous battle).
2. CONTINUE: SLOT 21 safe-point (escape from dead-end).
3. LOAD: existing manual save selector.
4. TITLE: clean title return.
- RETRY and CONTINUE stay disabled until full serializer and restore routes pass G1–G4. LOAD and TITLE remain available.
- No Lou time-rewind narrative, no automatic rematch.
- Restore must include field coordinates/scene, HP/MP/TP, inventory, equipment, party, flags, event triggers, and pending-encounter suppression.

## Acceptance
- Normal, forced, Raider battles; repeated defeats; corrupt/full storage; cross-map return; 20 slots unchanged; Android mobile QA.
- Check actual game engine state before wiring auto-save; existing v30 manual payload is insufficient for exact battle-state restoration.
- No main merge or publication without explicit approval.
