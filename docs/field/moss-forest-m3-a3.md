# Moss Forest M3 — AREA 3 古樹の聖域 runtime + seal

- Map: `data/maps/moss_forest_03_ancient_grove.json` (8400×6600, k=2.5), exported by `tools/moss/export_runtime.py` from `tools/moss/design/moss_forest_03_ancient_grove.json`.
- Dev page: `dev/moss-forest.html?map=../data/maps/moss_forest_03_ancient_grove.json[&flags=moss_a3_seal_open]`.
- Seal: `cb_a3_seal` rect [3846,3271,128,18], `enabledWhen {moss_a3_seal_open:false}` evaluated live by `FieldCollision.compileMap`. Dev API: `ForestDev.setFlag(name,bool)`, `symbolsLeft`, `defeatSymbol(i)`, `sealNodes`. Dev stand-ins for forestGob1..3: touching one removes it; at 3 the flag is set. Seal visual is a single placeholder node, present only while closed.
- Tests: `node tests/moss/scatter.test.js` (A1–A3), `python3 tests/moss/seal_a3.py` (closed/open walk, treasure, rest, 60× toggle, symbol-driven open, node budget).
- Real index.html wiring (story, saves, effects) is M4.
