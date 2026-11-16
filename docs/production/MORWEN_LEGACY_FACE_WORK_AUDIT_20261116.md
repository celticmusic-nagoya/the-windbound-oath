# MORWEN — Legacy face / eyelid / eyelash / nose work audit and handoff

Director decision (2026-11-16): **FULLY ADOPT** full-body design-first, sculpt-ready anatomical base, modular sculpt/retopo/rig approach. The prior face work was not entirely wasted: technical observations and failures can be reused, but **no existing geometry is assumed production-ready**.

## Evidence-backed classification (no invented asset PASS)

| Work | Evidence known | Reuse status | Next required evidence |
|---|---|---|---|
| Eye and eyelid candidate geometry | Earlier Morwen eyelid candidate and QA work existed | REFERENCE_ONLY | Locate exact .blend and topology/fit tests on new base |
| Eyelid annulus / zipper | Same approach failed twice in earlier QA | REJECTED_METHOD | No same-family retry; use sculpt-ready anatomical loops or redesigned eyelid topology |
| Eyelashes | Historical iterations reported; no inspected final mesh in this audit | NOT_VERIFIED | Locate file, assess mesh thickness/placement/deformation |
| Nose | Historical iterations reported; no inspected final mesh in this audit | NOT_VERIFIED | Locate file, assess silhouette/face integration |
| CC0 VRoid contact candidate | 6.57-head legacy body, missing official costume/identity | REFERENCE_ONLY | Verify original license, do not promote or treat as final |
| 2026-11-16 head/hair procedural generator | Run 43866841140 produced five PNGs; visible ellipsoid face, tubular hair, overexposure | REJECTED_AS_FINAL; TECHNICAL_EVIDENCE_ONLY | Replace modeling method, not minor parameters |
| Canonical five Morwen reference images | assets/canonical/morwen/2026-11-16/MANIFEST.json | CANONICAL_INPUT | SHA-256 match required for every build |

**No destructive deletion.** The source files, old QA evidence and failure logs must be retained. Reuse only after exact file identity, SHA, license, mesh quality, anatomical compatibility and independent visual QA are verified. Any missing file or provenance = BLOCKED / NOT_VERIFIED, never PASS.

## Required work before new facial detail
1. Enumerate actual historical eye/eyelid/eyelash/nose artifacts, SHA, source commit, QA reports and method-family failure ledger; record precise file paths.
2. Validate 2026-11-16 approved canon source images and director 7.5–8-head adaptation.
3. Lock full-body measurements and choose licensed sculpt-ready human topology. Confirm topology and facial proportions before independent details.
4. Calibrate neutral diagnostic lighting; automated clipped-pixel/alpha/coverage QA, followed by human visual QA.
5. Reassess legacy reusable *techniques* and *data* against new mesh. Do not automatically transfer old mesh or facial landmarks.
6. Build integrated face with eye sockets, anatomically supported eyelids, eyelashes, nose, and hair; capture multi-view and close-up QA.

## QA and no-loop policy
- G1 BLOCKED until actual geometry matches canonical refs; G2 FAIL for procedural head candidate, new base NOT_RUN; G3 render files PASS only; G4 NOT_RUN.
- No annulus/zipper rerun or ellipsoid/tube parameter micro-adjustment. Method change must have structural differences and a measurable hypothesis.
- CI success cannot certify artistic quality. Repeated review requests without new deliverables are not progress.
- Current changes: policy/handoff documentation only; **no new sculpt, no legacy asset deletion, no main merge**.

See `AGENTS.md` and `docs/production/MORWEN_PRODUCTION_METHOD_RESET_20261116.md`.

## Repository search evidence (2026-11-16, main-indexed code search)
- `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md` explicitly records **Morwen eyelid AND mouth polar annulus/zipper two failed trials** (face folding, UV inversion). The next method suggested there is corner-anchored, curve-constrained local quad topology; it is a **proposal, not a verified implementation**.
- The same policy explicitly preserves **nose candidate depth 0.5** and source hashes. This corrects the generic NOT_VERIFIED row above: **nose parameter evidence exists**, but nose mesh, appearance and integration remain NOT_VERIFIED.
- Search results for `eyelid` also include `docs/qa/EYELID_CORRECTION_20E.md` and `tools/assets/eyelid-revision/README.md`, which concern **Fiona/Lou 2D portraits**. They are **not Morwen 3D eyelid evidence** and must not be counted as Morwen work.
- The repository search did not establish the precise location of the legacy Morwen eyelash mesh or a production-ready nose mesh. These remain BLOCKED for physical reuse pending exact source file and SHA.
- Search covers default branch; branch-only artifacts or other historical commits may not be indexed. This inventory is **partial**; do not report full legacy inventory PASS.
