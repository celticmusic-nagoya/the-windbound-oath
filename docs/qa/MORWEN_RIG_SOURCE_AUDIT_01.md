# MORWEN-RIG SOURCE AUDIT 01

Status: **SOURCE_CONFLICT_REQUIRES_CANON_CHECK**; no production asset adoption.

## Two distinct source tracks

1. **Main-branch design lock**: `docs/design/MORWEN_V561_CANONICAL_20261108.md` names the director-uploaded `7374.png` (actual JPEG/JFIF 1536×1024, SHA-256 `47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638`). Its binary is not in main.
2. **PR #228 HD walk task**: source receipt `tools/character-asset-studio/qa/morwen-walk-asset-07b/SOURCE_DOWNLOAD.json` identifies four HD v2 pixel RGBA originals, retrieved and hashed 4/4 PASS on its pinned branch. The task's report explicitly states these four were director-selected for that task, and does **not** claim to replace the main design lock.

| Direction | Source path | SHA-256 |
|---|---|---|
| front | `assets/official/characters/morwen/hd-v2/originals/pixel/front.png` | `d6fe876bf997dda37aa513519f940f5560ea21ec2ac8332a05c1e1e82d2c2b5a` |
| left | `assets/official/characters/morwen/hd-v2/originals/pixel/left.png` | `5d0608bf2d60708325b0cdbb0a75a160e7153365cb402d5b33183c608c7eccf8` |
| right | `assets/official/characters/morwen/hd-v2/originals/pixel/right.png` | `f2a485d2d9591cb4cdc5b5d7aabb87f539546b53899bbb1dfd8410ba99c060c7` |
| back | `assets/official/characters/morwen/hd-v2/originals/pixel/back.png` | `64bc5cbe418d39255d28830e317c8b22fe19cb7fa5da626281fa9bca9b91e03f` |

## Implications

- Do **not** equate the JPEG design sheet with any of the four HD PNG originals.
- Do **not** replace the main canonical design lock merely because PR #228 has verified task-specific source PNGs.
- Do **not** claim the source is wholly unavailable: the HD v2 task references are retrievable from the pinned branch; only the named JPEG master is missing from main.
- Do **not** promote rejected PR #228 walk candidates. Its report records two attempts, zero accepted frames.
- The current `MORWEN_RIG_01_PROTOTYPE_SPEC.md` describes a 48×64 candidate track from the main design sheet. HD v2 walking may have different export targets; do not silently combine the two pipelines.
- Before producing a Blender rig, reconcile the exact director-approved **production target** (v5.61 48×64 field sprite vs. HD v2 walk pipeline), source priority and per-frame export geometry with latest current canon and PR decisions.
- Keep both sources and all SHA records immutable, with separate candidate output directories.

## QA

- [x] Main design metadata read.
- [x] PR #228 source receipt and report read.
- [x] Conflicting target assumptions documented.
- [ ] Verify current private canon and latest director decisions.
- [ ] Confirm source-target mapping and rig scale.
- [ ] Blender render and Android QA: NOT_RUN.

No source image, approved sprite, or game code was modified.
