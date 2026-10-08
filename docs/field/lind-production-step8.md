# Lind Village — Player QA follow-up and STEP 8

Start: `8d3c7be521c207d6c3378426278ad4833b561dfc` (latest main fetched).
Scope: cow scale / Lind outdoor movement / Wind Stone assets and DEV staging only.
STEP 9 onward, formal map/story hooks, NPCs/Emma and battle changes are excluded.

## Follow-up checkpoint

- Cow: visible width 56 → 72.8 px (×1.30), same PNGs. Idle/walk bottom ground anchor retained; small pen extension accommodates sprite without crossing fence. Foot collision scales with cow.
- Pig 43 px and chicken 24 px, assets/behavior unchanged.
- Central `FieldMovement.settings`: outdoor pointer 4 → 5 px/frame; keyboard 18 → 22.5 px/input (×1.25). Original keyboard repeat model retained; no dash.
- Both paths use ≤2 px collision substeps. Pointer arrival clamps to exact destination; keyboard cancels old pointer movement; original world bounds retained.
- Interior/forest movement is outside this Lind outdoor adjustment and remains unchanged. No player walking animation exists to retime.
- Browser checks: PC 1280×720, landscape 844×390, portrait 390×844; actual livestock walk, 120s pen simulation, cow idle/walk foot anchor, unchanged other livestock, declared foot colliders, bridge crossing, water edge/dock, training gate/dummy click/tap/Enter, save guard and full preview restoration passed.
- Additional checks: thin obstacle cannot be skipped; world clamp, exact pointer arrival/no overshoot and keyboard/pointer interruption passed.
- Visual cow/fence/other livestock comparisons approved in all three viewport screenshots. Original livestock PNG bytes unchanged.

QA evidence: `qa/lind-step8/`.
