# Independent static review — PLAYER-WALK-UP-06-QA

PR153 exact `c15a715fe450e76820153e71ea7b04e70e258d6d`. Read-only art review; no candidate generation or repair script executed.

**Static visual verdict: PASS with disclosed small residuals. Dynamic five-pose gait remains pending actual browser evidence. No formal adoption recommendation is implied by the static result.**

## Independently measured scope

- Candidate SHA256 `1bde96684c85739e821e8c7e5e8f07831b8819414569d07d6a3bbb3613e80dfd`.
- RGBA2048×1280, bottomalpha>128 row1227, same as formal03/PR152. PNG does not embed game anchor; runtime owner must verify1024/1230 registration separately.
- Versus formal03:18,549 changed pixels; **0 outside original37,699px mask plus29px extension**.
- Versus PR152:248 changed pixels, inclusive bbox[1055,973,1135,1108];216 outline-mask pixels all changed,32 remaining gap-fill pixels. Thus this is a local correction, not whole-leg regeneration.
- Extension29px inclusive bbox[1123,973,1135,996], exact coordinates and SHA metrics in `metrics.json`.
- No formal03 pixel withalpha>200 outside original mask changed. **Onealpha200 pixel did change**; avoid equatingthreshold>200 with all opaque/semiopaque formal pixels protected.

## Documentation discrepancies (not hidden)

1. Actual formal03 alpha values at29 extension pixels range **26–200**, not all26–67 and not transparent0. Higher values include70,75,83,88,104,107,200. The29px operation fills a recorded narrow semitransparent boundary, which appears visually justified, but its range must be described accurately.
2. Threshold24 global enclosed pixels remain20 in formal03, PR152 and PR153, **all outside inspected leg zone/originalmask/extension**. Candidate leg-zone holes0 at24,128,200; global0 at128/200. “All global holes0 at24” is false.
3. Actual alpha>200 contiguous planted-boot edge,25-row closing: maximum notch **8→1 native px**, not8→0. Author target profile and final antialiased PNG are different measurements. One residual native pixel is0.0625CSS px at gameplay scale; not a rejection reason.

## Visual assessment

Own `own-legs-black-white.png` and `own-outline-knee-black-white.png` show formal03/PR152/PR153 at the same coordinates on both backgrounds, with spatial2×nearest enlargement. The planted boot formerly had a noticeable inward notch between armor sections; PR153 smooths that exposed contour while keeping plate highlights and boot volume. No newly detached ankle/sole, hard horizontal knee cut, or isolated cloth fragment is evident in the inspected native crops. The216 additions are consistent with continuing existing armor/edge shading, rather than attaching another foot.

The narrow filled area beside the new knee/cloth underside removes small dark/white pinpricks in the comparison. It slightly expands an antialiased boundary; the change must not be described as preserving every original edge byte. With exact29px authorization/recording, the visible correction is proportionate.

The raised right boot/sole has a softer, more uniform shading treatment than the richly segmented existing planted armor; faint horizontal sole bands remain. It is not grossly incompatible, and the difference is subtle in own336×210 fullcanvas render (128×80CSS atDPR2.625). This plate is a static resampling, **not an Android device capture or moving gait PASS**. Native knee, cuff and sole remain attached; pose/weight transfer needs actual sequence review.

## Reproduction

`python analyze.py --repo <checkout> --out <output>` reads originals/candidates/masks and writes only output. `metrics.json` includes hashes, all extension coordinates, alpha histogram, holes and actual edge profiles. This is an independently implemented measurement, not execution of Claude's repair code. SciPy/NumPy/Pillow required. Exact candidate source remains unchanged.
