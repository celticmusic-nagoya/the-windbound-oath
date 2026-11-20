## Director-approved continuous 3D production and expansion — 2026-11-21
Mandatory for all AI agents and automations: read [Continuous 3D authoring, recovery and world expansion](../policy/CONTINUOUS_3D_AUTHORING_AND_WORLD_EXPANSION_20261121.md). Batch safe authoring, recover UI context with undo/redo, copy/paste, restore native checkpoints and resume actual work; render, independently QA, correct and continue without routine approval pauses. Apply causal retry v3, preserve originals and avoid duplicate CI. Expand village, cliff, meadows and forest in parallel with reusable assets, density and traversal QA; after Morwen succeeds extend validated methods to diverse canonical character/NPC candidates. No new canon, formal adoption, asset main merge, publication, destruction or added costs without approval.

Preview-first rendering is mandatory: capture actual viewport screenshots (or labeled low-cost headless previews), report and independently QA, correct and re-preview before provisional completion and actual final-quality rendering where supported. Routine reports are not approval gates; preserve native checkpoints and QA evidence.

## Director decision — continuous native character authoring (2026-11-20)
Mandatory for all AI agents and automations: follow the continuous native character authoring policy at the top of [AGENTS.md](../../AGENTS.md). Batch blueprint-driven GUI edits, save meaningful native checkpoints, capture actual visual progress and provisional-complete multi-angle screenshots before VRM export, without routine approval pauses or per-control CI restarts. Existing Morwen PR #427 remains the owner; G1–G4 and all asset adoption gates remain unchanged.

## Director-approved parallel world production v2 — 2026-11-20
Mandatory for all agents and automations: read [Art-Directed Hybrid World Production 2.0](../policy/ART_DIRECTED_HYBRID_WORLD_PRODUCTION_V2.md). Cliff, village and forest proceed independently; preserve cliff E/C12/rock candidates and shift from isolated refinement to scene-level review. Audit existing HOME/BUILD/ECO/ROUTE owners before work, reuse modular assets, build real scenes and test gameplay early in provisional environments. No quality-gate waiver or unfinished asset adoption. Retry v3 remains authoritative; explicit approval required for main changes, deletion and publication. This policy supersedes conflicting cliff-first scheduling only.

# TWO｜セッションをまたぐ制作引き継ぎの入口

Status: LIVE INDEX / 2026-11-18. This index is navigation and verified status, **not a new canonical lore source**. Always re-fetch current GitHub state; timestamps and PR numbers here can become stale.

## Adaptive agent allocation (director approved 2026-11-20)
Read the adaptive cross-agent production policy at the top of [AGENTS.md](../../AGENTS.md). Ownership is task-specific, not model-fixed. For C11 see [PR #421](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/421); Claude preferred for detailed sculpting if available, Codex for technical QA, ChatGPT for independent review. Verify live HEAD and artifact status before work; no external agent has been confirmed running.

## Mandatory startup (ChatGPT / Codex / Claude / other agents)
1. Read current `main:AGENTS.md`, this index and latest director-approved policies. Check the branch, HEAD, open PRs, Actions, artifacts and changed-file contents **before** editing.
2. Read the **private** `celticmusic-nagoya/the-windbound-oath-handoff` repository on `main`: `reference/lore/THE_WINDBOUND_OATH_OFFICIAL_BIBLE_v5.0.md`, `CANON_ADDENDUM.md`, `CANON_STATUS.md`. If inaccessible, mark lore-dependent work `CANON_SOURCE_UNAVAILABLE`. Never duplicate full private lore into the public repo.
3. Read `docs/policy/HIGH_END_3D_CHARACTER_AND_WORLD_PRODUCTION_V1_1.md`, `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V3.md`, `docs/policy/MORWEN_VISUAL_EQUIVALENCE_REFERENCE_20261118.md`, and the **director-approved pending** `docs/policy/PROVISIONAL_LOCAL_3D_PRODUCTION_APPROVAL_20261118.md` in PR #424. Do not mistake unmerged policy text for main content.
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

## Director decision — Morwen blueprint-first base evaluation (2026-11-20)
- Mandatory for all AI agents: [Morwen blueprint-first base selection policy](../policy/MORWEN_BLUEPRINT_FIRST_BASE_SELECTION_20261120.md). Prior VRoid-based candidate G2 failures are **not** a categorical VRoid/VRM rejection; a well-planned anime-styled base may be preferable to an unmodified realistic CC0 base. Audit official Layer 0 references and create measured/assumption-labeled precise 3D blueprint before a matched VRoid/new sculpt/realistic CC0 comparison. No base is adopted yet; actual comparison renders and G1–G4 remain NOT_RUN. Continue assets on existing Morwen owning PRs (#425/#427 as of this decision), not this policy-only branch.

## Director decision — cross-asset high-end technology reassessment (2026-11-20)
- **Mandatory for all AI agents:** [Cross-asset technology re-assessment and production pipeline](../policy/HIGH_END_3D_TECHNOLOGY_REASSESSMENT_AND_PRODUCTION_PIPELINE_20261120.md). Covers VRoid/new sculpt/CC0, HairHarpy, Cascadeur, Mesh2Motion, CG Painter, mPainter, Spirula Studio/photogrammetry, Blender 5.3 and Actions. A previous failed candidate is not a categorical tool rejection; inspect reference/blueprint/environment/method failure separately and validate through real artifacts with G1–G4. Compare production alternatives using common controlled cameras/materials and preserve licensing and hashes. Policy only; no new tool installed, asset approved or Android G4 verified by this merge. Owning asset PRs remain separate (#427 Morwen, #421 cliff; verify live HEAD).

## Mandatory cross-AI binary artifact sharing — director approved 2026-11-20

For all asset and game workstreams, use the owning PR and authenticated GitHub Actions artifact ZIP as the shared binary transport. Record producing commit, run ID, artifact ID, expiration, exact relative paths, SHA256SUMS (and manifest SHA-256), editable source, previews, QA, geometry hash when applicable, and candidate/approved status. Reuse matching outputs; never rerender solely to transfer files.

ChatGPT: use GitHub connector **download_workflow_artifact** to retrieve ZIP into the working environment; extract safely (reject traversal/symlinks, bound size), verify hashes, open actual PNG/JPG bytes. GitHub text fetch is not binary transport (UTF-8 failure). Claude/Codex/Gemini: use authenticated GitHub CLI/API or supported file download; verify each client's access independently. A link or text description is not visual inspection. ACCESS_BLOCKED if unavailable; never mark G2 PASS on that basis. Use fixed-camera previews, clay and comparison sheets as applicable. Record actual retrieval and QA separately.

Check expiration before handoff; preserve needed binaries via existing authorized storage and retention processes, flag at-risk artifacts in owning PR. Never expose signed URLs, tokens or private canon; no new public release, paid storage or unauthorized external transfer. No duplicate CI, no asset adoption or merge implied. Verified ChatGPT transport pilot: [PR #421](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/421#issuecomment-7037011453), run 44713884694, artifact 14617769408; other clients and durable retention remain unverified.


- **2026-11-20 shared performance:** Follow AGENTS.md director-approved 3D production efficiency. Native checkpoint restoration and verified archive caching are in #427 (runtime QA pending); render optimization must be benchmarked before shared implementation adoption. No unfinished asset merge.
