# STEP B resume — dynamic-navigation checkpoint

Start: `8eef59fdc91d7b114b33e716f71431b9a1ebd136`.
Source: `work/lind-visual-polish-village-life`.
Main remains `ac3707698018aa9efe016e04776ba3d1d1be833e`.

**Navigation foundation: PASS. Full STEP B: incomplete, not PLAYER QA READY.**
No fisherman/children/villager-life/Emma animation has been implemented at this
checkpoint. The intended implementation order is retained.

## Runtime change

Only `js/field/field-navigation.js` and `js/field/lind-review.js` change.
The active Lind review exposes separate static/dynamic predicates on the existing
combined collision callback. The combined predicate still governs keyboard/native
movement. Static destination validation/geometry remain locked.

Navigation first uses its existing bounded planner to respect live actors. If a
dynamic actor occupies the start/destination or makes the live plan unavailable,
it falls back to a statically reachable route instead of discarding the target.
Live movement still sweeps feet against the combined predicate; contact never
pushes the player or an NPC. During temporary contact, the same destination is
retained, with `waiting-actor` status. Actor-wait frames do not consume the original
movement-progress timeout. Normal movement resumes on the existing RAF once clear.

For an actor that stays ahead, the existing planner attempts a live detour after
30 waiting frames and subsequently no more often than once per 120 waiting frames.
Detours use 2px clearance around dynamic actors only; locked static shapes are
not enlarged. If no live detour exists, the destination is retained. No new
pathfinding engine or timers were added. Keyboard cancel/new pointer destination
continue to replace the pending movement normally.

A permanently occupied destination stays pending until the actor leaves or the
player cancels/selects another destination. There is no forced movement through
an NPC. This fixes lost-destination behavior, rather than removing all contact
pauses or claiming complete crowd navigation.

## Tests and limits

- Four viewports: 1280×720, 1920×1080, 844×390, 390×844.
- Actual mouse/tap pointer selection and normal RAF: pig crosses the player foot,
  target retained during contact, pig moves away, arrival without another click.
- Dynamic destination accepted; manual keyboard cancels auto movement; a locked
  building destination remains unavailable.
- Existing child/villager/multiple-actor contact fixtures preserve the destination
  and do not push the player. These are **controlled collision fixtures**, not
  newly implemented child AI or a claim that the chase feature passed.
- Existing planner with a late stationary actor: wait/detour/arrival. Occupied
  destination: 4,000 navigation calls retain target, then resume after clearing.
- Legacy callbacks: seven cases compare old/new x/y/target/outcome at every step
  (straight, diagonal, wall detour, blocked goal, no route, clamped destination, legacy timeout).
- Existing camera/input/bridge/wall-slide/corner-assist/river/interaction/wind/water
  suite runs at four viewports and 1.00/1.50/1.80/2.10x. See `camera-qa.json`.
- Live Aidan/Fiona attacks, 一閃, guard/enemy turn and normal/Raider COMMAND,
  DEV kill during motion, KO/Victory/race protection: three viewport regressions.
  Raider remains HP1250 with an independent HUD and existing huge visual.
- Runtime PNGs, Aidan, camera, static collision data, Terrain implementation and
  Battle code/CSS are unchanged. See `source-protection.json`.
- Image404, JS exceptions, console errors and legacy runtime asset references:
  zero in the executed runs/search. Full STEP B integrated QA and child long
  simulation have **not** run because the subsequent features are not implemented.
- Physical mobile remains untested. Camera source default remains 1.00x; the
  provisional 1.80x specification discrepancy is acknowledged and unchanged.

## Provided assets

The new fisherman sheet is visible in the conversation, and the resume instruction
explicitly authorizes splitting it as production art. **The original PNG bytes
are not available as a downloaded file in this workspace.** Available attachment
files and repository assets were inspected; they contain the old fisherman PNG
and historical ZIPs, but no new fisherman sheet file/download identifier.
The conversation display was resized from 2172×724 to 2048×683. That preview cannot
establish actual alpha/margins/frame boundaries. No equal-grid assumption,
replacement generation, old-fisherman edit, or crop from the preview was made.

Resume prerequisite: attach the **original fisherman sheet as a PNG file or ZIP**.
Then inspect dimensions/alpha/frame regions/anchors before production splitting,
and proceed with fisherman animation, children, general villagers/Emma and final QA.
Visible red fragments in the preview are not, by themselves, an alpha/background
quality verdict; inspect actual file data before making a decision.

`eidan_fiona_lou.zip` was downloaded and its sole `eidan_fiona_lou.png` compared
byte-for-byte with the already preserved reference:
`docs/art/reference/characters/aidan-fiona-lou-field-reference.png`.
They are identical, SHA256
`d5cfebcd2dabfbdbc4a984a309dd356fb1105546664c3fdb3d7fc624affeafc4`.
It remains reference-only; no character was cropped or implemented from it.

## Reproduction

Start the repository static server on 127.0.0.1:8015. The cloud environment has
Playwright and `/usr/bin/chromium`. QA output goes outside the repository.

```sh
mkdir -p /workspace/onboarding/lind-village-life-resume
NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules \
node docs/field/qa/lind-village-life-navigation/dynamic-qa.cjs
node docs/field/qa/lind-village-life-navigation/legacy-qa.cjs
node docs/field/qa/lind-village-life-navigation/detour-qa.cjs
```

Main/GitHub Pages were not updated. Do not treat this checkpoint as completed
STEP B or merge it as a public PLAYER QA release.
