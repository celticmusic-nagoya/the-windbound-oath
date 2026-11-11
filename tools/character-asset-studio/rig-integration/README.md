# MORWEN-RIG-INTEGRATION-PREP-08

Development-only, read-only integration adapter. New files only; SOURCE-05, PR #225–#228, official PNGs and rig references remain unchanged. No renderer, image generation, adoption, runtime/game connection or publication.

## Dependency / execution path

`import_rig.intake` -> `SOURCE-05.generate` -> SHA-pinned `poseInput` validation -> existing `convert_real_motion_export.convert` -> existing `audit_stance_contact.audit_stance`, independently per facing direction. Source05's existing image/measurement/receipt contract is reused without writing intermediate inputs or changing its source. Right/left frame IDs and original SOURCE-05 slot counts (six each) are preserved.

```sh
python tools/character-asset-studio/rig-integration/import_rig.py tools/character-asset-studio/rig-integration/morwen.import.template.json tools/character-asset-studio/motion-source/morwen_walk6.source-plan.json
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_rig_integration_08.py' -v
```

CLI emits JSON to stdout only, exit PASS=0, FAIL=1, BLOCKED=2. Present template intentionally exits 2. Synthetic technical PASS never makes `adoptionReady` or `productionReady` true. Labels/receipts establish input consistency, not human authority or visual correctness.

## A. Layer import contract — `cas/rig-import/08`

- `characterId: morwen`; `rigSource` and `designSource`: repository-relative `{path, sha256}` references. SHA is checked before loading, using SOURCE-05's contained-path reader. The actual template pins the existing v1.0 spec without changing it. `designSource=null` because the requested four-view sheet has not been supplied/verified in this task.
- `rigSize: [1200,1600]`, `sheetSize: [1536,1024]`: distinct spaces, not interchangeable canvases.
- `joints`: ID -> `{parent: ID|null, side: L|R|null}`. Parent references must exist, graph acyclic, one root. Explicit L/R-suffixed canonical joint IDs must match their side and anatomical parent chain. The actual template uses the v1.0 parent/ID definitions, preserving its source SHA/body reference; world-ground is not introduced as another deform root.
- `layers`: exactly L0/L1/L2/L3 in order, explicit strictly increasing `zOrder`, `adoptionStatus` (`NOT_AVAILABLE`, `UNAPPROVED_CANDIDATE`, `DIRECTOR_APPROVED`). L0=body, L1=base clothing, L2=outfit, L3=outer/accessories. A NOT_AVAILABLE layer is blocked. Status is carried through; importing never changes it. For rear/foreground splitting, supply separately reviewed parts/order in a future contract rather than silently shuffling this four-layer stack.
- Each layer has all `front/back/left/right` view keys. Each view provides `image:{path,sha256}`, declared `size`, `space:rigPx|sheetPx`, `mirrored:false`, measured `anchor:[x,y]|null`, and `joints:{ID:[x,y]|null}` for the same rig ID set. PNG must decode as RGBA with exact size and real transparent pixels. No resizing, color conversion or alpha rewrite occurs.
- All layers of one view must agree on mapped anchor and joint positions, so costume layers cannot silently change the body proportions. This technical consistency is not an independent morphology/design review. Missing coordinates stay null and block.

## B. Anatomy and asymmetry

`attachments.rightGarter` has `side:R`, explicit `jointId`, and `layerId`. Its joint must belong to anatomical R, regardless of facing direction. Actual `jointId/anchor` stay null until the intended attachment is evidenced; no hip/strap pixel is guessed. Layer manifests preserve direction-specific source PNGs. Automatic mirroring is forbidden (`mirrored:true` blocks), as is a reflection matrix. No new garment pixels or anatomy are generated. Design source fingerprint and frame measurement binding preserve provenance; visual costume/proportion approval remains a separate NOT_RUN gate.

## C. Four-view sheet -> rig coordinates

All 2D spaces use top-left origin, +x right, +y down. The 1536×1024 object is a **declared source sheet**, not four automatically inferred quadrants or twelve gait frames.

For a `sheetPx` view, `viewMappings[view]` must specify:

- `crop:[x,y,width,height]` within the sheet (explicit view bounds, not guessed equal panels);
- `matrix:[a,b,c,d,tx,ty]`, mapping **crop-local** pixel coordinates into the rig canvas, finite coefficients and positive determinant (`a*d-b*c>0`); no reflection/singular mapping.

Input sheet anchors/joints are full-sheet points: `q = p - crop.origin`; `rig = [a*q.x+c*q.y+tx, b*q.x+d*q.y+ty]`. Source points must be within the declared crop. A `rigPx` layer is already native rig coordinates and needs no implicit scaling. No 3D projection, identity mapping between different canvases, independent per-view body fitting, or 1536/1200 ratio inference occurs. Missing/invalid mapping returns null mapped coordinates and BLOCKED. Current mappings are all null.

## D. Pose and world-contact contract

SOURCE-05 plan is unchanged on disk. Each of its six slots per facing can additionally reference `poseInput:{path,sha256}`. Pose JSON:

- `schema:cas/rig-pose/08`, exact `frameId`, `direction`, `timeMs`, `space:rigPx`;
- `joints`: explicit posed coordinates for the complete imported rig ID set;
- `actorTransform`: exact same object as the slot's pinned SOURCE-05 measurement. Actual frame PNG must already be 1200×1600, matching SOURCE-05's `imagePx` local coordinates; otherwise BLOCKED. Pose files are not inferred from imported static joints.

Actual `timeMs` must be finite and strictly increasing in each track. Selected measured heel/ball/toe per anatomical foot must equal that posed joint's local coordinate. SOURCE-05 checks side ID, image SHA, phase/stanceId and computes world = translationPx + positive scale × clockwise rotation × localPx. Actor/root values must come from the producer; there is no default identity or fixed-ground substitution. Camera offsets/CSS scaling are not part of worldPx.

Existing converter checks continuous stanceId, and the auditor measures per-foot drift. Each facing is audited separately; plants do not carry across a view boundary. The adapter gates using unrounded per-foot maxima to avoid the known PR225 subprecision issue while leaving its files untouched. Missing stance samples block; actual slipping yields FAIL. Stance/swing and contact selection are authored input, not inferred from image bounds. Synthetic fixture input is marked synthetic in tests, never registered as real assets.

## Current state / substitution

`morwen.import.template.json` is intentionally incomplete: no four-view PNG, no approved L0–L3 split PNG set, no measured sheet crop/matrix/anchors or garter attachment. Supply future immutable PNG references, dimensions, hierarchy/side declarations and measured coordinates at these input fields. No old PNG or prior PR file needs overwriting. Then supply independent frame/pose/measurement files through a new SOURCE-05-compatible plan, and run this adapter. Technical PASS does not grant asset adoption or start real-motion export automatically.
