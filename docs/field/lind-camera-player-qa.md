# Lind field camera PLAYER QA

Start baseline: `c380c13112b6a7ec2af0c81ee48dc27a482f89cd`.
Branch: `work/lind-camera-qa`.
Aidan A1 is formally PLAYER QA PASS; its PNGs, animation adapter and source sprite size are unchanged.

## Source audit and implementation

The Lind world is a 2200×1550 absolute DOM canvas. Previously `camera()` translated it using the player position; pointer input subtracted its screen rectangle and the (17,42) foot anchor. Collision, NPC proximity and navigation operate in world units. Interiors and Moss Forest have separate cameras/inputs.

`FieldCamera` now provides world-only rendering and forward/inverse screen/world conversion. It scales the world parent, not HTML, the browser, UI or individual sprites. In DEV review it centers the actor body within the visible field below the existing toolbar and clamps the camera against the map's real extent divided by scale. It measures the visible game viewport, accounting for the existing game container's offset. No map layout or collider changes are involved. Outside review the effective scale is always 1.00 and the ordinary camera follows the established player-origin behavior. UI choice is session-only and is not added to saves or settings.

The shared inverse conversion subtracts the actual rendered world screen origin, divides by rendered scale, and only then subtracts the unchanged player foot anchor. The existing navigation, speed, X/Y sweep, wall slide and corner assist algorithms are untouched. Element-based NPC click/tap remains native; interaction distances stay in world units.

The `カメラ` dropdown shares the Wind Stone control row. Options: **1.00x, 1.15x, 1.20x, 1.25x, 1.28x, 1.30x, 1.35x**. Initial selection: **1.00x**. Switching requires no reload. The selected QA choice remains available when reopening review, but closing review immediately restores effective rendering to 1.00x. No final standard scale is chosen.

## QA results

| Viewport | Browser zoom | All seven scales | Bridge round trips per scale | Result |
|---|---|---|---|---|
| PC 1280×720 | 100% | 7/7 | 5 | PASS |
| Mobile landscape 844×390 | 100% | 7/7 | 5 | PASS |
| Mobile portrait 390×844 | 100% | 7/7 | 5 | PASS |
| Desktop 1920×1080 | 100% | 7/7 | 5 | PASS |

140 total round trips. Real DOM mouse/touch input uses independently measured screen coordinates; deterministic stepping of the existing navigation verifies swept collision safety, constant ≤5 world units per pointer step and arrival at the screen-selected destination. Actual arrows/WASD remain 22.5 world units per input. All scales pass map edges/corners, close/diagonal/visible-edge destinations, bridge entrance/exit, NPC click/tap/Enter, wall sliding, corner assist and blocked river destinations. Zoom changes preserve world position and an outstanding destination. Review exit restores saved live coordinates/story/storage.

Separate actual RAF playback at 1.30x passes idle 4/4, walk 16/16 and visual foot registration at all three required sizes. Source PNG audit passes SHA equality, RGBA and true alpha 20/20. Aidan's intrinsic body height remains 44 world pixels; camera magnifies it along with NPCs/buildings/animals rather than resizing it separately.

Wind Stone NORMAL/GLOW/OFF and interaction pass at every scale; the monument remains below the toolbar. Wind-driven motion and birds stop when wind is OFF; water continues. The dedicated bird regression suite also passes takeoff/flock/wind/water/lifecycle at all three required sizes.

Normal/Raider COMMAND, normal attack, 一閃, defend, enemy actions/turns, DEV instant kill, KO/Victory and race protection pass. Review at 1.35x is closed before battle and effective camera scale returns to 1. Raider HP stays 1250; sprite/HUD geometry exactly matches the start baseline for all three viewports. Battle source/CSS/assets have no diff.

Image 404: **0**. JS exceptions: **0**. Console errors: **0**. Legacy/invalid literal asset references: **0**. Screen-to-world input tests have no systematic coordinate error (floating point tolerance <0.0001 world unit).

Evidence and reproducible scripts: [qa/lind-camera/README.md](qa/lind-camera/README.md).

## Compare and stop

DEV → リルド村・素材仮配置 → カメラ dropdown. Compare 1.25 / 1.28 / 1.30 directly, then check 1.00 and 1.35 for context. PC comparison captures are at the same Emma location:

- [1.00x](qa/lind-camera/camera-1280-1.00.png)
- [1.25x](qa/lind-camera/camera-1280-1.25.png)
- [1.28x](qa/lind-camera/camera-1280-1.28.png)
- [1.30x](qa/lind-camera/camera-1280-1.30.png)
- [1.35x](qa/lind-camera/camera-1280-1.35.png)

The work branch is ready for camera PLAYER QA. **Main is not merged and GitHub Pages still publishes the approved previous main; the camera selector is not yet on that public page.** No A2/Fiona/Lou/STEP12/story/settings work is included. Await the user's camera choice and any subsequent publication instruction.

CAMERA PLAYER QA READY
