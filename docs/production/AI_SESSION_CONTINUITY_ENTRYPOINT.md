# TWO AI session continuity — shared entrypoint (candidate)
Updated: 2026-11-18. Branch: feature/morwen-rebuild-01. NOT merged to main.

## Startup contract (ChatGPT / Codex / Claude)
1. Read latest `main/AGENTS.md` and the director-approved `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md` before any production.
2. Verify latest canonical lore and relevant character design references; distinguish formally adopted assets from experiments. If private lore inaccessible, mark only lore-dependent work BLOCKED.
3. Read this entrypoint and `docs/production/MORWEN_BRANCH_AND_BASEMESH_RECOVERY_INDEX_20261118.json`, `docs/production/MORWEN_CC0_BASEMESH_SOURCE_LOCK_20261118.json`, and prior QA reports. The branch inventory is only a name index; file/artifact inspection remains NOT_RUN.
4. Check branch/HEAD, relevant PRs, actual Blender files, rendered previews, Actions artifacts and expiry, source SHA-256, and causal retry history before starting any new method.
5. Report concrete output and G1–G4 separately. CI success is not art QA. Do not create a new head model before evaluating existing VRoid, MPFB, CC0 and prior Morwen sculpt assets.
6. Do not reset failure counts across sessions/agents/branches. No destructive cleanup, canon overwrite, main merge, or publication without approval.

## Current work state
- Primary character: Morwen, complete production-quality character NOT_FINISHED.
- Existing Morwen branch names inventoried: 78. Full branch file/PR/artifact audit: NOT_RUN.
- Procedural head studies Method A and B: independent art QA FAIL. Do not reattempt same ineffective procedural family.
- Prior VRoid Base_Female.vrm, MPFB and CC0 candidate comparisons must be recovered and verified against original files. Do not assume license for VRoid/third-party meshes.
- User supplied human-base-meshes-bundle-v1.4.1.zip in conversation; SHA-256 recorded in source lock. GitHub Actions runner does NOT automatically have access. Avoid redundant network retrieval.
- Current integration branch is an unapproved candidate, not the canonical source.
- G1 canonical compliance: PARTIAL/BLOCKED where original is inaccessible; G2: FAIL for head studies; G3: partial technical tests only; G4: NOT_RUN.

## Continuity data model and update discipline
Maintain one authoritative entrypoint and link to machine-readable records rather than copying long session transcripts. For each candidate asset track: source URI or branch/path/commit, SHA-256, license, current owner, method family, failure count and root cause, exact artifacts (run ID and retention), G1–G4, reuse decision, next concrete deliverable. Preserve previous evidence, update status atomically with actual work, and mark unverified fields NOT_RUN or UNKNOWN.

If a session cannot read this branch, open the GitHub URL explicitly or ask for access; never infer state from memory. The durable workflow becomes available to all agents by default only after a reviewed and authorized merge into main.

## Next real deliverable
Recover and inspect actual prior head and body mesh files and available artifacts, compare editability and visual fitness of VRoid vs MPFB vs official CC0 head. Select one defensible base and produce a reusable Blender production candidate with four-view renders and independent art QA; avoid documentation-only cycles.
