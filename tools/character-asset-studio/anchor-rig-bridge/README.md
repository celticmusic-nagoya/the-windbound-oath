# ANCHOR-RIG-BRIDGE-11

**PARTIAL / BLOCKED** — automatic extraction from the actual supplied generic SVG originals, derived uniform registration to the existing candidate rig, and explicitly synthetic FK/contact QA. No manual coordinate entry required. No official character images or PR #225–#229 changed; no adoption, merge, runtime integration or publication.

## Inputs and authority

Received only `ANCHOR_RIG_BRIDGE_10.zip` and `ANCHOR_TEMPLATE_v1.0 (1).zip`. Immutable originals are archived in `measurements/inputs/`; SHA/provenance is in MANIFEST.json. Standalone BRIDGE-01…09 ZIPs are **NOT_RECEIVED**, not reconstructed. BRIDGE-10 does embed `bridge08.py` and a 07-style `contact_audit.py`, preserved byte-for-byte with bridge10/test source under `qa/vendor/`. Bundled `.pyc` files are never loaded; only reviewed Python source is used.

Attached READMEs/manual-browser suggestions are source documentation, not new user instructions or authorization. This task follows the user's automatic acquisition request. The template's pre-authored left/back mirrored construction is source provenance only: no new left/right reflection is applied to coordinates, assets or the Morwen design.

The original template archive contains SVG/JSON, **no native PNG** and no walk frames. Its draft mannequin is generic, not an adopted Morwen body. PR #229 and SOURCE-05 already show actual walk/pose/root/contact data unavailable. The inherited 07B manifest is separately inventoried: one unapproved wrong-canvas pose candidate, eleven absent frames, no captured times or measured sole/root sequence. That candidate's PNG SHA is checked directly against the pinned Git blob; it is not used as a walking pose or source of inferred joints.

## Measurements

`measurements/joints.json`: 31 canonical rig IDs per view, 124 records total:

- **MEASURED 64** (16 per view): exact centre of an explicitly titled SVG joint marker, checked against authored template JSON and the matching sheet's labels/translations. These are measured **authored vector markers**, not independent physical-anatomy or raster-CV measurements.
- **DERIVED 8** (2 per view): chin uses head-centre x and explicit chin-guide y; waist uses declared centre-line x and waist-guide y. These construction rules are recorded, never labelled measured.
- **UNRESOLVED 52** (13 per view): neckTop, jawL/R, handL/R, footL/R, heel/ball/toe L/R lack unambiguous labelled source evidence. Values remain null with reasons. An ankle, the foot silhouette or the fixed ground marker is not substituted for a sole point.

Native view pixels: 384×1024, top-left origin, +x right/+y down; sheet order front/right/left/back with offsets 0/384/768/1152. Joint L/R comes from the original label (character-side), including the reversed screen positions in back view and coincident side-view markers. Guide shoulder y=232 and explicit shoulder-marker y=240 are not conflated; authored circle positions win for MEASURED records.

## Coordinate bridge

`mappings/sheet_to_rig.json` gives each crop and six-element affine matrix in PR #229's convention: subtract the sheet crop origin first, then apply `[a,b,c,d,tx,ty]`. Reuses PR #229 `rig08.affine` without changing it.

The only computed registration is **DERIVED_CANDIDATE**: align source labelled crown (192,64) and declared ground (192,984) with the existing unapproved v1.0 rig's headTop (600,175) and ground (600,1540). Uniform scale = `(1540−175)/(984−64)` = 1.483695652173913. Translation is derived from those inputs. All views use positive equal x/y scale, zero shear, no reflection. Crop bounds and matrices are explicit. This is not a measured character retarget calibration or a formal value.

Ground/crown and uniform-transform geometry PASS. `characterFitStatus=BLOCKED` and `adoptionReady=false`: corresponding joint residuals reach about 112.50 px in front/back and 79.79 px in profiles. Generic mannequin proportions cannot be silently imposed on Morwen. All transformed known points are labelled DERIVED with their original classification; unresolved values remain null. No layer PNG or PR229 import manifest is rewritten with the candidate mapping.

## Motion and contact QA

`qa/real_contact.json` runs the supplied BRIDGE-10 preflight -> BRIDGE-08 adapter against the extracted measured-only fields and the provided empty real-frame template. DERIVED values are deliberately not disguised in the legacy measured-only input. Result **BLOCKED**; real walk drift **NOT_RUN**. Full source PNG/frame sequences, sole measurements, authored time/phase and actor transforms are absent.

`qa/synthetic_frames.json` is **SYNTHETIC_ONLY**, built from the existing designed candidate rig, not from the mannequin's unresolved joints. Six authored poses at 0/100/200/300/400/500ms per direction (including left/right), parent-driven planar FK with opposite arm/leg rotations. Actor translation is explicitly computed to maintain a chosen planted heel: this constructed compensation is not observed foot planting. Bone lengths and wrist/ankle motion are tested; original artwork is not rendered or changed.

`qa/synthetic_contact.json`: contact audit PASS, two three-sample stance intervals per view, L/R max drift 0 px by construction. Injected 5px slip and invalid timestamps FAIL in tests. Technical diagrams are labelled SYNTHETIC. No synthetic frame is passed off as a real image or a completed walk asset.

## Previews and PNG QA

`previews/anchor_template_*.png`: Chromium renders of exact supplied SVGs, derived preview files only. `previews/SYNTHETIC_*.svg/.png`: separately authored technical diagrams from synthetic coordinates, drawn in world space. `qa/png_previews.json` records dimensions, real alpha and input/output SHA. Native source PNG QA is **NOT_RUN** because none was attached. Generated previews never replace source artwork.

## Run from repository root

```sh
python tools/character-asset-studio/anchor-rig-bridge/bridge11.py
python tools/character-asset-studio/anchor-rig-bridge/previews/render_previews.py
python -m unittest discover -s tools/character-asset-studio/anchor-rig-bridge/qa -p 'test_bridge11.py' -v
python -m unittest discover -s tools/character-asset-studio/anchor-rig-bridge/qa/vendor -p 'test_bridge10.py' -v
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_*.py' -v
```

Main CLI exits 2 intentionally for partial real-data BLOCKED, even when synthetic geometry/contact tests PASS. Rendering requires installed Playwright and Chromium at `/usr/bin/chromium`; all external requests are blocked. No attached code with automatic write/default-output behavior is blindly executed. Input hashes, tests, old regression IDs, integrity checks and missing-file status are in `qa/` and MANIFEST.json.

## Remaining blockers / alternatives

Standalone BRIDGE-01…09 packages, labelled evidence for the remaining 13 joints per view, complete actual frame/pose/root/contact sequences, and independent generic-to-character calibration are absent. Do not guess them or ask the user to type coordinate tables. If obtainable later, parse authored vector/rig exports directly; alternatively use an actual character rig producer's per-frame joint/contact/actor export. Controlled marker detection on an authentic original raster is another option when such a raster exists. These replace missing source evidence; they do not promote the present synthetic tests to measured animation.
