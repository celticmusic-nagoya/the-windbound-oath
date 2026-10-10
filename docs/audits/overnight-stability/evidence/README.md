# Audit evidence / reproducibility

Source: fresh remote main d3e299ac7ca90eb49629570a57a90ff678ad7591.
HTML/CSS/JS/images unchanged. Tests use actual application code; fixture placement,
DEV jumps and accelerated browser clock are test-only in isolated contexts.

Environment verified with cloud onboarding/runtime skills: Python/Pillow/numpy,
Node/Playwright, system Chromium. No new dependency or reusable setup configuration
was required. Start static server from repo root on127.0.0.1:8015; never use these
loopback URLs as public PLAYER QA links.

Example command (from repo root, no game source edits):

```sh
python -m http.server 8015 --bind 127.0.0.1
```

In another shell:

```sh
export NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules
export LIND_QA_OUT=/tmp/overnight-qa
export AIDAN_IDLE_QA_OUT=$LIND_QA_OUT
export LIND_CAMERA_QA_OUT=$LIND_QA_OUT
export FRONT_QA_OUT=$LIND_QA_OUT
export OVERNIGHT_AUDIT_OUT=$LIND_QA_OUT
mkdir -p "$LIND_QA_OUT"
node docs/audits/overnight-stability/evidence/animation.cjs
```

Other runners can be invoked similarly. Some standalone new runners use `__dirname`
as output; copy runners into a temporary output folder first if you need to retain
tracked evidence unchanged. Front runner requires adjacent front-fixtures.json.
One viewport per long runner avoids session-length interruptions; no assertions
are removed. Archived results are from this run, not prior branch evidence.

- inventory CSV: all187files, literal metadata/runtime provenance, hash/alpha/size.
- render-audit:85viewport/DPR/scale cases /3825frames; derived hidden-frame geometry
  is labeled, actual visible rectangles also retained.
- stress:actual update functions,0.1s×36000,windON/OFF. Not an hour of wall-time.
- emma:30min away/normal focus/windOFF/direct player blocker.
- camera:actual mouse/touch/keys+actual collision/navigation,10roundtrips/input/scale.
- dynamic:retained destination/retry/resume without forced movement.
- actions:real Critical/一閃/TP/cut-in/enemy hit; screenshot taken after motion sample
  to avoid test-induced elapsed-time errors.
- battle-regression:actual enemy action followed by DEVkill,KO/Victory/race.
- prayer-item:real Prayer COMMAND; item safety via API (not full item UI coverage).
- performance:90actual RAF intervals/sample, instrumented pending timers/decode,
  CDP DOM/listener/layout. Measurement RAF is included in pending totals.
- sweep:20actual DEV routes×4viewports; not exhaustive playthrough/story proof.
- forest-bat/idle-centroid/anchor:read-onlysource + actual painted pixel soles.
- protection:all differences confined to audit docs; no production changes.

Failed/incomplete runner attempts are distinguished in the final report. Mobile
results are Chromium emulation, not physical smartphone measurements. Image-memory
sums are nominal RGBA source estimates, not OS/GPU resident memory readings.
