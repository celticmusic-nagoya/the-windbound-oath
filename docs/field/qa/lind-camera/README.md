# Lind camera QA

Run a static server from the repository root on port 8015. Install/use Playwright and Chromium; no application dependency changes are required.

```sh
node docs/field/qa/lind-camera/camera-qa.cjs
node docs/field/qa/lind-camera/aidan-animation-qa.cjs
node docs/field/qa/lind-camera/battle-regression.cjs
```

Set `NODE_PATH` if using the managed runtime's Playwright installation. Optional `LIND_QA_URL` changes the server URL. `LIND_CAMERA_QA_OUT` controls camera/battle outputs; `LIND_QA_OUT` controls Aidan outputs. Chromium path is `/usr/bin/chromium`.

Camera tests use real mouse/touchscreen input against the rendered DOM at seventeen scales (1.00–2.10) and four viewport sizes. Existing navigation sweeps are stepped deterministically to verify five complete bridge round trips per scale/viewport (340 round trips total; center and slight off-center routes) without a long real-time soak. Separate Aidan tests run actual RAF animation at 2.10x, all idle and walk frames, anchors, keyboard and mouse/tap display toggle. Battle tests enter review at 2.10x and verify camera restoration before normal/Raider action/KO/Victory regression. Additional action/geometry/bird logs are from the existing regression suites.

New captures compare 1.50 / 1.60 / 1.70 / 1.80 / 1.90 / 2.00 / 2.10 at the same Emma review location in all four viewports. Earlier committed screenshots/JSON preserve the original seven-scale run; extended results are recorded separately. These are captures of the game, not modified production assets. No final standard camera choice is made.


For public Pages, set `LIND_QA_PUBLIC=1` and `LIND_QA_URL=https://celticmusic-nagoya.github.io/the-windbound-oath/` on the camera suite. It opens the actual DEV menu and player-display toggle. `LIND_QA_VIEWPORTS='[[1280,720]]'` optionally runs one viewport. The selector is checked against all 17 independently specified candidates; repeated changes check position, destination, DOM-node count and CDP event-listener count. Release config values must stay undecided (`null`).

At high zoom, the 140-world-pixel-tall Wind Stone can exceed the unobstructed mobile-landscape height (2.10x ≈294px versus284px below the toolbar). A full-monument screenshot is not required at every scale: tests require the player and clickable interaction area to remain visible/usable. No special landmark camera correction, sprite resize or toolbar redesign is introduced. This is a PLAYER QA visibility consideration, not a movement or input change.

Field interaction inputs use the visible intersection of hit area, viewport and toolbar, checked with `elementFromPoint`. This avoids Playwright locator scrolling of the overflow-hidden game container when a tall/high-zoom object is partly outside the viewport. Camera follow remains unchanged.
