# WALK-QA-02 — Codex / Claude coordination

Codex owns `feature/dev-walk-motion-01`: shared DEV tester, `walk-motion.js`,
`walk-test.js`, `field-walkers.js`, and minimal runtime frame-policy adapters.
Claude owns integration of PR #107 and #112. Do not merge #109/#111 separately.
No adopted PNG is changed by the tester.

## Integration contract

- Tester enumerates `FieldWalkers.describe()` directly from the production manifest.
  PR #107's six-frame bank is picked up without a DEV frame list.
- Tester reads `MossForest.walkStride(actor, dir)` at playback time.
  When integrating #112, return the actual production `aidanStride(dir)` for Aidan,
  and the unchanged production stride for Fiona. Preserve the existing DEV query override.
  Do not maintain a second stride setting solely for the preview.
- `index.html` loads `walk-motion.js` before `field-walkers.js`, monsters and runtime.
  Preserve this order and refresh cache keys after integration.
- NPC/legacy enemy left/right reuse is explicitly labelled. Missing up/down banks
  show 未実装, with no substitute preview. Flyer is available as idle/flight, not walk.

## Independent QA already collected (historical heads only)

- #107 `7201b582dc9c24fb64a17747732659c1f741ff07`: PASS implemented horizontal
  six-frame patrol, three viewports, formal 259 SHA. Dedicated up/down absent.
- #112 `42509215520ac129cf14c83d436f448d1487dd83`: comparison 50/72/90,
  recommendation 72. Code already used 72; PR description's 50 was stale.
  Main m31 5/5 and PR m31 6/6; earlier intermittent failure not reproduced.
- Both heads changed when checked during this extension. These results must NOT
  be presented as independent QA of the newer heads. Revalidate integration heads.

Physical Android visual acceptance remains the director's task. Codex does not
claim that pushing this handoff starts a Claude session or completes its integration.

Integration update: upstream #107 via #123 and #112 via #124 are merged in main22efe87.
Codex imported them after their integration completed, preserved default72 / query
overrides and connected the shared runtime adapter. Final integrated tester QA pending.
