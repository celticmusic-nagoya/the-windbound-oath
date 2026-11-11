# MORWEN-MOTION-CONTACT-EXPORT-04 — Codex implementation packet

Status: READY / real-motion contact QA BLOCKED
Repository: celticmusic-nagoya/the-windbound-oath
Baseline: verify current HEAD of feature/character-asset-studio; use separate task branch and Draft PR.
Prior independent execution: PR #225, commit c9d04592f0669e884858779296d72137a74b45a5.
Latest scoped Actions at 12aad80dc5f379031d711a70b69a172414281478: success, run 43030594611.

## Verified sources

- `assets/candidates/morwen-right-walk/72/build_meta.json`: 6 frames with near/far local hip, knee, ankle and authored phases; **historical candidate, not v1.0 rig**.
- `tools/character-asset-studio/pipeline/caslib/articulated.py`: v0.9 3D L/R joints, heel/ball/toe and rotation-axis definitions; no demonstrated animated world-contact export.
- `tools/character-asset-studio/layer0/morwen-master-v1.0/MASTER_BODY_SPEC.v1.0.candidate.json`: world-ground detached, coordinates preserved, adoption NOT_RUN.
- `tools/character-asset-studio/qa/validate_real_motion_export.py`: fail-closed structural validator.
- `tools/character-asset-studio/qa/convert_real_motion_export.py`: validated export -> stance-frame converter.
- `tools/character-asset-studio/qa/audit_stance_contact.py`: drift auditor.

## Objective

Implement the **smallest evidence-backed exporter** in the actual v1.0 animated rig pipeline. Do not graft old near/far sprite ankles onto the v1.0 rig or infer L/R from a screenshot. First locate the actual authored per-frame rig pose and actor/root transform; if missing, implement a narrow opt-in export hook at the point where such transforms are truly calculated. If no such generator exists, report BLOCKED with exact missing inputs and do not manufacture a pose sequence.

## Required output

For each actual generated frame: source path+SHA, rig version, frame ID/time, anatomical L/R mapping, authored stance/swing and stanceId, selected heel/ball/toe contact point, local-to-world actor/root transform, resulting worldPx and units. Preserve coordinate convention and distinguish a fixed ground reference from a planted sole contact.

Use `cas/real-motion-contact-export/1.0` and run validator -> converter -> stance auditor in that order. Add tests for left/right inversion, missing source transform, missing contact points, stance switches and actual drift above tolerance. Existing validator only checks that provenance is nonempty; **provenance authenticity and anatomical mapping require separate evidence checks**.

## Scope and stop conditions

- No edits to official PNGs, archived v0.8/v0.9 manifests or protected canonical references.
- No overwriting PR #225 files or shared feature branch; use independent worktree/branch.
- Max two similar repair attempts, then stop and report structural cause.
- Run targeted tests and record exact command outputs, then compare regression failures by ID.
- Never claim real-motion PASS from synthetic fixtures or an emulator.
- Draft PR only. No merge, adoption or publication.

## Response contract

TASK ID; branch/base/HEAD; changed files; exact commands; PASS/FAIL/NOT_RUN; real world-contact drift per L/R or explicit BLOCKED reason; SHA checks; regression diff; Draft PR URL.
