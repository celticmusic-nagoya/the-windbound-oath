# DIRECTIVE-21B — InputManager Loading priority / Issue #60 / PR #61

Continuation on the same `fix/common-loading-21a` branch. Prior PR head:
`25f59c51434e694047b54023d28589f3e39a5862`; main/base:
`dcc36c6725286e89f43b424c8b87165bf59c6bbf`. PR #47 remains design-only.

## Root cause and fix

The previous document-capture guard ran after InputManager's window-capture handler. The real InputManager could report FIELD and invoke `MossForest.interactNearest()` before the Loading guard saw Enter. The original failed diagnostic is retained; it is not relabeled PASS.

`LoadingInput` is now the single map/battle Loading policy, loaded in the head before game input handlers. LoadingView owns its lock; stale owners cannot release it. InputManager checks this same policy at the start of onKey and reports LOADING before field, dialogue, scene, menu or battle contexts. This is not solely a propagation barrier. The old independent BattleLoading document guard was removed.

The policy handles keyboard, pointer/click and recovery-action permission. Only enabled, visible `data-loading-action` buttons inside the Loading/recovery panels are allowed. Enter/Space activate an allowed button once, suppress native keyup activation, and consume held-repeat events. Retry is focused on failure; Tab cannot escape the active recovery control. Existing explicit map/load retry controls use the same permission; no new cancel operation is invented.

Loading acquisition clears InputManager held directions, old-world movement targets and field runtime keys/held pointers via one lock notification. Keys already down, or pressed during Loading, cannot restart after unlock until released. Pointer gestures spanning the boundary cannot replay a delayed background click. A fresh permitted recovery gesture remains usable. Map retry disables its button synchronously, before scheduling asynchronous work, and re-enables it on a new failure.

S2 rollback, event/treasure/slain state, save bytes and failure notification contracts are retained. LoadCoordinator only delegates explicit recovery-target permission to the common policy; its boot/load/failure/save guards remain unchanged.

## Current executed QA

| Verification | Result |
|---|---|
| `node tests/loading_input.test.cjs` | PASS 37 cases |
| Original InputManager probe with the real common Loading policy loaded | PASS: LOADING / underlying interactions 0 (previously FIELD / 1) |
| `node tests/common_loading.test.cjs` | PASS 17 existing cases, actual common input module loaded |
| `node tests/loading_map_readiness.test.cjs` | PASS 3 existing cases |
| `node tests/s2_transition_recovery.test.cjs` | PASS 19 existing cases, real common input + view loaded |
| `node tests/issue51_command_lock.test.cjs` | PASS 14 existing cases |
| `node tests/issue54_coordinator.test.cjs` | PASS |
| `python tests/battle/battle_opening.py --self-test` | PASS (asset/classifier only) |
| Syntax of changed JS, all inline scripts; staged/unstaged diff checks | PASS |

Input tests execute real InputManager/LoadingInput/LoadingView and simulate window capture → document capture → target → document bubble → window bubble. They test Enter, Space, Escape, all arrows across normal/Raider/map owners, mouse/touch events, explicit retry priority and exactly-once activation, InputManager registered first, held-key release, stale owner, pointer tail, disabled controls and map recovery controls. Existing tests retain their expectations; fixture wiring now includes the real shared module.

## Environment and residual limits

- Browser rendering/regression, desktop/portrait/landscape: **NOT_RUN / ENV_BLOCKED** (loopback socket PermissionError).
- Android physical device: **NOT_RUN / ENV_BLOCKED** (no device attached).
- Tests simulate DOM/event dispatch; they do not certify browser-native touch or keyboard synthesis. A real browser/device smoke check remains recommended after merge.
- Latency, image-memory/LRU and long Fiona soak limits from 21A remain. No lore, balance, save schema or scene choreography changes.

The previously reported input-leak P1 is addressed and executable mandatory alternative QA is PASS. No new P0/P1 or unintended conflict identified. DIRECTIVE-21B authorizes merge after latest main/head/conflict checks.
