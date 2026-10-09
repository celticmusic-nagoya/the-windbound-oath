# Lind camera QA

Run a static server from the repository root on port 8015. Install/use Playwright and Chromium; no application dependency changes are required.

```sh
node docs/field/qa/lind-camera/camera-qa.cjs
node docs/field/qa/lind-camera/aidan-animation-qa.cjs
node docs/field/qa/lind-camera/battle-regression.cjs
```

Set `NODE_PATH` if using the managed runtime's Playwright installation. Optional `LIND_QA_URL` changes the server URL. `LIND_CAMERA_QA_OUT` controls camera/battle outputs; `LIND_QA_OUT` controls Aidan outputs. Chromium path is `/usr/bin/chromium`.

Camera tests use real mouse/touchscreen input against the rendered DOM at seven scales and four viewport sizes. Existing navigation sweeps are stepped deterministically to verify five complete bridge round trips per scale/viewport (140 round trips total) without a long real-time soak. Separate Aidan tests run actual RAF animation at 1.30x, all idle and walk frames, anchors, keyboard and mouse/tap display toggle. Battle tests enter review at 1.35x and verify camera restoration before normal/Raider action/KO/Victory regression. Additional action/geometry/bird logs are from the existing regression suites.

PC screenshots compare 1.00 / 1.25 / 1.28 / 1.30 / 1.35 at the same Emma review location. Mobile screenshots show 1.28x. These are captures of the game, not modified production assets. No final standard camera choice is made.
