# DIRECTIVE-21A — common Loading / Issue #60

Base: `dcc36c6725286e89f43b424c8b87165bf59c6bbf` (PR #59 S2 retained).
Design reference only: PR #47, `7307c48b8a457aba6aafd1dfb43a304734d5d718`. PR #47 is unchanged.

## Accepted implementation contract

- LoadingAssets distinguishes fetch completion from successful `Image.decode()`. Results are ready / failed / timeout, with fetched/decoded flags. Failed records can be requested again; pending/ready requests share one image. Timed-out responses never retroactively become ready.
- Both final normal/Raider entry adapters use one Loading transaction before any existing battle initialization, visibility, opening, equipment wrapper, roster or battle-generation mutation. The original combat/entry choreography is retained after preparation succeeds.
- Required: registered participants' idle stills, installed idle animation frames, installed opening frames and their stills, and a registered background. Missing/failed/undecoded required images never authorize combat. Required sets derive from existing registries; no unmerged Fiona v3 artwork is assumed.
- Optional motion manifest: failure/10-second timeout disables delivered motions, retaining existing still-only behavior after mandatory still/idle readiness. Regions without a registered background keep the existing CSS gradient. Map decorative props retain existing coloured placeholders; missing map JSON/collision remains a rejected S2 transaction.
- The existing BattleMotion preload and BattleIdleMotion canvas renderer share LoadingAssets images. No additional cache of copies is introduced. ForestLoader retains its existing image/retry batches, now tracks actual successful decode and reports optional readiness instead of returning undefined/marking failures warm.
- LoadingView is shared by maps/battles, uses text and CSS only, and has owner-checked close. No fixed display delay, CG, Tips, new lore, LRU policy or fade-duration changes.
- Battle transaction excludes duplicate starts, blocks pointer/tap/keyboard and COMMAND submissions, protects SAVE/DELETE through failure, and provides explicit retry. Loading UI is viewport-independent and includes safe-area padding; rendered portrait/landscape behavior is not claimed as tested here.
- Map entry, explicit LOAD and DEV reset cancel pending battle transactions; generation checks prevent stale completion. S2 rollback, retry, event progression and original save bytes remain protected. Loading state is never serialized.

## Executed QA (2026-10-25, this environment)

| Command | Result |
|---|---|
| `node tests/common_loading.test.cjs` | PASS 17 cases |
| `node tests/loading_map_readiness.test.cjs` | PASS 3 cases |
| `node tests/s2_transition_recovery.test.cjs` | PASS 19 cases, shared view loaded |
| `node tests/issue51_command_lock.test.cjs` | PASS 14 cases, includes Loading locks in both modes |
| `node tests/issue54_coordinator.test.cjs` | PASS |
| `python tests/battle/battle_opening.py --self-test` | PASS asset/manifest and timing-classifier checks only |
| Node syntax checks, HTML inline script syntax, `git diff --check` | PASS |

New tests execute real image/motion/loading modules and the actual normal/Raider HTML entry functions with simulated network/DOM. Required 404/fetch/decode failure, delayed decode, duplicate start, recovery retry, old generation, timeout, optional manifest fallback, repository asset existence, shared-view ownership and actual SAVE/DELETE guards are covered. The S2 suite retains its original 19 assertions, including KI-004 stages 0/15, training retry, actual LOAD/coordinator recovery, event/treasure/slain protection and superseding replies.

## Not executed and residual limits

- Browser regression / rendered desktop, portrait and landscape: **NOT_RUN / ENV_BLOCKED**. Current loopback socket preflight raises `PermissionError: [Errno 1] Operation not permitted`. This is an environment restriction, not a product PASS or FAIL.
- Android physical device: **NOT_RUN / ENV_BLOCKED** (no device attached).
- Real GitHub Pages/mobile-network latency and decoded-image memory use remain unmeasured. Existing caches still have no LRU eviction. Loading is bounded per image/manifest (10 seconds); readiness waiting intentionally adds first-entry latency.
- Optional action animations beyond idle/opening retain existing behavior; this change does not certify every later battle action image, Fiona long-soak behavior or performance.

All executed mandatory alternative QA passed. Both known Loading P1 contracts are addressed; no new P0/P1 found in this scope. Automatic integration is authorized by DIRECTIVE-21A plus v1.3 environment fallback. Browser/device verification remains a post-merge task, never relabeled PASS.
