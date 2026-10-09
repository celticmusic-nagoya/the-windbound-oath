# Aidan A1 QA evidence

JSON results record Chromium1280×720,844×390 and390×844. Mobile tests emulate touch input; these are not physical-phone tests. PNG/JPG files are QA views only, never source production sprites.

To repeat Aidan/navigation checks, serve the repository with `python -m http.server 8015 --bind 127.0.0.1`, install Node Playwright and Chromium, then run `node docs/field/qa/aidan-field-a1/aidan-qa.cjs` and `node docs/field/qa/aidan-field-a1/navigation-qa.cjs`. `LIND_QA_URL` overrides the server URL and `LIND_QA_OUT` the output directory (default /tmp/aidan-field-a1-qa). Chromium executable is /usr/bin/chromium. Current cloud uses NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules.

Aidan QA uses actual field RAF, actual keyboard and mouse/touch controls. Navigation records20 actual RAF bridge crossings (10 round trips), plus20 microstep-checked crossings for each viewport and bounded planning with4×CPU emulation on mobile. Performance uses a captured native clock, not mocked animation time. Saved progression/storage/position restore is checked. Light/dark asset reviews are separate from pixel statistics.

Other regression procedures reuse the recorded STEP9–11/navigation harnesses under docs/field/qa/lind-navigation-a1. This resumed run freezes the livestock QA clock before image decoding so initial-state assertions cannot depend on download time. No livestock source was changed.
