# Lind Visual Polish STEP B — Village Life PLAYER QA

FINAL RESULT: **PASS WITH WARNINGS**

SOURCE BRANCH: `work/lind-visual-polish-village-life`
START COMMIT: `51707fcc025377c54301a541d9dc7e8ed934c34b`
Runtime verified: `e53eeea0475c555ee62a74acabcccc92d519f761`.
QA commit: the commit containing this report. No main merge/deploy was performed.

## Checkpoints

| Checkpoint | Commit |
|---|---|
| Previous investigation | `8eef59fdc91d7b114b33e716f71431b9a1ebd136` |
| Previous dynamic navigation (reused, not reimplemented) | `2e77f13913a375f065cdb67a415dbb63c01b7802` |
| Previous navigation QA / resume point | `51707fcc025377c54301a541d9dc7e8ed934c34b` |
| Fisherman source/frame import | `88ee59a06674729b234f8f225fa3d9cdd313859d` |
| Fisherman ambient implementation | `c4239eb4942788a9c77d38cc9036bec204795558` |
| Children chase | `9a67992646c55987ad155a271c94967e3f5e3235` |
| General villager life | `493f494aab184fecd3602ef7b3bb4ec6f614ade3` |
| Emma | `46a39f7bec2724f8c0c3ab2e77f56ff6428e18be` |
| DEV NPC focus safety | `16e0de2c6d6f36c4ceea07ceb5ab88bae2cf9fc3` |
| Brief worker motions | `e53eeea0475c555ee62a74acabcccc92d519f761` |

## Fisherman — PASS

The uploaded ZIP contains one actual `fisherman_animation_sheet.png`: **2172×724, RGBA**, 878,026 fully transparent pixels / 1,572,528 (55.84%). Source SHA-256 `d578d29a27eeffbc6b31201d6fb9bebdbc525133acfe0bc00848efca3a9ba255`.

Layout is irregular **7 + 8 + 8** poses, not a regular grid. Twelve inspected, complete poses were extracted losslessly. Each RGBA crop has real transparent pixels and exactly matches its source region; original alpha, including partial alpha and faint edge pixels, was preserved. No regeneration, background removal, old PNG edits, or character redesign. [All crop regions/anchors](../lind-village-life-assets/frames.json), [alpha/pixel audit](asset-audit.json), [source PNG](../lind-village-life-assets/fisherman_animation_sheet.png), [visual contact sheet](fisherman-frame-contact.jpg).

The source's bottom-right rod is clipped; that pose and unnecessary neighboring poses are **unused**. Used frames retain the fisherman, rod/line/bobber for fishing states and the fish for catch/inspection states, with no baked checkerboard or matte detected by visual QA. Orange bite/music marks belong to the artwork. The original inline preview was not used as a production image.

Fisherman sits at dock tip `(1560,1380)`, faces right, bobber over right-side water. Fixed body/foot anchor and **18×8** body footprint; rod/splash do not enlarge collision. Per-frame margins are compensated using independent anchors. The old non-solid separate rod is hidden only in DEV review to avoid duplication; no prop/collision data was changed.

Shared NPC RAF drives `FISH_IDLE → WAIT → BITE → REEL → CATCH → INSPECT → RESET → FISH_IDLE`. Ordinary waits end in a brief rod adjustment. Waits 8–25 seconds, bite chance 18% at eligible checks, catch cooldown ≥60 seconds. Thirty-minute deterministic simulation: **11 catches, WAIT 1,600/1,800 seconds (88.9%), shortest catch gap 74.6 seconds**. No fishing rewards, story hooks, or extra timers.

[Idle](fishing-1280-1.8.jpg) · [Bite](fishing-sequence-bite.jpg) · [Reel](fishing-sequence-reel.jpg) · [Catch](fishing-sequence-catch.jpg) · [Inspect](fishing-sequence-inspect.jpg) · [Reset](fishing-sequence-reset.jpg).

## Children / villagers / Emma — PASS

Two existing children use an authored route derived from actual plaza/Wind Stone geometry. Bounded RUN/CHASE, pauses/look-back, role exchanges, alternating direction, unequal speeds, and player yield. No synchronized constant circle or world-wide random roaming. Thirty-minute simulation: **52 role exchanges (including 2 close tags), 26 reversals, 104 pauses**, no zone escape, static collision, sustained mutual overlap, or player pushing. Role exchange also occurs after a long chase to avoid endless pursuit. A separate player-in-route fixture verifies yielding.

[Children sequence 0](children-sequence-0.jpg) · [1](children-sequence-1.jpg) · [2](children-sequence-2.jpg) · [3](children-sequence-3.jpg) · [4](children-sequence-4.jpg).

Nine general NPCs have staggered occupation-specific routines: local walkers ~20px radius; workers up to ~18px near existing farms, brief 1.4s inclination toward work followed by long rest; shops ~5px; elders ~4px. Farmer's existing walk image is reused. No new character art. All candidate movement is swept against existing static collision, player, other NPCs, and livestock; occupation waits/returns instead of forcing through blocked space. No synchronized all-NPC walk in the 30-minute test.

Emma keeps her original origin `(820,780)` and height 38, slowly moves ~4px, turns, and returns. Cane/glasses/hair/shawl source PNG untouched. No late-story events or dialogue. [Farm](life-1280-1.8-farm.jpg) · [Emma scale](life-1280-1.8-emma.jpg).

DEV focus was corrected after testing discovered Enter could pick a passing child instead of the selected villager. It now chooses a free nearby location where the selected NPC is nearest. Clickable hit areas may partially overlap momentarily as children pass; tested actual exposed hit areas, rather than assuming every rectangle's center belongs to that NPC.

## Integrated regression evidence

| Check | Result / evidence |
|---|---|
| All 13 NPC mouse/tap + Enter, child yield, humans/livestock continue with wind OFF | PASS — [integrated-qa.json](integrated-qa.json) |
| Fisherman 30-minute cycle, fixed anchor, dock, all scales | PASS — [fisherman-qa.json](fisherman-qa.json) |
| Children 30-minute simulation | PASS — [children-qa.json](children-qa.json) |
| General NPC / Emma 30-minute simulation | PASS — [villagers-qa.json](villagers-qa.json) |
| Pig contact waits and resumes without re-click, child/villager/multiple fixtures, cancel | PASS — [dynamic-qa.json](dynamic-qa.json) |
| Late stationary actor detour / retained occupied destination | PASS — [detour-qa.json](detour-qa.json) |
| Static navigation exact per-step equivalence, 7 cases | PASS — [legacy-qa.json](legacy-qa.json) |
| All 14 buildings' front/door/corners/collision at PC 1× | PASS — [collision-qa.json](collision-qa.json) |
| Five representative buildings on both mobile views, 1.8× / 2.1× | PASS — [mobile-collision-qa.json](mobile-collision-qa.json) |
| Real input/bridge/corner assist/camera/exit restore | PASS — [camera-qa.json](camera-qa.json) |
| Aidan all 4 IDLE / 16 WALK frames, anchor and control | PASS — [aidan-qa.json](aidan-qa.json) |
| Birds approach/takeoff/flock, wind OFF, water continues | PASS — [step11-bird-qa.json](step11-bird-qa.json) |
| Original doors, normal attacks, 一閃, Fiona guard | PASS — [live-input-qa.json](live-input-qa.json) |
| Normal/Raider COMMAND, DEV kill during motion, KO/Victory/race protection | PASS — [battle-regression.json](battle-regression.json) |
| Protected sources + runtime static geometry/object hashes | PASS — [source-protection.json](source-protection.json) |

**PC:** 1280×720 and 1920×1080 PASS. **Mobile emulation:** 844×390 and 390×844 PASS. Field display/input/camera checked at **1 / 1.5 / 1.8 / 2.1**. Battle/Aidan/bird suites use the three requested principal viewports. No assertion failures remain.

Wind OFF stops foliage and birds; **water, fisherman, children, villagers and livestock continue**. Review exit preserves story state, localStorage and the original player location. No NPC save/story changes.

**Dynamic navigation:** reused unchanged since `51707fc`; pig route retry PASS, previously solved livestock interference remains improved. **Static collision / Terrain STEP A / Aidan A1 / camera / Battle assets and logic: UNCHANGED**. Main/index inline code unchanged except five external field include lines. **Raider HP 1250**, giant scale and independent HUD preserved. eidan_fiona_lou reference preserved with SHA-256 `d5cfebcd2dabfbdbc4a984a309dd356fb1105546664c3fdb3d7fc624affeafc4`.

**IMAGE 404: 0 · JS EXCEPTIONS: 0 · CONSOLE ERRORS: 0 · OLD / INVALID REFERENCES: 0** in executed tests. `index.html`, `js/`, `css/` have no embedded/numbered battle/old Lou path matches; embedded directory absent.

## Changed files

- `index.html`: one field stylesheet + four field module script includes; inline code unchanged.
- `js/field/lind-npcs.js`: shared update/render/hit/foot tracking and safe local NPC movement/DEV focus.
- `js/field/lind-emma.js`: bounded peaceful DEV routine metadata.
- New `js/field/lind-fisherman-assets.js`, `lind-fisherman.js`, `lind-children.js`, `lind-village-life.js`.
- New `css/lind-village-life.css`: DEV fisherman prop visibility and restrained child/worker motions, reduced-motion support.
- Twelve new `img/field/lind/npc/fisherman/fisherman_*.png`.
- Source/frame audit and regression artifacts under `docs/field/qa/lind-village-life-assets/` and this directory. JPEG files are QA screenshots only, not production assets.

## PLAYER QA / warnings

1. Test this **source branch**, open DEV → リルド村 · 素材仮配置, select 釣り人 / 風の石 / 農夫 / エマ via 素材へ移動. Observe rare catches over a few minutes, children's route/pause/role changes, farm/Emma behavior, and walk across the plaza/dock/bridge. Try wind OFF while observing people, livestock and flowing water.
2. Children and most villagers reuse existing idle art for movement (children add a small step inclination); they do not have newly drawn multi-frame leg cycles. Foot sliding/feel needs PLAYER visual review. Farmer reuses the existing walk pose. Fisherman's reset transitions from supplied fish-check pose to existing rod wait pose; no new casting artwork was invented.
3. Camera default remains **1×**, although an earlier brief mentioned provisional 1.8×. This batch does not change camera policy. Use the existing selector for QA.
4. Mobile checks are Chromium touch emulation; physical Android/device verification remains PLAYER QA.
5. Remote main advanced independently from `ac3707698018aa9efe016e04776ba3d1d1be833e` to `92e77b94aee6277df7b045a7edf97e543fc345ec` (user's Battle idle uploads). They were not merged into this branch or overwritten. This task leaves main untouched. GitHub Pages main publication is not updated by this source-branch push; later integration requires separate authorization.

No Aidan A1.5/A2, Fiona/Lou sprites, Party Follow, interiors, STEP12, new camera or Battle work performed.

For rerunning gate scripts, start a static server on 8015 from the repo, use installed Playwright/Chromium (`NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules`), and run the `.cjs` files. `LIND_QA_OUT` can place generated artifacts outside the repository. Existing broader suite paths are documented in the preceding terrain QA directory; fresh results are linked above.

**LIND VISUAL POLISH STEP B — VILLAGE LIFE PLAYER QA READY**
