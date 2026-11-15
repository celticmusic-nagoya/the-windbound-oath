# MAP-PIPELINE-01 — Codex work packet

Status: ASSIGNED / NOT EXECUTED BY CODEX
Owner: Codex (manual/agent handoff; this document does not invoke Codex)
Baseline: current main AGENTS.md; compare active Aidan PR #295 before any pipeline changes.

## Mission
Audit and improve Blender-on-GitHub-Actions production pipeline without changing existing render outputs or official assets.

## Required work
1. Inventory current workflows/scripts, trigger filters, permissions, Blender version, downloads, cache and artifact paths. Identify duplicates and cross-branch side effects.
2. Add an independent, reproducible verification module for source SHA-256, license metadata, source URL, image alpha, texture-map presence, UV validity, object transforms, geometry bounds, material links, consistent scale/anchor and all requested render angles.
3. Generate machine-readable JSON reports and an understandable summary; never report G2 artistic PASS from technical checks.
4. Test a positive fixture and intentional failures (missing texture, wrong hash, bad dimensions, missing render). Record exact commands, test counts and logs.
5. Keep Actions token at least privilege (contents: read); no secret-dependent untrusted PR execution; no AI API cost.
6. Draft PR only. Do not alter game runtime, canonical image files, or merge.

## Exit criteria
G1 source status recorded; G3 deterministic checks pass; G2 manual art review PENDING; G4 Android runtime PENDING. Any unresolved blockers explicitly listed.
