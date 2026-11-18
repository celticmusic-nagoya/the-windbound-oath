# TWO｜セッションをまたぐ制作引き継ぎの入口

Status: LIVE INDEX / 2026-11-18. This index is navigation and verified status, **not a new canonical lore source**. Always re-fetch current GitHub state; timestamps and PR numbers here can become stale.

## Mandatory startup (ChatGPT / Codex / Claude / other agents)
1. Read current `main:AGENTS.md`, this index and latest director-approved policies. Check the branch, HEAD, open PRs, Actions, artifacts and changed-file contents **before** editing.
2. Read the **private** `celticmusic-nagoya/the-windbound-oath-handoff` repository on `main`: `reference/lore/THE_WINDBOUND_OATH_OFFICIAL_BIBLE_v5.0.md`, `CANON_ADDENDUM.md`, `CANON_STATUS.md`. If inaccessible, mark lore-dependent work `CANON_SOURCE_UNAVAILABLE`. Never duplicate full private lore into the public repo.
3. Read `docs/policy/HIGH_END_3D_CHARACTER_AND_WORLD_PRODUCTION_V1_1.md`, `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md`, `docs/policy/MORWEN_VISUAL_EQUIVALENCE_REFERENCE_20261118.md`, and the **director-approved pending** `docs/policy/PROVISIONAL_LOCAL_3D_PRODUCTION_APPROVAL_20261118.md` in PR #424. Do not mistake unmerged policy text for main content.
4. Inspect `docs/production/PR_TRIAGE_INITIAL_20261118.json` (historical initial inventory) and rerun/read the read-only PR inventory workflow when needed. Never close, delete, or merge branches based only on keyword grouping.
5. Consult each active PR's latest description, files, QA reports and Artifacts; prefer reusing existing valid work to creating duplicate branches or rerunning failed methods.
6. Keep asset-specific handoff next to its owning PR. Update **this index only when the decision, owner, blocker, or canonical pointer changes**; do not rewrite the same status report each turn.

## Current verified state at index creation
- Shared Blender **5.2.4** infrastructure merged in [PR #423](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/423), merge commit `944b9766a3a58cb46073835d0dfc352ea92b6a56`. CI runtime SHA verification, throwaway blend save/reopen and artifact upload PASS. This is NOT G1–G4 asset approval.
- Director explicitly approved **independent new 3D production in provisional asset-local coordinates**; adjust real-world scale later. Approval recorded in [Draft PR #424](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/424). Asset-local work GO; canonical WORLD placement, map assembly, traversal, G4 remain gated.
- Private canonical lore source files were accessible through GitHub connector on 2026-11-18. Re-check access and latest versions every session.
- **Morwen**: approved Layer 0 four-angle images first; visually verified same-design alternatives permitted, actual SHA and provenance preserved. PR #407 sculpt02 G2 FAIL, #417 local topology G2 FAIL, #419 quad-patch G2/G3 FAIL. These are evidence, not final meshes. Next: genuinely new authored sculpt (or separately qualified CC0 base), actual .blend + 4-view/3/4 renders + independent G2/G3.
- **Map / 風待ちの崖**: approved Art-Directed Hybrid World Production. PR #351 WORLD/ROUTE geometry and 3-view images G2 FAIL; PR #353 cross-team spatial contract preparatory, metric scale/anchor NOT APPROVED; PR #421 CC0 rock art study; #415 source candidates; #416 negative controls. Next: independent art-directed cliff/rock modular production with provisional local transforms, real renders and independent QA; don't use candidate geometry as approved final art.
- Other existing branches HOME/BUILD/ECO: inspect before editing; HOME↔BUILD origin conventions partially align in source, runtime geometry verification NOT_RUN.
- PR #423 merged; PR #424 Draft at index creation. Verify live state; do not assume these remain open/closed forever.

## Handoff record required for each substantial production change
Each owning PR should have a short machine-readable or Markdown record of:
- workstream / owner / current branch and exact HEAD / base SHA;
- source of truth, design decisions, original SHA-256, licenses and candidate-vs-approved status;
- actual outputs: editable .blend, renders, exports, artifacts with URLs and SHA, dependencies and Blender version;
- G1/G2/G3/G4 separately PASS/FAIL/BLOCKED/NOT_RUN and independent QA evidence;
- previous attempts, root causes and stopped method families (do not reset across sessions);
- **next single executable task**, prerequisites, stop condition, owner and conflicts;
- whether the changes were committed, PR-open, main-merged or only proposed.

## Continuation safety
- At new session start, read this index **and live sources**, then pick the next unblocked executable task from existing PRs. Do not claim a running agent, completed render or background work without evidence.
- Preserve accepted source hashes, private lore, and current shipped game; no unapproved main merge, deletion, canon rewrite or publication.
- When user says `c` or `ok`, continue only within existing approved non-destructive scope. Explicit approval remains required for main merge and irreversible actions.
- This index cannot itself make a ChatGPT session remember: persistent handoff works only when future agents actually retrieve the repository and inspect its current evidence.
