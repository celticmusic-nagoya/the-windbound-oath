# THE WINDBOUND OATH — Autonomous Game Development Protocol v1.0

Status: Director-adopted workflow standard (2026-11-11)
Scope: Narrative, game systems, UI/UX, direction/polish, implementation, QA, and asset pipeline.
Relationship: Complements existing AGENTS.md, AI token/workflow policy, CHARACTER_ASSET_GENERATION_GUIDE_v1.2.md, and official canon. Where they conflict, protect director-approved canon and repository safety rules; escalate explicit conflicts rather than silently override them.

## 1. Domain standards
### Narrative and world
Modularize scenes, dialogue and flags into structured JSON/YAML where compatible with the actual engine. Use stable IDs, references and schema validation; keep approved character voices, foreshadowing and event ordering. Write concise, emotionally effective dialogue without changing adopted story beats without approval.

### Game systems
Identify and test the core game loop first (MVP). Prefer data-driven configuration for items, encounters, progression and balancing; avoid speculative rewrites or new frameworks where the current implementation already provides equivalent separation. Preserve SAVE compatibility and test migration paths.

### UI/UX
Start with layout grid, information hierarchy, contrast, keyboard/touch navigation and responsive behavior. Minimize input latency and cognitive load. Test mobile, accessibility, reduced-motion and text overflow.

### Direction and polish
Add camera shake, hitstop, transitions and synchronized sound as opt-in, parameterized layers. Respect reduced-motion and audio settings; measure performance and avoid disrupting core gameplay.

## 2. Token-efficient context and work packets
Each work packet specifies: TASK ID, issue/PR, source revision, authoritative spec references, objective, exact paths, dependencies, acceptance criteria, protected files, tests and stop conditions. Prefer references and bounded diffs over repeating the entire context. Implement one function/component or small coherent dependency group at a time. Context reduction lowers but does not eliminate hallucinations; always inspect real repository state.

## 3. Issue/branch/PR workflow
- Inspect AGENTS.md, relevant current source and approved canon first.
- One bounded intent per issue/branch/PR; note coupled dependencies explicitly.
- Preserve official assets and original hashes. Separate assets/content from gameplay logic using existing interfaces and manifests.
- Commit incremental, reviewable changes to a work branch. Open or update a Draft PR with change list, tests and risks.
- For routine code changes, follow the latest Auto-Pilot / Auto-Merge policy in AGENTS.md, including its stop triggers and QA requirements. Task-specific explicit prohibitions on merge, release, website publication, canonical asset promotion or irreversible deletion remain binding; do not bypass protected-asset or canon gates.

## 4. Self-review and bounded retry
1. Run targeted tests and static checks, inspect failures.
2. Perform self-review for regressions, edge cases, null/missing data, ID mismatches, SAVE compatibility, mobile performance, UI overflow, accessibility and asset integrity.
3. Apply minimal patch and rerun tests.
4. Prefer an early review after two focused retries per failure class; follow AGENTS.md's current soft limit of up to three retries. If still failing, record reproducible evidence and mark BLOCKED rather than broad speculative changes.
5. Independent QA is separate from self-QA. Record PASS/FAIL/BLOCKED/NOT_RUN honestly; never claim unexecuted device tests passed.

## 5. Visual base-first
For characters, use locked base-body, anatomical anchors, shared master canvas, one-edit-intent, layer-based costume and multi-angle QA per CHARACTER_ASSET_GENERATION_GUIDE_v1.2.md. For UI, fix layout grid, sizing and responsive constraints before decoration. No guarantee of zero rework; use measurable quality gates.

## 6. Acceptance and reporting
Deliver implementation paths, code/diff, tests and results, regressions, unresolved issues, and next recommended task. Preserve director decision points for protected canon and official assets, fundamental architecture choices, and any task-specific approval gates; for routine merges follow the latest AGENTS.md Auto-Merge policy. Otherwise proceed autonomously within the approved bounded task.

## 7. Current priorities
Do not displace approved prologue work or ongoing Morwen FIX-03. For Morwen, base-body/anchor validation remains the prerequisite; HD pixel-art production remains BLOCKED until four-angle independent QA and director adoption.
