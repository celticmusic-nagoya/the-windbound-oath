# Field camera distance — extended PLAYER QA / future release design

## Current scope

Starting main: `46d5683a763f431da166b2684130865f16e46a2d`.
DEV Lind review alone supports these session-only comparison values:
1.00 / 1.15 / 1.20 / 1.25 / 1.28 / 1.30 / 1.35 / 1.40 / 1.45 /
1.50 / 1.55 / 1.60 / 1.70 / 1.80 / 1.90 / 2.00 / 2.10.
The unchanged initial value is 1.00. These are **QA candidates**, not final release min/default/max.
Browser zoom must remain 100%. PLAYER QA will decide visibility preferences; this task does not choose them.

`FieldCamera.config` is the single frozen runtime configuration:
- `defaultScale`: the existing QA/non-review initial value, 1.
- `qaScales`: selector candidates and `setScale` validation source.
- `release`: min/default/max/step and desktop/mobile-landscape/mobile-portrait defaults, all `null` pending PLAYER QA.

The world-only rendering and inverse screen/world conversion are unchanged.
Movement, collision, coordinates, interaction distance, sprite native sizes, map/bridge geometry and speed remain unchanged.
Selection persists only for this page session. Closing DEV review restores the original camera.
No storage, device detection, additional input shortcuts, pinch zoom or SETTINGS UI is implemented.

## Approved future release design

MENU → SETTINGS → カメラ距離, with 遠い ←────●────→ 近い or 遠い / 標準 / 近い.
Internal value: `cameraScale`. Save the player's choice in localStorage and restore next launch.
Technical numeric scales need not appear in the release interface.
Device-specific defaults may differ; no device values have been selected.
When implementing release support, extend the existing camera activation/validation boundary;
`setScale` currently intentionally accepts only DEV review candidates while review is active.
Future settings/storage adapters must validate values against the final approved limits rather than the QA list.

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
