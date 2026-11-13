# MORWEN-3D-TARGET-QUALITY-GATE-01

Status: director-confirmed quality target; production gate, **not** a replacement for design canon.
Task: MORWEN-HEAD-SCULPT-01 / Draft PR #306.

## Two independent mandatory sources

1. **Design authority (G1)**: current canonical Morwen design, latest private lore/addenda/status, and `docs/design/MORWEN_V561_CANONICAL_20261108.md`; preserve the short purple bob, hat, glasses, academy costume, palette, asymmetry, and knee-high socks. Do not promote any target image over an explicitly approved design decision.
2. **Final artistic quality target (G2)**: director-approved 3D target PNG at `assets/companions/morwen/reference/file_00000000301c8209af49625fd11d7670.png` on `feature/morwen-reference-binary-01`. Pinned SHA-256: `7640822cfeb6c3de5b988a79e438babfaf7e3dafbdbc8433ae6cde78f3988957`. This image sets the required *final* standard for sculptural finish, facial anatomy, material depth, controlled lighting, hair volume and visual polish; it is not merely an optional inspiration image.

## G2 acceptance gate

- Compare actual candidate renders against the approved quality target at matched crop, camera angle, head size, and exposure. Label any alignment uncertainty; never score uncalibrated overlays as objective measurements.
- Independently inspect eye shape/placement, cheek-jaw-chin anatomy, nose and mouth form, hair silhouette/strand groups, hat and glasses construction, material response, shadows and finished presentation.
- Judge at final game display size **and** at full render resolution; include front, right, back, left and a close-up.
- Technical PNG output or source SHA PASS does **not** imply G2 PASS. Unfinished or unstyled VRoid geometry, absent signature accessories, and weak material treatment must remain FAIL/NOT_RUN, not approved.
- Before each sculpt attempt, record the defect, method family, target, hypothesis, measurable result, and G1–G4 outcomes in the shared attempt ledger; after two failures with the same technique, switch methods.
- If the stock VRoid base cannot reach the target quality without destructive patch accumulation, switch to constrained retopology, sculpted component construction, or appropriately licensed high-quality source geometry.

## Current status (2026-11-14)

- CI run #43503356166: source SHA verification, Blender candidate render, four 512x512 PNG validations and artifact upload PASS (**G3 partial**).
- First candidate: bounded jaw/cheek adjustment only. No target-calibrated independent art review. **G2 NOT_RUN**, **G4 NOT_RUN**; no formal asset adoption.
- The target image itself must remain unchanged; candidate branch only. No main merge, release or canonical overwrite.
