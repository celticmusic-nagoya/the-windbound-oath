# MORWEN-WALK-ASSET-07B

Status: **reference/production-preparation deliverable complete; formal walking sequence BLOCKED**. Two generation attempts made, then stopped. One six-cell draft rejected; one source-based single-pose candidate retained but fails production technical gates. No accepted walk frames; no independent right-side sequence. Next asset-production handoff can use the package; real-contact Export-06 cannot proceed.

## Branch and provenance

- Base `2cbbc631426e240eeb9a2f03257d19f913c31c46` verified against PR #227 source branch on GitHub.
- Isolated worktree `/workspace/morwen-walk-asset-07b`; branch `feature/morwen-walk-asset-07b`.
- Read AGENTS.md, selected registry, HD director decisions, source-generation guide and ART-74 historical specs. Source design for this task is exactly the four HD v2 pixel originals explicitly selected by the user. No superseded chibi artwork was used as a generation reference or promoted to canon. No global canonical designation changed.
- Only new task-specific asset/QA paths; PR #225–#227 worktrees and existing files untouched. No main merge, formal adoption, runtime integration or publication.

## 1. Official references: retrieved and verified

Retrieved all four original PNGs directly from GitHub Git Blob API at the pinned base (not just a local filesystem assertion). Blob IDs and exact expected/downloaded hashes, sizes, modes and byte counts: `SOURCE_DOWNLOAD.json`. Registry source is `data/morwen-hd-canonical-v2.json`.

| Original | SHA-256 result | Native size |
|---|---|---|
| pixel/front.png | PASS `d6fe876bf997dda37aa513519f940f5560ea21ec2ac8332a05c1e1e82d2c2b5a` | 1024×1536 RGBA |
| pixel/left.png | PASS `5d0608bf2d60708325b0cdbb0a75a160e7153365cb402d5b33183c608c7eccf8` | 1024×1535 RGBA |
| pixel/right.png | PASS `f2a485d2d9591cb4cdc5b5d7aabb87f539546b53899bbb1dfd8410ba99c060c7` | 1087×1446 RGBA |
| pixel/back.png | PASS `64bc5cbe418d39255d28830e317c8b22fe19cb7fa5da626281fa9bca9b91e03f` | 1086×1448 RGBA |

All downloaded bytes were compared to registry SHA. Package embeds these same PNG bytes using ZIP_STORED; originals were not decoded/re-encoded, resized, cleaned or overwritten. Protected manifest **17/17 PASS** (`PROTECTED_SHA.json`). Originals have genuine outer alpha=0 and many partially transparent subject pixels; preserve them. Binary-alpha requirements apply to new walk derivatives.

## 2. Visual audit / historical specification

`VISUAL_AUDIT.md` records actual inspection of all four originals: purple blunt bob, gold glasses, hat shape/pendant and direction-dependent ornaments, layered purple/gold costume and robe patterns, stockings, buckled boots, shoulder/ear details and right-side bag/strap asymmetry. Original proportions are preserved as a visual constraint; no hidden joint coordinates were guessed. This is Codex self-review, not independent art approval.

Read ART-74A/74F README, phase report and build metadata at `cd5525c2dc122ac0cc3a199db15c868d3dce5b44`. 74F uses 12 frames / 840ms / 96×128 or 48×64 and a historical mirrored pipeline; it is not the requested HD six-frame source. It was used only to understand arm/cloth phase sequencing. Current left six-frame nominal 10fps/F1–F4 contact guidance comes from the later HD DEV director decision. Right 10fps is a task proposal and must be independently drawn. Never transplant the old 74A emblem deletion: the requested HD left visibly retains an emblem.

## 3. Produced deliverables

Under `assets/candidates/morwen-walk-asset-07b/`:

- `REFERENCE_PACKAGE.zip`: four original PNGs byte-preserved, source receipt, pose specification and production manifest. All four embedded SHA values reverified.
- `POSE_SPEC.md`: left/right six-frame proposed gait, 10fps schedule, target canvas/anchor, preservation rules, ART-74 applicability, production/measurement gates and two alternative methods.
- `PRODUCTION_MANIFEST.json`: 12 distinct frame IDs, direction, proposed pose, anatomicalFoot/contactPhase/stanceId, actual null timeMs plus separate planned targetTimeMs, imagePath/imageSHA256 and anchor. Proposed timing is explicitly not captured timing. Unmeasured actual anatomical assignment/phase/contact/anchor/world coordinates remain null. F01 points only to the unapproved technical-fail candidate; the other 11 image paths/hashes remain null. Target paths/anchor are separate planning fields.
- `rejected/attempt01_left_sheet.png`: preserved first model output, not six accepted frames.
- `candidates/left_F01_attempt02.png`: preserved second model output, UNAPPROVED and technical FAIL.

SHA and byte sizes of delivered assets: `DELIVERABLES.json`. No cropped sheet cells, mirrored right sprites, duplicate held frames or shifted stills were created as substitute walking assets.

## 4. Generation attempts and stop

Tool: `image_gen.imagegen`, local reference paths and `transparent_background=true`. Model outputs copied without image edits from `/workspace/generated_images/` into the new task asset paths; original generated files retained. No external Runway/Weave generation or additional service upload performed.

1. **Whole six-frame left sheet** (left/front/right originals supplied): requested uniform 3×2 grid, same detailed costume, six distinct contact/loading/passing poses and alpha exterior. Output 1536×1024. FAIL: sheet rather than individual 1200×1600 PNGs; reduced cape/ornament fidelity and near-repeated pose pairs; no proven alternating anatomical lead. Alpha has 360,942 partial pixels and zero opaque pixels. `ATTEMPT01_QA.json`.
2. **Changed method, single original-based lower-leg edit** (left original only): protected costume/upper body and independently exposed far leg instead of redrawing a full sequence. Output 1025×1535, substantially closer to the source appearance. FAIL technical: wrong canvas, 578,109 partial-alpha pixels; anchor and anatomical contacts unmeasured; full sequence absent. Independent design/asymmetry acceptance NOT_RUN. `ATTEMPT02_QA.json`.

Generation stopped at **2/2 attempts**. Structural limitation: unconstrained raster generation does not guarantee exact canvas/alpha, protected source-pixel fidelity, unique gait states or anatomical correspondence. Avoid another near-identical prompt. Alternatives: controlled layered artist/manual pose construction, or a verified split-part 2D rig with authored gait/root data and deterministic rendering. Both are specified in POSE_SPEC.md.

The first live preview was initially described as an opaque background; pixel audit corrected this: it has transparent exterior pixels and partial-alpha subject pixels. That initial visual interpretation is not retained as a QA fact.

## 5. QA and commands

Retrieval: `git fetch origin feature/morwen-motion-source-05`; for each registry path, `git rev-parse 2cbbc631426e240eeb9a2f03257d19f913c31c46:<path>` resolved its blob; `gh api repos/celticmusic-nagoya/the-windbound-oath/git/blobs/<gitBlob>` fetched base64 content, decoded without image re-encoding and checked SHA. Exact blob IDs: SOURCE_DOWNLOAD.json.

```sh
python tools/character-asset-studio/qa/morwen-walk-asset-07b/verify_package.py
python tools/character-asset-studio/pipeline/cas.py protect-verify
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_*.py' -v
node --test tools/character-asset-studio/tests/*.cjs
node --test tests/*.cjs tests/field/*.test.js
python -m unittest discover -s tools/character-asset-studio/pipeline/tests -v
```

| QA | Result |
|---|---|
| GitHub original SHA / reference package bytes | PASS 4/4 |
| Package/manifest/unknown/contact-binding checks | PASS 9/9; production status remains blocked |
| Protected canonical SHA | PASS 17/17 |
| Candidate canvas and binary alpha | FAIL both attempts |
| Full formal design/asymmetry, 12-frame uniqueness/loop | NOT_RUN / BLOCKED; one provisional pose is insufficient |
| Actual anchor/contact/world drift | NOT_RUN; unmeasured values null |
| QA unit tests before/after | PASS 37/37 → 37/37 |
| Studio Node before/after | PASS 19/19 → 19/19 |
| Repository regression before/after | FAIL 52 pass / 8 fail, identical IDs |
| Pipeline before/after | FAIL 55 pass / 3 fail, identical IDs |
| Human adoption / actual Android / browser E2E | NOT_RUN; no runtime/UI integration |

Verifier exit **2** intentionally reports task BLOCKED; `PACKAGE_QA.json` separates valid-package PASS from candidate-production FAIL. Full regression commands, stdout/stderr and exit codes: `REGRESSION_COMMANDS.json`; failing ID differences: `REGRESSION_DIFF.json`. No new failures. Existing eight runtime-fixture failures and three strict archived-PNG SHA failures reproduce on this task's untouched base and final state. Prior Source05 pixel-equivalence diagnosis is retained as prior evidence, not silently rerun/claimed as a new analysis. No existing test assertion or expected SHA changed.

## 6. Next stage

**Asset-production handoff: ready via reference package/spec. Formal left/right six-frame delivery: BLOCKED. Real-contact Export-06: NOT_STARTED / not ready.** Need twelve independently drawn, design-approved frame candidates; common canvas/alpha and measured anchors; anatomical phase/contact/stance IDs; actual producer root transforms and source hash binding. Director adoption and Android remain separate gates. No source PNG or prior PR was altered to force readiness.
