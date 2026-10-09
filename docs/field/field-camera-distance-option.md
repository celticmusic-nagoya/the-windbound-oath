# Field camera distance — extended PLAYER QA / future release design

## Current scope

Starting main: `46d5683a763f431da166b2684130865f16e46a2d`.
DEV Lind review alone supports these session-only comparison values:
1.00 / 1.15 / 1.20 / 1.25 / 1.28 / 1.30 / 1.35 / 1.40 / 1.45 /
1.50 / 1.55 / 1.60 / 1.70 / 1.80 / 1.90 / 2.00 / 2.10.
The unchanged initial value is 1.00. The release range is now confirmed: **MIN 1.00 / MAX 2.10**. The default candidate is **1.80, temporary**, to be reevaluated after Moss Forest, Dunvar Fortress and Royal Capital Caerdyn maps are complete.
Browser zoom must remain 100%. The current public initial value remains 1.00; this documentation change does not switch it to 1.80.

`FieldCamera.config` is the single frozen runtime configuration:
- `defaultScale`: the existing QA/non-review initial value, 1.
- `qaScales`: selector candidates and `setScale` validation source.
- `release`: min/default/max/step and desktop/mobile-landscape/mobile-portrait defaults, reserved, still `null` in the current DEV-only runtime; the future SETTINGS implementation will apply the approved range and reevaluated default.

The world-only rendering and inverse screen/world conversion are unchanged.
Movement, collision, coordinates, interaction distance, sprite native sizes, map/bridge geometry and speed remain unchanged.
Selection persists only for this page session. Closing DEV review restores the original camera.
No storage, device detection, additional input shortcuts, pinch zoom or SETTINGS UI is implemented.

## Approved future release design

MENU → SETTINGS → カメラ距離, with 遠い ←────●────→ 近い or 遠い / 標準 / 近い.
Internal value: `cameraScale`. Save the player's choice in localStorage and restore next launch.
Technical numeric scales need not appear in the release interface.
Device-specific defaults may differ; no device values have been selected. Do not automatically override the player choice per map.
When implementing release support, extend the existing camera activation/validation boundary;
`setScale` currently intentionally accepts only DEV review candidates while review is active.
Future settings/storage adapters must validate values against the approved 1.00–2.10 limits.

Apply only to field world distance. Do not scale Battle UI, dialogue, MENU, JOURNAL, EVENT CG,
LOCATION CARD or HUD. The UI stays outside the world transform.
PC +/- or modifier-wheel may be considered later; mobile pinch is not intended as the default
because of accidental input. SETTINGS remains the primary control.

## PLAYER QA route

GitHub Pages → DEV → リルド村 · 素材仮配置 → プレイヤー表示: Aidan A1 → カメラ.
Existing 素材へ移動 choices provide comparison locations without changing the map:
- 中央広場: 風の石 (Aidan, stone, nearby village buildings).
- Emma: エマ (character comparison).
- 家畜: 牛 / 豚 / 鶏 / 牛舎 (farm comparison).
- 橋 / 訓練場: 川を渡る橋 and training-ground objects (route/view-distance comparison).
Prioritize 1.50 / 1.60 / 1.70 / 1.80 / 1.90 / 2.00 / 2.10,
especially 1.70–2.00. High zoom necessarily reduces the world visible at once;
it does not increase interaction reach. Use ordinary movement to approach objects.

No Aidan PNG/frame/native-size changes, next-character production, A2 or STEP12 integration.


## PLAYER CAMERA ownership / future CINEMATIC CAMERA

Ordinary exploration respects the player-selected camera scale across map transitions.
If the player chooses 2.10, the next map normally keeps 2.10; do not force Lind=1.8,
Caerdyn=1.2 or House=2.0. Future localStorage restores that choice on the next launch.

FIELD CAMERA comprises PLAYER CAMERA (user distance) and CINEMATIC CAMERA
(PANORAMA / TEASER / EVENT). First-map introduction: Location Card → cinematic →
restore PLAYER CAMERA → enable control. PANORAMA introduces village/city/fort/capital/castle
landmarks; TEASER shows only a characteristic part of forest/cave/ruins/dungeon;
EVENT is story-specific framing. Only during the cinematic may the game temporarily
control position and zoom. At completion, always restore the previous player scale:
PLAYER 2.10 → cinematic zoom → PLAYER 2.10.

1.00 supports broad city walls, castles, plazas and landscapes; 2.10 supports close
inspection of actors, equipment, architecture and environment detail. Neither camera
mode may enlarge UI layers. No cinematic, SETTINGS, camera persistence, +/- shortcut
or pinch implementation is added in this collision-audit task.
