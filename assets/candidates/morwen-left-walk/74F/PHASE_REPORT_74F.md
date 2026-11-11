# ART-74F: phase report (pelvis, shoulder, arm, cloth)

12 frames per cycle; 1 frame = 8.33 % of the cycle. "Lag" is measured behind the pelvis, except for the arm.
Values are per frame, F00…F11. +1 means 1 px down on screen. dx is in right-view coordinates (+ = forward); the PNGs are mirrored for the left walk.

| Part | Lag (requested) | 74F-B | 74F-C | Values (C) |
|---|---|---|---|---|
| Pelvis (hip joint, skirt) | 0 | 0 | 0 | dy `+1 +1 0 −1 −1 0 +1 +1 0 −1 −1 0`, dx `0 0 0 +1 +1 0 0 0 0 +1 +1 0` |
| Chest | 0.5–1 f | 1 f | 1 f | dy `0 +1 +1 0 −1 −1 0 +1 +1 0 −1 −1` |
| Shoulder (capelet front) | ~1 f | 1 f, opposite to the pelvis dx | same | dx `0 0 0 0 −1 −1 0 0 0 0 −1 −1` |
| Head posture | ~0.5 f | Down only after 2 frames of chest-down (0.5 f) | same | dy `0 0 +1 0 0 0 0 0 +1 0 0 0` |
| Arm (whole) | Lead the legs 0.06 cycle (74E, protected) | Same as 74E | same | dx `−2 −1 0 +1 +2 +2 +2 +1 0 −1 −2 −2` |
| Hand / cuff | Behind the forearm | – | 0.5 f behind the forearm | dx `−2 −2 −1 0 +1 +2 +2 +2 +1 0 −1 −2` |
| Collar ribbon | – | 74E (1/8 cycle = 1.5 f) | 1 f | dy `0 +1 +1 0 0 0 0 +1 +1 0 0 0` |
| Potions | – | 74E (1.5 f) | 1 f (dy only; a dx would open holes) | dy `0 +1 +1 0 0 0 0 +1 +1 0 0 0` |
| Hair tips | ~1.5 f | 74E (1.5 f) | 1.5 f (down when the pelvis was low 1 and 2 frames ago) | dy `0 0 +1 0 0 0 0 0 +1 0 0 0` |
| Mantle | ~1.5 f | 74E (1.5 f) | 2 f, held for 2 frames | dy `0 0 +1 +1 +1 0 0 0 +1 +1 +1 0`, dx `−2 −1 −1 −1 −1 −2 −2 −1 −1 −1 −1 −2` |
| Skirt hem | – | 74E | 1 f | `0 −1 −1 0 0 0 0 −1 −1 0 0 0` |

Notes:
- Attached cloth parts move with the body through the per-row level map. Only free ends get their own lag: hair tips, mantle, collar ribbon, skirt hem and potions.
- No part shares its phase with all the others.
- Amplitudes stay at 1–2 px at 96 px and 0–1 px at 48 px; nothing is amplified beyond 74E.
