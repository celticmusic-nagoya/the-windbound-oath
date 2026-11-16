# THE WINDBOUND OATH — AI development handoff

> Coordination entrypoint. Read current `main:AGENTS.md` first, then this file, then `Blender.md` for Blender tasks. This branch is a proposal until merged; other agents will not automatically see it from main.

## Authority and precedence
1. Director's explicit latest approvals; private canonical lore repository main (if authorized and available).
2. Current public repo main `AGENTS.md` and linked policy, especially `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md`.
3. Approved source asset bytes and manifests, SHA-locked.
4. Task-specific docs, PRs and candidate branches (not canon).

If private canon cannot be accessed, mark canon-dependent work `BLOCKED / CANON_SOURCE_UNAVAILABLE`. Do not infer official design or dimensions.

## Work lanes
| Lane | Ownership | Current constraint |
|---|---|---|
| WORLD | terrain, coastline, river, roads, geography | Codex candidate PR #346 is paused; inspect before new work |
| HOME | Aidan hero home, independent asset | no overwrite without provenance review |
| BUILD | modular buildings, bridge, masonry | preserve existing Claude candidates |
| ECO | vegetation, fields, rocks, water embellishments | preserve existing Claude candidates |
| INTEGRATION | interface contracts, source tracking, runtime adapter | ChatGPT isolated branch |
| QA | independent G1/G2/G3/G4 evidence | independent of implementing lane |

## Current references
- Approved Lind illustration: PR #344 / commit `dc17dd4846f35ea1f5dea25168eec9ddb50a3838`, `assets/sources/lind-world-20261116/original.png`, SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`.
- Spatial contract: `docs/production/LIND_BLENDER_SCENE_INTERFACE_V1.md`, `docs/production/lind-new-world-topology.v1.json`.
- Technology plan: `docs/production/LIND_ENVIRONMENT_VFX_TECH_RESEARCH_20261116.md`.
- Runtime feasibility: `docs/production/LIND_BROWSER_RENDERER_FEASIBILITY_20261116.md`.
- Ownership / QA: `docs/production/LIND_CHATGPT_TAKEOVER_20261116.md`.
- Blender instructions: `Blender.md`.

## Shared task protocol
Before: read current main policy and task branch; check existing attempts, PRs, assets, provenance, CI; declare scope, owning lane, expected outputs, exact SHA, quality gates and stop conditions.
During: separate candidate branches, immutable canonical sources, deterministic parameters and seeds, no overlapping edits, no false claims about tool execution.
After: publish commit SHA, PR, workflow run, artifacts, image renders and G1–G4 status (PASS/FAIL/BLOCKED/NOT_RUN), plus next reproducible command. `CI success != art PASS`.
Never merge to main, publish, delete, or replace canon without explicit director approval.

## Automation reality
GitHub Actions can execute checked-in deterministic Blender scripts and tests; it cannot autonomously act as a visual AI critic without an actual authorized AI evaluation service and evidence. No API keys or AI provider access are assumed. Art review remains separately required.

## Current status
Source-review Blender CI run #43848242090 SUCCESS, including source image and empty semantic scene checks. This is NOT actual village mesh or art acceptance. WORLD geometry, G2 and Android G4 remain unverified.
