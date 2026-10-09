# Battle / performance / next-motion structure audit

Production HTML/CSS/JS/PNG remain byte-identical to freshly fetched main.
No prototype branch is integrated. No new motion, skill, character or enemy.

## Source audit

Active state: `battle-actor-state.js`; dynamic roster adapters are registered by
`prologue-combat.js`, not a separate assumed adapter file. State owns source PNG,
sequence ID and one cancellable timeout per actor. KO/Victory protections remain.
`battle-facing.js` owns inner-image facing, motion roots/HUD stay independent.
`battle-party-layout.js` owns current sizes; presentation/cut-ins are handled by
`battle-presentation.js` and Critical WAAPI pauses by the existing presentation
module. The old engine in index.html is still involved; do not rewrite it as a
cleanup task. Source syntax40modules passed.

All74 Battle images inventoried. Normal Goblin/Tainted/Raider each have registered
existing art and actual battle scenes in the error sweep. BattlePNG dimensions,
alpha and path are in asset CSV; live geometry/facing/object-fit/parent transforms
are in scene-sweep.json. A transform string of `none` alone is not a facing verdict:
CSS individual scale and custom `--battle-facing` are also relevant. Party faces
right, ordinary enemy art is flipped left by the established inner-image policy;
frontal terminal/support artwork is deliberately neutral.

Raider source1312x1199. Image wrapper rectangles in the current baseline:
1280x720:537.59x504;1920x1080:720x640;844x390:520x440;390x844:366.59x438.88.
These are measured existing rectangles, not newly chosen sizes. HP1250 and boss
HUD outside the Raider sprite tested; phases >820/>400/<=400 unchanged.

## Aidan Idle: why subtle

Only Aidan is registered. Main's normal breathing cycle remains
00→01→00→02→00,5.4–7.9s.01 and02 each850–1150ms;00 at cycle end and next cycle
start concatenate into2600–4000ms of the same pose. Every3–5 cycles adds
00pause2–4s→03hold1.2–1.9s→00return1.8–2.4s. Crossfade220ms. No retuning.

Actual60s trace: two03 starts at24.560s/56.816s (32.256s apart). Within the
recorded transition span:00 time39.936s (~69.4%),01 time7.120s,02 time7.040s,
03 time3.440s. This random trace is evidence, not a guaranteed schedule.
Whole-sprite alpha centroid after current anchor compensation differs by
approximately x+1.96/-2.73/+0.83 and y-0.77/-0.43/-0.16 CSS px at the normal PC
fit. This includes cape/sword, not a measured chest displacement. Small pixel
changes plus long00 holds explain the perceived stillness.

Rendered-canvas foot QA: primary sole193.596px in all4 frames; other foot varies
~0.998px, below1.5px threshold. Current anchors preserved. Source1536x1024 all
4RGBA true transparency; no processing.

Live action suite covers all4viewports and both normal/Raider: actual COMMAND
attack/target, forced DEV Critical preserving820ms lunge/100ms hit-stop, actual
一閃/cut-in/TP30, enemy damage→Idle. Prayer real COMMAND confirms MP-6/RUNE+28;
item API confirms consumption once, KO/Lou rejection (not a full new item UI suite).
Separate terminal tests issue DEV kill while enemy action is running: KO fixed,
Victory fixed, result shown. Long-idle suite independently tests guard/action,
dialogue/cut-in pause, reduced motion, old-timer races, shared cache and exit cleanup.

## Forest Bat source readiness

Four existing1536x1024 RGBA frames,transparent56.31–59.15%. Contact review:
no obvious baked white/black/checkerboard. Wing phases and body placement differ;
keep native PNGs and use anatomical center registration before any future flying
motion. Frame02 strong right wing has only4px margin; faint alpha reaches edges
of several frames. Inspect complete wing silhouette in PLAYER QA. Metadata
threshold1/64/192 bounds recorded in forest-bat.json; wing bbox center is not a
body anchor. No Bat AI/motion/asset registry has been added to main.

## Minimal future structure (proposal only)

Reuse BattleActorState lifecycle/sequence cancellation, existing shared Idle RAF,
preload cache and action WAAPI. Add optional actor `motionType` metadata with a
GROUNDED default. Keep action root translation separate from image-local idle.
Existing `defineType` covers frame/hold patterns; only extend paint/idle offset
when an actual airborne use case requires it. Do not introduce an independent
clock per actor or a new battle engine.

|Type|Example|Future idle anchor / visual layer|
|---|---|---|
|GROUNDED|Aidan|foot anchor; current breath|
|FLYING|Forest Bat|chest anchor; wing extent/air offset inside visual layer|
|FLOATING|Lou|body anchor; optional small hover; current support position preserved|
|HEAVY|future Bram|foot anchor; deliberate pose holds; no global duration changes|
|SLIME|future Moss Slime|base contact; local squash only, no collider changes|

No new behavior is implemented. A small facade around current Idle hooks may be
added on the motion branch if multiple types need it, not during this audit.

## Performance / preload / cache

Chromium headless,4viewports:PC DPR1/mobile emulation DPR3.90actual RAF intervals
per scene sample. Concurrent QA load means these are indicative desktop-host
numbers, not physical-phone benchmarks. Field average16.67–20.74ms; scene DOM797
constant across3open/close cycles. Event-listener counts stable on second/third
open (178/180); transient first-open count can fall when nodes are collected.
Pending Field RAF8 (including measurement RAF)/0–2timeout/1interval; Battle RAF4
(including measurement)/temporary presentation timers/1interval. These are total
application counters, not8idle loops. Idle itself shares one RAF and one4-image
cache between normal and Raider; terminal/exit tests verify it stops.

24explicit decode calls,24unique paths across three Field visits and normal+
Raider:20AidanField+4Idle, no repeated explicit decode. NPC/fisherman images are
mounted once; browser source cache reused, not reloaded perframe. Twelve fishing
frames swap hidden visibility under the NPC shared clock. Cut-in DOM is temporary;
its repeated insertion is expected. No proven duplicate-load/listener/cleanup bug
requires a compatible code fix.

Nominal RGBA of unique loaded DOM image sources during Field review is about
543–597MiB by viewport, including hidden scene images; this is a conservative
source-size sum, NOT measured resident GPU memory. JS heap ~2–3MiB excludes image
storage. CDP layout/style counts/durations are stored, no global reflow rewrite.
Continuous NPC inline-style writes and depth/camera RAFs are future profiling
candidates; changing their ownership here risks behavior and is deferred.

An all-image2x pack costs4x decoded source size (~4.11GiB versus1.03GiB total).
AidanField alone20frames120MiB→480MiB (+360MiB). Emma1frame~6MiB→24MiB (+18MiB).
Current PC sources already exceed physical render resolution. Do not indiscriminately
upscale. Proposed future gate:one actor opt-in at a time, record load latency,
resident memory/frame timings on an actual low-memory phone; a+32–64MiB incremental
pack is a trial budget, not a certified device limit. No 2x increase is approved
by the current headless measurements.

## Errors and limits

20DEV destinations×4views checked, no HTTP error/JSexception/console error in
that sweep. Both normal and Raider plus Field functional suites have independent
error listeners. Static/runtime registry exact-case paths all exist. External
unvisited deployment/physical devices are not certified. No Pages deploy occurred.

Expected QA-runner errors were investigated without modifying application code:
missing copied front fixture was supplied and runner restarted; the Prayer runner
initially referenced a closure variable, then used the public normalRune getter.
Those failed attempts are not game exceptions. Only completed assertions are
reported as passes. Every durable result is from this fresh-main branch.
