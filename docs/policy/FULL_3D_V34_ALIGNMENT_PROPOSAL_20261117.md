# v3.4 Full-3D Policy Alignment — proposed additive guidance

## 2026-11-19 status reconciliation (historical proposal)
This v3.4 document remains **proposal/history**, not the operative policy. The director's v3.7 instructions, latest main `AGENTS.md`, `docs/production/SESSION_CONTINUITY_INDEX.md`, later approved policy and private canon govern current work. PR #362 updates `AGENTS.md` but does not itself authorize a main merge. The 2026-11-18 provisional-local-coordinate approval permits independent character and environment sculpting, geometry, materials, rigs and real renders **now** with explicitly provisional origin/axes/scale/transform. Unapproved *shared world placement, metric contracts and game integration* remain BLOCKED; they do not block independent asset production. The historical 'conflicts to resolve' section below records 2026-11-17 status and is not a current work queue. Prefer existing owner branches/PRs; new PRs only when safe continuation is impossible. No automatic main merge, canonical overwrite, destructive deletion or publication.

**Status:** PROPOSAL / NON-CANONICAL. This file supplements but does not replace current main `AGENTS.md`, private canon, or director-approved retry policy. It does not authorize canon replacement, main merge, deletion, or publication.

## Evidence and authority (2026-11-17)
- Main `AGENTS.md` (blob `e063d74cc5524794d04de50f1a6d1e3bf9949ad0`) still contains historical 2D / 2.8-head / 2.5D production targets and an old statement that the game is an existing 2D JRPG. These are historical implementation/rollback constraints, **not the new final visual target**.
- Later explicit director approval: full high-quality 3D character and map production. See `feature/morwen-fable-eval-01:docs/production/MAP_TEAM_FULL_3D_HANDOFF_20261116.md`. Preserve working 2D runtime, SAVE, collision, events, touch UI and assets until separately verified 3D migration.
- Existing map-team proposed handoff: `feature/lind-agent-blender-handoff-01:HANDOFF.md` and `Blender.md`. These are **branch proposals**, not automatically main policy.
- The current `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md` is authoritative for retry semantics. Two effective failures stop **the same method family for the same root cause**, not the task or all new methods.

## Shared visual ambition
Benchmark the *craft* of Genshin Impact (color, landscapes), Neverness to Everness (spatial/city presentation), Arknights: Endfield (geometry/materials), and NIKKE (character art), while retaining THE WINDBOUND OATH's independent Celtic/fantasy design. Do not reproduce proprietary designs or assets. The benchmark is an artistic target, not evidence of achieved AAA quality.

## Character / world separation
- CHARACTER owns source-locked character design, four-view consistency, geometry, rigging, animation and character QA.
- MAP owns WORLD/HOME/BUILD/ECO geometry, materials, terrain, water, buildings, VFX and map QA.
- INTEGRATION owns jointly reviewed scale, coordinates, projection/camera, ground contact, shadows, occlusion, collisions, asset exchange and runtime bridge. No metric scale, renderer or camera is implicitly approved.
- Keep high-quality Blender sources separate from optimized WebGL/Android runtime assets. Require actual device profiling before G4 PASS.

## Technology evaluation and adoption
Use https://3dnchu.com/ plus official technical documentation, GitHub, production breakdowns, research, Pinterest and user-provided video as *research inputs*. For each candidate record source, license, compatibility, cost, measurable quality/workflow hypothesis, scope, stop condition and reproducible QA. Within approved non-destructive scope, proceed from research to bounded experiment, implementation and independent QA; do not claim deployment when only a proposal exists. Do not treat rights-unknown assets as production-ready.

## Non-destructive migration checklist
1. Verify latest main policy, private canon availability, source SHA, existing PRs, branch owners and cumulative failure ledger.
2. Define deliverable and G1 canonical / G2 independent art / G3 geometry-render / G4 runtime-Android acceptance evidence. Mark PASS/FAIL/BLOCKED/NOT_RUN independently.
3. Preserve existing 2D behavior as rollback baseline. Prototype 3D runtime adapter under feature flag; no direct replacement until approved and verified.
4. Render and store reopenable `.blend`, output PNGs, manifest hashes, tool versions, settings, tests, license metadata and QA reports as applicable.
5. After two same-cause same-family failures, stop that family, diagnose, and switch to a causally distinct method with an explicit hypothesis. Never reset history by renaming.
6. Use separate branches and Draft PRs; do not merge to main, delete, overwrite canon or publish without explicit director approval.

## Conflicts to resolve in a future reviewed AGENTS.md edit
- Retire the *final-art target* language for 2.8-head field sprites / 2.5D maps without deleting historical implementation notes or rollback assets.
- Reconcile old `Auto-Pilot` language that implies unrestricted main merges with the later explicit approval gate.
- Resolve character reference precedence (v5.61 versus later five-file reference package) against actual original bytes and director approvals before declaring G1 PASS.
- Preserve legacy gameplay and mobile controls until 3D migration G4 PASS.

**This file is policy-alignment documentation only.** It does not imply that Blender rendered a finished asset, that external AI sessions were launched, or that any QA gate passed.
