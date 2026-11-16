# THE WINDBOUND OATH — Cross-chat autonomous execution contract (2026-11-16)

Status: **Director-approved operating intent; branch-only implementation.** This document is a shared repository handoff, not a claim that ChatGPT runs continuously or that all GitHub events are dispatched automatically.

## On every new development chat
1. Read latest `main` and the active feature branch's `AGENTS.md`, production handoff, relevant workflow, current Draft PR, latest Actions runs, artifacts and failure ledger. Do not trust a previous chat's cached status over GitHub evidence.
2. Identify the affected domain (map, character, UI, gameplay, website). Assign independent branch, Draft PR and QA evidence. Respect cross-team common coordinate, scale, camera and canonical design contracts.
3. Execute approved non-destructive work with available GitHub connector permissions. If direct `workflow_dispatch` is unavailable, use a **documented, scoped push trigger** only after inspecting the workflow's `on.push.branches` and `on.push.paths`. Never create empty/repeated commits solely to poll; check existing runs and commits first.
4. For Morwen CC0 source audit, the branch-only workflow `.github/workflows/morwen-parallel-production-gates.yml` accepts a push whose commit message contains `[audit-basemesh]` **and** whose changed path matches the workflow's push path filter. Its optional job is read-only, stores a 14-day artifact and does not authorize formal adoption. A manual dispatch with `audit_basemesh=true` is an alternative.
5. Inspect the exact run ID, job logs and Artifacts. Distinguish CI SUCCESS from G1 canon, G2 art, G3 technical and G4 game/device quality. Record PASS / FAIL / BLOCKED / NOT_RUN and source commit, SHA, software versions, test configuration.
6. Continue only if a real new artifact or verified evidence warrants it. Two failures in one root-cause/method family require a structural method switch; do not rename attempts to reset counts.
7. Never overwrite canonical files, destructively delete, merge to `main` or publish without explicit director approval. Do not claim external AI delegation, rendering, or QA completed merely because a workflow or prompt was written.

## Execution ownership and continuity
- **GitHub**: persistent code, official references, branches, Draft PRs, state/QA records and Actions artifacts.
- **GitHub Actions**: unattended jobs that have already been enabled by repository permissions, triggers and workflow definitions. Prefer read-only `contents: read`, pinned inputs and independent QA.
- **ChatGPT in any conversation**: retrieves current GitHub state, makes approved changes through connected tools, reads logs/artifacts, interprets results, then continues. No automatic cross-chat session execution or permanent background worker is implied.
- **Scheduled autonomous work**: requires a separate `schedule` event or an explicitly configured scheduled task; ordinary push/manual workflows are not a perpetual agent.
- **Chat-independent starting instruction**: `THE WINDBOUND OATHのGitHub最新状態とAGENTS.mdを読み、既存の失敗履歴を確認してから、承認済みの非破壊的工程を続行。Actions/Artifactsを実際に確認し、G1〜G4を報告。`

## Current implementation boundary
The Morwen push-tag trigger is on `feature/morwen-fable-eval-01` only and does **not** automatically apply to all other development branches. The new CC0 ZIP download has not yet been proven successful by an inspected run. Generalizing to all teams requires independent per-domain workflows and branch trigger checks. This policy does not silently grant permissions or bypass approval gates.

## Shared render → inspect → repair → rerender gate (2026-11-16)
- Implemented reusable stdlib decision controller `tools/qa/production_loop_gate.py` and eight unit tests `tools/qa/test_production_loop_gate.py`; wired tests into Morwen integration Actions. This is **a decision gate**, not yet a fully automated sculpt/render/visual-review worker.
- Inputs: `gates.G1..G4` (PASS/FAIL/BLOCKED/NOT_RUN), `source_verified`, `render_sha256_verified`, `method_family`, `same_cause_attempts`, `repair_plan_approved`, `repair_is_non_destructive`, optional `source_commit`. Command: `python tools/qa/production_loop_gate.py evidence.json decision.json`.
- Decisions: `NEXT_STAGE` only after all G1–G4 PASS; `REPAIR_AND_RENDER` only with approved non-destructive plan and fewer than two cumulative same-cause attempts; `METHOD_SWITCH_REQUIRED` at two failures; `BLOCKED` on missing evidence, canon failure, or unapproved repair. All decisions explicitly deny automatic main merge or formal adoption.
- Art QA must be sourced from actual independent visual review, not merely file existence, green CI, or numerical clipping metrics. Human review or a separately configured and validated vision reviewer is required. Without such reviewer, G2 stays NOT_RUN/BLOCKED, **never silently PASS**.
- Next integration work for each production team: (1) adapter to run real Blender render, (2) image and geometry QA evidence collector, (3) scoped repair recipe registry with bounded attempts, (4) resumable persisted state and artifact hashes, (5) gated transition to next stage, (6) real Actions test and cross-team rollout. Never create a recursive self-triggering Actions loop without a budget, permissions and stop conditions.
- Current status: controller and test files committed; workflow test run result not yet inspected; actual autonomous Blender edit/re-render loop **NOT_IMPLEMENTED**, cross-team rollout **NOT_RUN**.

## Visual progress thumbnails across chats
- Every render-producing team should generate `RENDER_PREVIEW_CONTACT_SHEET.png` and `RENDER_PREVIEW_MANIFEST.json` using `python tools/qa/create_render_contact_sheet.py RENDER_DIR OUTPUT_DIR`. This is wired to Morwen's render lane and stored in its `morwen-qa-render` artifact. No canonical image is modified.
- For each interactive chat progress report, inspect the latest run/artifact, obtain the actual generated PNG, and display the verified preview **in that chat** when an image-accessible tool/path is available; otherwise provide the exact run/artifact link and clearly state that an inline thumbnail could not be attached. Do not fabricate an image or label an old image as the latest result.
- GitHub Actions cannot independently inject an image into an arbitrary ChatGPT conversation. It can publish artifacts and optional repository PR comments. A new chat must fetch current evidence. Automatic unsolicited messages to every chat are **not supported** by this implementation.
- Preview sheet is a convenience visualization, not an independent G2 PASS. Thumbnail crop, transparency, and full-resolution details require separate QA. Current rollout: Morwen only; other teams must add the same script to their workflows.
