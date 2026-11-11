# MORWEN-MOTION-SOURCE-05 — opt-in frame-data source

This tool generates source/coordinate records from an explicit plan and SHA-pinned measurements. It does **not** animate/draw a PNG, synthesize a v1.0 pose sequence, reuse a still as six walk frames, or promote historical sprites to adopted art. The requested actual v1.0 animation source remains BLOCKED until authored pose and adopted raster frames exist. This is the smallest usable data-input/coordinate evaluation layer, not a completed walking-animation generator.

## Current evidence

- `morwen_walk6.source-plan.json` has six explicit slots for each facing direction. `left`/`right` refer to facing; anatomical foot `L`/`R` is independent.
- The left delivery file is AWAITING_ART / NOT_DRAWN. Its DEV directive plans six unique frames at nominal 10fps, with contact events F1 and F4, but supplies no actual PNGs or per-foot measurements. `plannedTimeMs` is a schedule, never an observed timestamp. Actual `timeMs` stays null.
- No approved right six-frame specification or frame mapping was located. Six right IDs are task slots only; even planned timing/path stays null.
- Official/canonical images are static views. Older 74I/75/76/77 chibi walks are SUPERSEDED in `data/morwen-hd-canonical-v2.json`; candidate 72 local ankles are not v1.0 sole contacts. No candidate is substituted.

## Usage

From repository root (output must be a **new** JSON in this task's QA directory):

```sh
python tools/character-asset-studio/motion-source/generate_frame_data.py tools/character-asset-studio/motion-source/morwen_walk6.source-plan.json tools/character-asset-studio/qa/morwen-motion-source-05/FRAME_DATA.json
```

Current result: exit 2, BLOCKED, 12 incomplete slots, no measured contact coordinates, `export06Allowed=false`. If replaying, choose a fresh task-local filename; overwrite is refused. No runtime imports, timers, file mutation or PNG generation occurs. `REVIEW_REQUIRED` for fully supplied input is still not approval and never automatically starts Export-06.

## Source contract

Each plan slot has a stable task `id`, optional original `sourceFrameId`, actual `timeMs`, an `image` reference `{path, sha256}`, optional SHA-pinned `adoptionReceipt`, and optional SHA-pinned `measurement`. Paths must resolve inside the repository. A supplied image must decode as PNG; SHA must match before using it. Missing sources are left null, never loaded from a fallback. `plannedPath` and `plannedTimeMs` are explicitly unused hints, not evidence.

A receipt JSON binds `kind: "walk-frame"`, `status: "DIRECTOR_APPROVED"`, exact `frameId`, `direction` and `image` reference. Binding bytes checks consistency only: human authority and adoption must be independently reviewed; copying these labels cannot establish real approval. Existing receipts/PNG assets are never rewritten. The current plan has **no** receipts or frame images.

A measurement JSON uses `schema: "cas/frame-contact-measurement/1.0"`, exact matching `frameId`, `direction`, `timeMs`, `image`, `coordinateSystem: "imagePx:x-right:y-down:top-left"`, optional `actorTransform`, and anatomical `feet.L` / `feet.R`. Each foot explicitly records `phase`, `stanceId`, selected `contactPoint` (`heel`, `ball`, `toe`), `jointId` (e.g. `heelL`, never inferred near/far), and `localPx` or null. Measured records must be supplied by the actual frame producer or an independently evidenced measurement process. No measurements have been supplied here. `SOURCE_RECORDED` means a pinned source reported the value; it does not claim independent visual verification or anatomical correctness.

## Coordinates and transforms

1. **Local:** original frame canvas pixels, origin at the top-left, +x right, +y down. A projected/posed sole coordinate must already be expressed in that image space. This tool never treats 3D rig joints or sprite-local ankle joints as projected sole contacts.
2. **Actor/root transform:** explicitly supplied per actual frame: `translationPx: [tx,ty]`, positive uniform `scale`, and `rotationDeg`. Rotation is clockwise in y-down coordinates. No identity/root movement is assumed when data is absent.
3. **World:** +x right/+y down, world pixels, `world = translationPx + scale * R(rotationDeg) * localPx`. These are pre-camera coordinates. Camera offset/zoom and CSS viewport pixels are excluded. No 3D-to-2D projection is inferred.
4. **Anchor placement:** existing `MorwenHDCanonical.placeDisplay` in `js/field/morwen-hd-canonical.js` supplies still-preview left/top from the fixed (600,1540) anchor, display scale and measured anchor correction. That is an image-placement reference, not per-foot contact. It is not imported as a motion transform.
5. **Unknowns:** no image, transform, foot side, phase, stanceId, selected sole point, local/world coordinate or time can be derived from the fixed ground marker. Missing data stays null with blockers. A stance/swing label is authored input, not guessed from pixel bounds.

The generator's output is `cas/motion-source-data/1.0` (incomplete data is allowed), intentionally distinct from `cas/real-motion-contact-export/1.0` (complete authenticated motion evidence). Do not feed the incomplete source inventory to the Export-04 converter as though it were a real export. Export-06 remains blocked pending independent checks of adoption, frame correspondence, phase, mapping, transforms and actual contacts.

## Tests

```sh
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_motion_source_05.py' -v
```

Tests use temporary synthetic PNGs and receipt/measurement records. They verify frame identity, hashes, side inversion rejection, exact explicit transform math, duplicate IDs, invalid transforms and unknown preservation. They are not real-motion accuracy or human adoption tests.
