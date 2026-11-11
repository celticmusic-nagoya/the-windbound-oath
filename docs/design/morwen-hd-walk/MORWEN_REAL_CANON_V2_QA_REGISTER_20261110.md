# MORWEN-REAL-CANON-V2 — 4-direction normalization candidate

Date: 2026-11-10. Director approved continuing with V2, subject to visual QA. **This is not a replacement of canonical source masters.**

## Delivery
User-supplied archive: `MORWEN_REAL_CANON_COLOR_SIZE_V2.zip`. **2026-11-10: the four normalized PNGs were uploaded byte-identical** to `assets/candidates/morwen/real-canon-v2/` with `scripts/import_morwen_real_v2_candidate.py` (plus `IMPORT_MANIFEST.json` and the delivery `DELIVERY_MANIFEST_V2.json`). The archive's `original_*.png` were not uploaded: their SHA-256 are identical to the already-registered `assets/official/characters/morwen/hd-v2/originals/real/*.png`.

| Direction | Normalized PNG SHA-256 | Alpha >=128 bottom |
|---|---|---:|
| front | `16c71079231b1a0f7b960a35d1e5cb1e3abfcd092ad22729924ac74c0bb0bca4` | 1558 |
| right | `55c5ce7ffaf5380eae56a79bae6fc3ddc50c5f7907a236c59bd4850c443823e1` | 1558 |
| back | `eb39bcbe0155f0b329e42cec1dc159f24d4758e362ad7a5130c14134020cb02c` | 1558 |
| left | `a4339f30cc7425521672b720aa226c510ec153c4f669b81deb48466a2dacb7e4` | 1558 |

Canvas 1200x1600 RGBA all four; SHA verified against archive manifest. Front/right colors retained in V2; back/left selectively corrected. Vertical shifts from V1: front +8px, right +10px, back +1px, left +20px.

## Outstanding acceptance gates
- [x] Upload candidate PNGs to a **new noncanonical candidate directory**, no overwrites. (SHA 4/4 PASS)
- [~] Visual comparison of face, hat, school emblem, satchel, stockings, cape, decorations and color — Claude self-QA: no inconsistency found at overview scale (hat/flower/ribbon/crystal side, bob hair, glasses, emblem, satchel side, thigh-highs, boots). Strap path and vial pouch side: NOT_VERIFIED. Director visual approval: NOT_RUN.
- [x] Check actual boot contact point — **FAIL**: sole row identical (y=1558, alpha>=128) but boot centre x front 578.5 / right 696.5 / back 564.5 / left 521.0 (spread 175.5 px, anchor x=600); ground 1558 differs from registered display anchor y=1540.
- [~] Check halo/fringe — no visible light halo on a dark background in head crops; full silhouette: NOT_VERIFIED.
- [x] Compare colors — front mean RGB identical to original; right within 0.6 (translation/resampling); back and left darkened (declared color_adjusted). Perceptual equivalence: NOT_VERIFIED.
- [ ] Independent QA, mobile 390px, Android device, production map scale.
- [ ] Director approval for replacing canonical references; until then no production switch.

The walk cycle remains blocked on the canonical artwork QA. Keep PR Draft, no main merge or website deployment.

QA report: `docs/qa/evidence/morwen-real-canon-v2/qa_report.json` (`python scripts/qa_morwen_real_canon_v2.py`, 23 PASS / 2 FAIL). Evidence images in the same folder.
