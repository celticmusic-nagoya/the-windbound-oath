# THE WINDBOUND OATH — Parallel AI asset production v1 (proposal, noncanonical)
Status: DRAFT / production orchestration specification. Does not authorize asset adoption, main merge or publication.

## Objective
Produce independent, reviewable finished-quality candidates concurrently, without forcing unrelated assets to wait for the Aidan masonry work. Reuse existing Blender/GitHub Actions; no paid AI API dependency.

## Six logical roles (not six running agents)
1. ChatGPT / director coordination: canonical lookup, asset queue, acceptance criteria, G1/G2 review and release recommendations.
2. Architecture & ruins producer (Claude session): buildings, stone modules, openings; isolated branch and render evidence.
3. Vegetation & nature producer (Claude session): grasses, ferns, flowers, rocks; isolated branch and render evidence.
4. Character head/face producer (Claude or Codex session): face, eyes, hair, expression and 4-direction silhouette; isolated character branch.
5. Character body/costume producer (Claude or Codex session): anatomy, clothing, equipment slots and deformation; separate character branch.
6. Integration & independent technical QA (Codex session + GitHub Actions): Blender reproduction, mesh/UV/alpha, scale, game-size tests, regressions. GitHub Actions is the executor, not an AI that makes art judgments.

Each Claude/Codex session must be started or connected by an authorized user. No unattended AI work is implied. Roles may be reassigned to available sessions. Never let multiple agents edit the same branch or shared canonical files.

## Independent work packages
- MAP-VEG-01: 3D modular grasses, ferns and flowering plants (first parallel package).
- MAP-RUIN-01: ancient ruins modular kit; **canonical placement and architecture remain BLOCKED until references are verified**.
- MAP-STONE-01: natural rocks, mossy rocks, bank stones.
- MAP-PROP-01: rural fences, wheels, barrels, wood piles.
- CHAR-FACE-01: face/head/hair and direction sheets; separate branch from body.
- CHAR-BODY-01: body, rig, costume and equipment; separate branch from face.
- CHAR-ASSEMBLY-01: integration only after matching interfaces and G1/G2 evidence.
Aidan masonry ART-02 remains a separate ongoing line, not a prerequisite for vegetation.

## Required package contract
Each task has task_id, asset_id, producer, reference_canon_ref+hash, reference_candidate_ref+hash, branch, input hashes, Blender version, seed, generation script, manifest, output dimensions and camera, materials and licenses, dependencies, review images, 48px/96px previews where relevant, and G1/G2/G3/G4 statuses.
Directory: assets/candidates/<task_id>/<candidate_id>/ ; script: tools/map_blender/ or tools/character_blender/ ; QA evidence: docs/qa/ .
Use draft PR, not main. Source files in separate package dirs; immutable accepted inputs. No unverified download/license. Do not commit restricted reference images to public repositories.

## Quality gates
G1 canonical consistency, G2 independent art review, G3 Blender topology/render/material/alpha technical checks, G4 in-game and Android performance. CI PASS never means G2 PASS. Final adoption requires all PASS and explicit director approval. BLOCKED where canon dimensions/camera unavailable. Keep cumulative causal retry ledger; after two failures for same cause/method, stop that method family and switch structurally. Do not reset failures by renaming.

## Parallel operation
(1) Confirm canon and source references; (2) assign disjoint tasks/branches; (3) create finished-quality master assets; (4) Blender CI with reproducible seed and source hashes; (5) independent visual review at final display scale; (6) only then integration review. No automatic main merge or publication.

## First execution tranche
MAP-VEG-01 and CHAR-FACE-01 can start in parallel after canonical references are verified; ART-02 continues independently. Map vegetation should first prove a single finished-quality plant family (not a low-quality placeholder) with consistent 4-view and 48/96px preview, then expand to related variants using the same validated generator and material library. Character face and body should share a locked interface contract before modeling starts.
