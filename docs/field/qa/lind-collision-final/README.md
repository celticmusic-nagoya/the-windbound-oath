# Lind building collision — main integration and public final lock

Integration baseline: `fa95f9646dfc70f37abfb4f64ad2b9e84ece424c`.
Source: `work/lind-front-collision-fix`, `0b92479d445ebcf31d41a9d285959306634115f5`.
Source checkpoints: `5890e2a`, `4c3aeb7`, `0b92479`.
Normal fast-forward integration and ordinary main push; no history rewrite.
Public QA target: https://celticmusic-nagoya.github.io/the-windbound-oath/

## Root cause and fix

The old item-shop wall and barrel rectangles left a ground-contact gap. At
player origin `(283.8,620.25)`, the feet started at x289.8/y652.25, beyond the
old barrel right edge289.2 and below the old wall bottom650.76. The visible
PNG still contained front props there. Image-bottom depth689 also incorrectly
occluded the player standing on clear central steps. The fix uses individual
ground-contact props and facade depth650.76; player depth and anchor are unchanged.

All14 profiles separate building/foundation/posts from front barrels, crates,
flowerbeds, fences, displays and loads. Door approach is a narrow metadata/debug
lane, never a subtraction from walls. Roof/awning overlap with the upper body is
allowed when feet remain outside ground solids. Closed storage and closed pens
stay closed; the training porch and existing chicken gate remain accessible.

## Future building rule

Use GROUND CONTACT, not the whole-image bounding box. Separate BUILDING SOLID,
FRONT PROP SOLID and DOOR APPROACH as needed. The player footprint remains
22×10 with offset(6,32), ground anchor(17,42), native44-world-pixel body.
Do not change actor origin or camera/movement to compensate for image bounds.
This rule applies to future shops, inns, homes, guilds, blacksmiths and cities.

## QA method and scope

Fresh Chromium sessions loaded the actual public HTTPS page through the
configured proxy, with normal certificate validation. No public application
responses were replaced by local source. Cache-busted public HTML/JS/CSS were
compared byte-for-byte with main:42files match, including all4 changed runtime files.

Public ground QA covers all14 at1280×720,1.00x, and5representative types
(shop, house02, barn, pigsty, training shed) at4scales in4viewports.
Each case checks4manual PNG contacts,20Arrow/WASD event-handler approaches,
native keyboard front stops,3real mouse/tap door routes, blocked-prop clicks,
a real destination behind a corner, overlay world alignment and debug lifecycle.
Initial positioning and clock stepping are test fixtures; movement/collision
and navigation remain the application's actual code. Deep2-lap perimeter
checks are retained in the source QA and re-run for5representatives on local source.
Public input/camera tests also exercise wall sliding, corner assist, river blocking
and bridge traversal. Mobile checks are MOBILE EMULATION, not physical devices.

Viewport:1280×720 /1920×1080 /844×390 /390×844; browser zoom100%.
Camera:1.00 /1.50 /1.80 /2.10.
Public bridge checks:5mouse/tap and5keyboard roundtrips per viewport/scale,
80roundtrips for each input family. No navigation implementation change.

## Regression protection

Aidan PNGs unchanged,4idle/16walk and last-facing idle/anchor/sizing verified.
Villagers/Emma interaction and patrol, birds/takeoff, livestock, Wind Stone
NORMAL/GLOW/OFF and wind OFF with water still flowing are checked separately.
Battle code/assets are unchanged: normal attack,一閃,guard,enemy turn,COMMAND,
DEVkill,KO,Victory and stale-timer protection. RaiderHP1250, giant scale and
HUD outside the sprite remain unchanged.

## Dynamic livestock / auto movement follow-up

Building ground collision and moving-actor interference are separate issues.
The moving-pig QA uses a controlled WALK fixture on the actual public page,
real mouse/tap/keyboard input and records positions, destination and navigation.
No pigAI, NPCcollision, navigation, pathfinding, wallslide or cornerassist changes
are made. Moving-actor interference is reserved for a separate future issue.

Controlled public moving-pig results: REPRODUCED at844×390,2.10x.
Three mouse and three tap trials stop with `outcome=blocked`, `staticBlocked=false`,
`animalBlocked=true`. Aidan `(1196.5,970)`, pig x≈1195.1/y985,
requested destination `(1196.5,939.175)`. Moving the pig away and selecting
again arrives. Three native keyboard trials move to y947.5 without interference.
This is deterministic overlap setup, not a claim about spontaneous frequency.
See `pig-public.json` for full snapshots. It does not invalidate building final lock.

## Reproduction

Serve the repository locally for source QA. For actual public QA use
`LIND_QA_PUBLIC=1`, `LIND_QA_URL=https://celticmusic-nagoya.github.io/the-windbound-oath/`,
configured `HTTPS_PROXY`, installed Playwright and Chromium `/usr/bin/chromium`.
`front-qa.cjs` accepts `FRONT_QA_OUT`, `FRONT_QA_VIEWS`, `FRONT_QA_ONLY`,
`FRONT_QA_SCALES`; defaults cover all14 and4scales/4views.
`camera.cjs` accepts `LIND_CAMERA_QA_OUT` and `LIND_QA_VIEWPORTS`.
`pig.cjs` contains a controlled moving-animal fixture only; it changes no files.
`verify-public.py` is the42-file byte comparison used in this session.
The other regression runners are retained in existing QA folders; the JSON
results here were freshly recorded from the public URL.

## Final result

FINAL RESULT: PASS WITH WARNINGS.
LIND BUILDING COLLISION FINAL LOCK: PASS.

- All14buildings: front/side/both corners/front props/door approach PASS.
- No excessive invisible-wall stop in tested approaches; overlays align with world solids.
- Public94building cases:376manual contacts,1880keyboard approaches,282door pointer routes.
- Fourviewports/fourcamera scales PASS; debug ON/OFF/lifecycle PASS.
- Keyboard/click/tap, wallslide, cornerassist, blocked destination and river/bridge PASS.
- Aidan4/4IDLE,16/16WALK; unchanged20PNGs/one sword/native size/ground anchor/22×10feet.
- Villagers/Emma/birds/livestock/WindStone/wind OFF with flowing water PASS.
- Battle attack/一閃/defend/enemyturn/COMMAND/DEVkill/KO/Victory PASS.
- Raider1250, giant scale and independent HUD retained; Battle sources/assets unchanged.
- Image404/JavaScript exceptions/console errors/legacy asset references:0.

Minimum premerge tests completed before fast-forward: representative5types at
1.00/1.50, camera/bridge4scales/4views, Aidan/NPC/Emma/bird/wind/water and Battle.
The extended20-case same-source perimeter run finished during deployment;
its source bytes are identical to the integrated commit.

Warnings: controlled moving-livestock overlap stops automatic movement as described
above; separate dynamic-avoidance follow-up only. Mobile is emulated, not physical
hardware. No new phase, asset generation, map/story integration or Battle work.

Public evidence: [PC shop contact](evidence/public-pc-shop-contact.png),
[PC shop clear steps](evidence/public-pc-shop-door.png),
[mobile pig approach](evidence/public-mobile-pig-door.png),
[mobile training porch](evidence/public-mobile-training-door.png).
Machine-readable coverage: `summary.json`, `public-all14.json`, `public-scales.json`,
`public-camera.json`, regression JSONs and `pig-public.json`.

LIND COLLISION FINAL LOCK — PUBLIC PLAYER QA READY
