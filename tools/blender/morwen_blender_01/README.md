# MORWEN-BLENDER-01 — four-view base/rig MVP

Issue #243. Dedicated branch: `feature/morwen-blender-01`. **Candidate only; no adoption, production integration, merge, publishing or legacy deletion.**

## Inputs and status

- PR #239 head `6374a9854e4b1e22fd7b180f656bf8f9b5f8f163`: original importer, anchor validator/template, 17-bone parent contract, rough 48-point estimate. Copied files are unmodified. `SOURCE_RECEIPT.json` records all SHA-256 values.
- PR #242 head `27dee80c34a568ba6657cd6683dd707beabfbed7`: `assets/references/morwen/reference_20261112/`, 12 original PNGs and manifest, all checked against GitHub bytes and manifest SHA. **REFERENCE_ONLY**; no user-mediated reupload or image modification.
- No branch-history merges or cleanup changes from either PR. Current main AGENTS and private canon main/addenda/status checked; lore, age, scenario and runtime unchanged. The Issue #243/director override permits candidate generation now.

## Outputs

`assets/candidates/morwen-blender-01/`:

- `morwen_base_rig_candidate.blend`: four separate aligned armatures, **17 bones and 16 parent links each**, four neutral segmented body blockouts, four exact packed references, cameras, diagnostic curves, and overview lighting.
- `front_overlay.png`, `right_overlay.png`, `back_overlay.png`, `left_overlay.png`: actual Blender renders, native 384×1024.
- `neutral_proxy_4views.png`: new neutral mannequin geometry, left-to-right **front / right / back / left**, 2048×1024. These are basic blockouts, not detailed finished bodies.
- `anchors_candidate.json`, `source_qa.json`, `blender_qa.json`, `reload_qa.json`: calibrated candidates and actual technical QA. Local logs and Actions evidence are in `QA_SUMMARY.md` / `CI_EVIDENCE.json`.

Open the .blend and inspect collections `References_REFERENCE_ONLY`, `Candidate_armatures`, `Neutral_body_blockouts`, `QA_overlays`. Proxies are wireframe in viewport and hidden from overlay renders. References are packed byte-identically, so opening the .blend does not require external PNG paths. The neutral overview is a separate render; the saved active camera is front.

## Calibration, precision and uncertainty

`LANDMARK_CANDIDATES.json` contains manually pixel-refined **visual estimates**, adapted from the upstream `views` rough schema into `facings` with the 12-anchor validator contract plus extra rig points. Front/back pixel offsets were corrected against the exact shifted silhouettes; front anatomical L/R naming was corrected. No `MEASURED_CANDIDATE_UNREVIEWED` claim is made and the old measured-only importer is not misused for these estimates.

- Width/height: 384×1024. Alpha>=128 bbox and ground row are measured. Heights 986/986/985/986 px differ by 1 px. All views share one pixel-to-world scale; per-view translation aligns ground and pelvis without independently resizing views.
- `x_world=(x_pixel-pelvis_x)*common_scale`, `z_world=(ground_y-y_pixel)*common_scale`. X aspect is preserved instead of stretching the 384px width to one character height. Camera projection roundtrip is checked for every bone endpoint, error <0.01 px.
- Side names are anatomical: front L is screen-right; back L is screen-left. Right-facing profile has anatomical R nearer the camera; left-facing has L nearer. Source art is never flipped.
- Visible joint candidates have a declared ±12px **uncertainty estimate**, not demonstrated accuracy. Occluded profile limbs share the observed projection and are explicitly inferred (±30px visual uncertainty); ±48px-equivalent lateral depth is a provisional construction value, not an image measurement or recovered anatomy.
- Orange=R, blue=L, green=central, magenta=occluded/inferred. Hidden guide curves are shifted **3px only in the diagnostic overlay** so coincident chains remain visible; this is not an anchor or rig position change. Red line=measured image ground.

The .blend contains four view-specific **2.5D candidate blockouts**, not one solved multiview 3D character. Ellipsoid sections use rigid segment weights (17 groups; root empty) and a real armature modifier. No face/hair/costume/cloth, smooth production skin, IK, animation, retargeting, final topology or production sprite is claimed. Torso/head depth and hidden joints need independent anatomical review. Source pose asymmetry and camera silhouette remain visible rather than being silently mirrored away.

## Repeatable build

Requires Blender 4.x and Python with Pillow. Cycles CPU keeps local/Actions runs independent of EGL/GPU availability.

```sh
python3 tests/blender/test_morwen_blender_01.py
python3 tools/blender/morwen_blender_01/prepare.py
blender -b -t 1 --python-exit-code 1 --python tools/blender/morwen_blender_01/build.py
blender -b -t 1 --python-exit-code 1 --python tools/blender/morwen_blender_01/verify_blend.py
```

All three tools accept `--output DIR` (after Blender's `--` for Blender scripts). Run prepare first. Input hashes are enforced by prepare **and** the build. Geometry/calibration is repeatable; .blend bytes/renders may differ between Blender versions and save metadata. `verify_blend.py` reloads the saved scene, checks packed original SHA, 17-bone hierarchy, finite/nondegenerate geometry, weights, actual forearm deformation and restoration. These are technical self-QA, not visual approval.

GitHub workflow: `.github/workflows/morwen-blender-01.yml`, real headless build/reload with read-only repository permission and downloadable artifacts. No commits, publication or adoption are performed by Actions.

## Next gate

Independent visual/anatomical review (including Claude review requested by the Issue), hidden-depth refinement and a coherent single 3D base are next. Claude/human approval and Android/device QA have not been performed by this implementation. Future finished Blender visual remains **FUTURE_CANON_PENDING_APPROVAL**.
