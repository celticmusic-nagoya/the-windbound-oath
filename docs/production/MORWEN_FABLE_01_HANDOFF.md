# MORWEN-FABLE-01 — executable handoff for Claude Code (Fable)
Status: READY_FOR_MANUAL_DISPATCH / NOT_EXECUTED
Repository: celticmusic-nagoya/the-windbound-oath
Base branch: feature/char-interface-01 (Draft PR #333)
Scope: **read-only assessment**. Do not edit canonical art, candidate .blend, main, or production assets. No Tripo purchases, external uploads, hosted inference or generated models.

## Instructions for Claude Code (Fable)
1. Read `AGENTS.md`, `docs/production/MORWEN_FABLE_3D_EVALUATION_V0.md`, `docs/production/CHARACTER_INTERFACE_CONTRACT_V0.md`, and `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md`. Honor stricter canonical source rules.
2. Confirm the model selected in Claude Code is actually the user-available Fable model. Record model identifier/version and execution timestamp; do not infer it from this handoff.
3. Fetch candidate .blend from frozen branch `feature/morwen-eyelid-08-contact-cage` at `assets/candidates/morwen-eyelid-08-contact/inspection/CONTACT_CAGE_DISABLED_08.blend`; verify SHA256 `9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4`. Do not modify the original.
4. Use existing inventory, bone, surface, boundary-region and proximity diagnostics in `tools/character_blender/` to understand geometry. Distinguish bone head-tail offset, nearest boundary-vertex distance, actual mesh contact and visible seam.
5. Prepare **candidate-only** evaluation of: 7.5–8-head target, face and hair silhouette, torso proportions, neck and costume join, deformation risk, UV/material integrity and four-view render requirements. Do not guess missing anatomical landmarks.
6. Produce a deterministic Blender Python inspection/render script (not low-quality box geometry). Work only in a separate `feature/morwen-fable-eval-01` branch, Draft PR, or a local isolated workspace. Use identical render camera/lighting settings when comparing A/B.
7. Do not run paid model generation, submit approved/private reference images to outside providers, or change approved original assets. For optional TRELLIS.2/Hunyuan3D, only assess GPU availability and terms from official documentation. No upload without consent.
8. Save `docs/production/MORWEN_FABLE_EVAL_REPORT.json` with status `NOT_RUN` for unexecuted tests and clear G1/G2/G3/G4. Include commands, Blender/model versions, SHA hashes, elapsed time, render paths and evidence for any PASS. Report G1 BLOCKED until canonical source bytes and handedness conflict resolved.
9. Stop same-root retries after two meaningful failures. Never merge to main or publish.

## Objective success criteria
- Evidence-backed comparison of current candidate and Fable-assisted variant without modifying original; reference-image fidelity independently judged.
- Technical mesh/rig/UV/material QA and front/back/left/right renders, at target display size; G4 Android performance only if actually tested.
- Quality-first: no primitive-only model can be accepted as final character.
- No automated adoption. Report recommended next step and explicit blockers.

## Optional free 3D generation — eligibility gate
- TRELLIS.2 and Hunyuan3D 2.1 remain research-only alternatives until official license, inference host privacy, no-cost GPU quota and upload permissions are verified.
- fal plugin may offer 3D generation but model pricing and output license must be confirmed before any job. Connected plugin does not imply free inference.
