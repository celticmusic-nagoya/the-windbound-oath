# Lind building front collision — branch review

Start: `fa95f9646dfc70f37abfb4f64ad2b9e84ece424c` (clean main).
Branch: `work/lind-front-collision-fix`.
Scope: DEV Lind field only. No production PNG, Battle, camera, movement,
navigation, Aidan actor, story or save changes. Main integration is deferred
until this branch result is reviewed, as requested.

## Cause and reproduction

The previous body rectangle ended above the actual front props. At the shop,
Aidan origin `(283.8, 620.25)` has foot rectangle `x=289.8..311.8`,
`y=652.25..662.25`. The old barrel's right edge was `289.2`; the old wall
ended at `650.76`. Neither caught the foot, although the PNG still showed
barrels/display props at that position. This is a world-space geometry gap,
not a camera conversion or actor anchor error.

There was also a depth error: the whole shop used full image bottom `689`
for z-index, placing its distant flowers/fence above an actor standing on
legal central steps. Its façade ground line is now `650.76` (z-index 651).
The actor's existing `py + 44` depth is unchanged. Whole PNG rendering
still permits upper-body overlap behind roofs/canopies; ground props are
protected by actual foot collision, not by blanket sprite overlap rejection.

## Model

Each of the 14 profiles separates body/foundation rectangles from named
front props. Door approach lanes are metadata/debug shapes only: they do
not subtract solids or carve a hole through walls. No single broad front
rectangle was added. Per-building `depthY` records the façade ground line.

- A: building wall/foundation/post solids (orange debug).
- B: individual barrels, crates, flowerbeds, fences and ground props (gold).
- C: narrow clear central approach (green dashed); no solid subtraction.
- D: overhead roofs/awnings allow upper-body overlap where feet remain clear.

Footprint remains **22 × 10**, offset `(6,32)`, ground anchor `(17,42)`.
Aidan remains native 44-world-pixel body height. Camera, speeds and key
handling are untouched. Debug colors are translucent so the feet stay visible.

The warehouse filled with logs is closed storage: approach stays outside the
log base. Cow/pig shed markers approach the closed pen front; they do not
open fences. The chicken coop's existing open gate and training shed's
central raised porch are walkable. Training columns, rails/platform edges
remain solid. No actual building interior interaction is added.

## QA method

`front-fixtures.json` records 56 manually measured PNG ground contacts and
14 door markers. Samples are not generated from collision rectangles.
The runner checks all 14 subjects at scales 1 / 1.5 / 1.8 / 2.1 and viewports
1280×720 / 1920×1080 / 844×390 / 390×844.

Each subject receives ten requested approach directions with both Arrow and
WASD (the actual DOM event handler), native browser keyboard pushes against
one measured front prop, three actual mouse/touch door approaches, rejected
solid clicks/taps, a visible rear destination and two live navigation laps.
Per-frame tracing rejects static-solid or river penetration. The browser
clock runs real requestAnimationFrame movement; it does not replace motion
or collision code. Initial position placement is test setup only.

Collision overlays are on for contacts, keyboard approaches and screenshots.
During timed route playback the runner temporarily hides the expensive SVG
and restores it afterward; collision physics remain active. Each rendered
subject rectangle is compared with world geometry (<0.04 screen px error).
The output also tests debug OFF stopping and repeated toggle lifecycle.

Touch samples avoid nearby NPC interaction buttons; those buttons retain
Chrome's existing tap priority. The barn's primary stop sample is at the
barrel center: the earlier sample close to its door correctly slid into the
approach lane via existing corner assist, and was unsuitable for a fixed-X
prop stop assertion. Cow/pig/coop adjacent fencing requires wider safe
perimeter endpoints rather than forcing passage through the pens.

```sh
# Run a static HTTP server for this repository, then:
NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules \
  node docs/field/qa/lind-collision-front/front-qa.cjs
```

Optional: `LIND_QA_URL`, `FRONT_QA_OUT`, `FRONT_QA_VIEWS`, `FRONT_QA_ONLY`.
Chromium executable defaults to `/usr/bin/chromium`.
Outputs include machine-readable results and actual screenshots. Evidence
images in this folder are QA-only copies/annotations, not production assets.

Retained regressions are recorded separately: Aidan 4 idle + 16 walk,
NPCs/Emma, birds, wind OFF with water flowing, camera/bridge input, normal
attack/一閃/guard/enemy turn/COMMAND/DEV kill/KO/Victory and Raider1250/HUD.

## Visual evidence

- [All 14 ground profiles and contacts](evidence/all14-after-contact.png)
- [Baseline shop with collision](evidence/before-lind_item_shop-0.52.png)
- [Baseline shop without collision](evidence/before-off-lind_item_shop-0.52.png)
- [Shop ground stop](evidence/visual-lind_item_shop-on.png), [without overlay](evidence/visual-lind_item_shop-off.png)
- [House ground stop](evidence/visual-lind_house_02-on.png), [without overlay](evidence/visual-lind_house_02-off.png)
- [Barn ground stop](evidence/visual-lind_barn-on.png), [without overlay](evidence/visual-lind_barn-off.png)
- [Training support column stop](evidence/visual-train_shed-on.png), [without overlay](evidence/visual-train_shed-off.png)

The preceding images use unchanged formal PNGs. Magenta in contact charts
is an independently measured ground point, not a replacement collision.
Closed storage and pen fronts do not become interior walkable areas.

## Audited building approaches

| Building | Solids | Door anchor (world) | Lane width | Access |
|---|---:|---|---:|---|
| lind_elder_house | 11 | 490.4, 346.2 | 42.0 | door |
| lind_inn | 10 | 907.5, 357.0 | 41.9 | door |
| lind_aidan_house | 9 | 1279.8, 423.2 | 40.6 | door |
| lind_item_shop | 11 | 321.1, 667.5 | 30.4 | door |
| lind_house_01 | 10 | 311.4, 1007.2 | 45.9 | door |
| lind_house_02 | 11 | 640.4, 1186.9 | 36.5 | door |
| lind_house_03 | 11 | 284.1, 1353.0 | 39.1 | door |
| lind_house_04 | 9 | 606.9, 941.8 | 39.1 | door |
| lind_barn | 11 | 1087.5, 792.5 | 36.2 | door |
| lind_storage | 7 | 1301.7, 806.6 | 28.5 | closed-storage |
| lind_cowshed | 6 | 1043.0, 984.0 | 27.8 | pen-front |
| lind_pigsty | 6 | 1213.5, 981.2 | 28.5 | pen-front |
| lind_chicken_coop | 5 | 1357.5, 981.2 | 31.5 | open-gate |
| train_shed | 8 | 2086.0, 729.6 | 34.1 | open-porch |

## Observed navigation warning

The initial 844×390, 2.1x run stopped with `blocked` during the pig-shed's
straight door approach. That run did not record the instantaneous actor
positions, so its precise cause is **not conclusively established**. The
other three viewport runs completed every subject/scale. A complete mobile
landscape rerun includes a route-failure diagnostic with static, animal and
NPC collision states; the initial stop is retained as a warning rather than
erased from the test history.

A separate controlled comparison used the baseline main JS/CSS and this
branch, with a walking pig deliberately entering Aidan's feet after a route
was requested. Both cancel the route with `blocked`, while static building
collision is false and animal collision is true. Both reach the same clear
approach target after the pig leaves and the destination is specified again.
See [controlled comparison](moving-obstacle-comparison.json). This confirms
an existing dynamic-obstacle cancellation behavior, **not** the exact cause
of the original uninstrumented stop. No navigation, animal behavior or
collision-bypass change was made to conceal that observation. Player QA
should include the pig-shed approach while livestock is moving.

## Final branch result

**PASS WITH WARNINGS.** Final successful runs cover 224 subject cases,
4480 keyboard approaches, 896 independent ground contacts,
672 actual door pointer routes and 448 perimeter laps.
Live trace samples: 122564; static/river penetration: 0.
Maximum debug alignment error: 0.000352 screen px.
All four final viewport runs: image 404 = 0, JS exceptions = 0, console errors = 0.
The complete 844×390 rerun passed all four scales, including the pig-shed
straight/left/right door approaches. The first-run stop remains documented.

Source checkpoints: representative shop `5890e2ac9d04077da80801dc57c933325d581a80`,
all-building correction `4c3aeb746d2a1cf8b04f173e063160f8d693096c`.
[Full final runs](front-results.json), [summary](front-summary.json),
[protected source and asset audit](source-protection.json),
[retained regressions](retained-regressions.json).

GitHub Pages still publishes main `/` at the starting baseline. This branch
is ready for review; the fix is not deployed publicly until main integration.
Do not proceed to Aidan A2, Fiona/Lou field production or STEP 12.

LIND FRONT COLLISION PLAYER QA READY
