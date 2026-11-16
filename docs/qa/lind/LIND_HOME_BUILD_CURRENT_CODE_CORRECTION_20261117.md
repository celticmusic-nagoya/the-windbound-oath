# HOME / BUILD current-state audit correction (2026-11-17)

This is a superseding **source-code inspection**, not a runtime test. Read the actual current `feature/lind-buildings-01:tools/map_blender/lind/buildings/kit_config.py` and `feature/lind-home-01:docs/production/lind/home/arch-kit-contract.v1.json`.

## Corrected finding

The earlier audit in `LIND_HOME_BUILD_ECO_PREINTEGRATION_AUDIT_20261117.md` used the BUILD programme text, which was stale relative to BUILD's `kit_config.py`. The current BUILD code explicitly declares origin at centre of exterior footprint bbox at grade, Z-up, front -Y, and reads the HOME contract JSON via `load_config()`. It includes a version-1 fallback snapshot and a runtime status `HOME_CONTRACT_V1_APPLIED` vs `FALLBACK_SNAPSHOT_OF_HOME_CONTRACT_V1`, with SHA only when a file is loaded. BUILD's roof pitch candidate 44° is within HOME's [38°, 48°] range.

Therefore the earlier statement that **current BUILD code** still uses threshold-centred origin or cannot consume HOME contract is **superseded**. The BUILD programme markdown still describes the older origin/contract state and should be updated by BUILD owner, not edited here.

## Remaining checks, not yet PASS

1. Verify actual Blender producer entrypoint invokes `load_config()` and records returned status/SHA in each build manifest. The fallback must be reported, not silently treated as exact external contract.
2. Validate HOME and BUILD rendered meshes' origin, anchor transforms, door locations, roof materials, and seam geometry in Blender. Documentation/code agreement alone is not a geometric test.
3. Compare BUILD-specific overrides with HOME ranges and source CG; preserve the intentional 44° override as a proposal, not canon.
4. Do not use HOME's provisional metre-scale kit to infer or lock WORLD's unapproved candidate-space metric scale.
5. ECO independent visual QA requires actual image inspection; manifest existence alone is not art PASS.

QA: source-code contract alignment **partial PASS** (origin convention and load path); runtime contract application **NOT_RUN**; model geometry integration **NOT_RUN**; G1 spatial **BLOCKED**, G2 **NOT_RUN**, G4 **NOT_RUN**.

No production source, workflow, model, or original asset modified by this correction.
