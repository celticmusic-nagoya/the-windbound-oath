# Morwen field sprite: common palette spec (DRAFT, from ART-74D)

Status: **DRAFT**. This spec has not been applied to the right walk 72, the back view or the front view, and will not be until it is approved. The machine-readable version is `PALETTE_SPEC_MORWEN_74D.json`.

## Source
- The official left profile in `assets/official/characters/morwen/turnaround/` on `main` (SHA-256 `d858c428…`).
- For each part, OKLab statistics were measured: lightness quantiles 5/25/50/75/95 %, median chroma and hue. These are the part targets.
- The front and back turnaround images use the same costume, so the same targets apply to every direction. Before use, check them against the back and front images.

## Part targets (OKLab; L = lightness, C = chroma, h = hue)
| Part | L 5 / 25 / 50 / 75 / 95 % | C median | h |
|---|---|---|---|
| Hat (crown and brim) | .200 / .290 / .365 / .430 / .560 | .073 | 318 |
| Hair | .179 / .271 / .365 / .415 / .444 | .057 | 332 |
| Collar bow | .190 / .333 / .442 / .625 / .843 | .142 | 315 |
| Jacket / capelet | .160 / .286 / .379 / .469 / .750 | .070 | 317 |
| Skirt | .189 / .323 / .431 / .587 / .700 | .074 | 318 |
| Mantle (outer side) | .190 / .290 / .370 / .470 / .680 | .104 | 314 |
| Potions | .339 / .537 / .661 / .849 / .989 | .102 | 322 |
| Knee socks (ramp, 5 steps) | .20 / .29 / .37 / .44 / .52 | .050 | 354 |
| Boots (ramp, 6 steps incl. gloss) | .13 / .20 / .27 / .35 / .46 / .64 | .055 | 322 |
| Gold (ramp) | .50 / .62 / .73 / .83 / .93 | .115 | 72 |

## Rules
1. **Per part, not global.**
   - Lightness: quantile-map each part's lightness to its target.
   - Chroma: target chroma × 1.25. Small sprite areas read duller than the painted sheet.
   - Hue: move to the target hue, keeping 35 % of the part's own hue variation.
2. **Gold.** Use one antique-gold ramp, and keep a dark step for edge definition. Single-pixel gold specks with no gold neighbour inside cloth become cloth. Trims and ornament lines stay.
3. **Untouched.** Skin, eyes, glasses, earring, white frills and lining highlights.
4. **Socks and boots.**
   - Socks are lighter, warm mauve: mid L ≈ .37. Boots are darker, purple-black leather: mid L ≈ .27. This difference must survive at 48 px.
   - The boot top sits at 0.5 of knee→ankle. The skin band and garter above the sock welt stay as they are.
5. **Outline.** Keep (12, 2, 12).
6. **Body shape and head ratio.** Not changed by colour work.

## Open points (approval needed before any other direction is changed)
- Right 72, back and front: apply the same targets by re-running the part-wise mapping with part masks for each direction. Their pixels stay unchanged until approval.
- On dark backgrounds, the deep purple hat and mantle lose some edge contrast. Third-party QA should judge whether a lighter outline on the lit side is needed.
