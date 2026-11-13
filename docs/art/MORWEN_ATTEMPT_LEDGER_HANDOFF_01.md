# Morwen attempt ledger handoff (2026-11-14)

## Shared authority
- Shared policy: `docs/design/3D_PRODUCTION_POLICY_LOOP_GUARD.md` on `feature/aidan-home-quality-master-01`, Draft PR #295.
- **Canonical cross-team ledger schema**: `tools/qa_3d_attempt_ledger.py` (`schema_version: 1`) from the same branch.
- Morwen ledger: `tools/blender/morwen_production/_qa/morwen_attempt_ledger.json` with matching schema.
- The earlier `validate_shared_attempt_ledger.py` and `validate_attempt_log.py` are legacy supplementary experiments, **not** the canonical cross-team schema. Do not generate competing new schemas.
- Main branch may not contain these files until authorized merge; do not silently copy or overwrite.

## Evidence-based history
- VRoid candidate: topology audit exists and reports technical geometry, **not** visual approval.
- Four Layer 0 views exist with hashes in previous audit records; full-costume target sheet is documented but binary registration in GitHub is pending.
- Previous visual G2 failed. Exact number and IDs of historic attempts are **unreconciled**. Do not invent attempt entries or reset counts.
- The current ledger has zero **individually verified** attempt records, not zero historical attempts.

## Required next steps
1. Run canonical `python tools/qa_3d_attempt_ledger.py tools/blender/morwen_production/_qa/morwen_attempt_ledger.json` in CI or local Python.
2. Confirm existing run artifacts and commit evidence before adding each historical attempt.
3. For each new attempt, record attempt ID, defect ID, method ID, SHA, hypothesis, evidence, result, root cause and G1-G4. Two failures per defect/method is a hard stop. Keep method aliases mapped to stable IDs in handoffs.
4. Compare canonical orthographic references against actual Blender renders; decide reuse versus reconstruction of face and hair before further tweaking.
5. Do not promote candidate or overwrite canon without G1-G4 and director approval.

## G1–G4
G1 BLOCKED (full target binary registration and canon cross-check pending); G2 FAIL (prior candidate, no approved match); G3 PARTIAL (topology audit only); G4 NOT_RUN.
