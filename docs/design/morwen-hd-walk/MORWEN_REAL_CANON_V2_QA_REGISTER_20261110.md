# MORWEN-REAL-CANON-V2 — 4-direction normalization candidate

Date: 2026-11-10. Director approved continuing with V2, subject to visual QA. **This is not a replacement of canonical source masters.**

## Delivery
User-supplied archive: `MORWEN_REAL_CANON_COLOR_SIZE_V2.zip`. This PR records its verified metadata; **the PNG bytes are not yet uploaded to the repository**.

| Direction | Normalized PNG SHA-256 | Alpha >=128 bottom |
|---|---|---:|
| front | `16c71079231b1a0f7b960a35d1e5cb1e3abfcd092ad22729924ac74c0bb0bca4` | 1558 |
| right | `55c5ce7ffaf5380eae56a79bae6fc3ddc50c5f7907a236c59bd4850c443823e1` | 1558 |
| back | `eb39bcbe0155f0b329e42cec1dc159f24d4758e362ad7a5130c14134020cb02c` | 1558 |
| left | `a4339f30cc7425521672b720aa226c510ec153c4f669b81deb48466a2dacb7e4` | 1558 |

Canvas 1200x1600 RGBA all four; SHA verified against archive manifest. Front/right colors retained in V2; back/left selectively corrected. Vertical shifts from V1: front +8px, right +10px, back +1px, left +20px.

## Outstanding acceptance gates
- [ ] Upload candidate PNGs to a **new noncanonical candidate directory**, no overwrites.
- [ ] Visual comparison of face, hat, school emblem, satchel, stockings, cape, decorations and color.
- [ ] Check actual boot contact point (alpha bounding-box bottom is insufficient).
- [ ] Check halo/fringe from semitransparent pixels.
- [ ] Compare front/right against their original pixel colors, document intentional differences.
- [ ] Independent QA, mobile 390px, Android device, production map scale.
- [ ] Director approval for replacing canonical references; until then no production switch.

The walk cycle remains blocked on the canonical artwork QA. Keep PR Draft, no main merge or website deployment.
