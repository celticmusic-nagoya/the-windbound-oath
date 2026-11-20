# C11 cross-AI resume / session continuity (UNAPPROVED)

Owner: Draft PR #421, branch `feature/lind-cliff-rock-art-study-20261118`. Do not create a duplicate PR or merge main. This document is a durable pointer, not a claim that C11 geometry or renders exist.

## Entry point for ChatGPT / Codex / Claude
1. Read latest main `AGENTS.md`, `docs/production/SESSION_CONTINUITY_INDEX.md`, and official cliff references. Compare branch HEAD and PR #421 before any write.
2. Inspect latest successful **C11 cliff local patch preflight** run for this branch. Download its `c11-handoff-<SHA>` Artifact and read `c11_handoff.json`. Match `head_commit`, `script_sha256`, and artifact provenance with current branch; stale checkpoints are historical evidence only.
3. Inspect C10 source and Actions artifacts; require exact SHA `0b6b0f3f6e8e270594cdac5fc81008ffe5210b7e98de352d826360dfd6676508` for `hero_fracture_UNAPPROVED.blend` before Blender execution. Missing/mismatched input = BLOCKED; do not substitute a different model.
4. Run `tools/production_qa/lind_blueprint/c11_recess_patch.py` only with Blender 5.3.0, bounded timeout, and the verified source. Capture `c11_patch_report.json`, editable candidate `.blend`, render views, SHA manifest, and failures in an Artifact. Do not assert G2/G3 PASS from static checks.
5. Record next owner, attempted root cause, attempt count (max 2 for the same approach), precise next command, QA G1-G4, output hashes, and stop reason in the next checkpoint. Resume from the latest verified completed stage, not the start.

## Verified as of 2026-11-20
- Preflight run [44675973127](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44675973127) succeeded and uploaded Artifact `14602292459` (30-day retention). This verifies upload, not content restoration by another AI.
- C11 actual Blender geometry, renders, independent visual QA, and game integration: NOT_RUN / NOT_VERIFIED.
- An unrelated C10 run [44675960165](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44675960165) was unintentionally triggered by the handoff script before exclusion was added. Inspect its final state; do not start a duplicate.

## Operational limits
GitHub Actions continues an already running job without ChatGPT/Claude/Codex chat access, but these AI sessions are not automatically restarted or handed credentials by this document. Artifact retention is finite; before expiry, preserve approved durable metadata in the existing PR/branch or repository as appropriate. No new paid AI API, main merge, deletion, publication, or canon adoption is authorized.
