# Causal Retry & Method-Switch Policy v2 — 2026-11-14

**Status:** Director-approved, repository-wide AI-agent policy. Read the latest `main/AGENTS.md` at every task start and check the branch-specific instructions. This policy applies to Claude, Codex, ChatGPT, Gemini, CI agents, and delegated workers.

## Purpose
Prevent ineffective loops without blocking completion-quality production. A **two-failure limit is a method-family circuit breaker**, not an asset/project-wide attempt ceiling.

## Definitions
- **Defect/root cause:** the observed mismatch and diagnosed mechanism (e.g. UV inversion at an eyelid corner caused by polar annulus/zipper connection).
- **Method family:** materially equivalent algorithm/topology/production approach. A renamed script, prompt wording, parameter, branch, agent or rerun does NOT create a new family.
- **Attempt:** an executed build/render/test intended to resolve the same defect using that family. Failed attempts remain cumulative across sessions and branches.
- **New method:** a structural/causal change demonstrably capable of addressing the root cause (e.g. polar annulus -> corner-anchored curve-constrained quad retopology; automated deformation -> hand sculpt plus local retopology). Different tools alone do not suffice.

## Mandatory execution
1. Inspect actual outputs and baseline; classify defect and record hypothesis, evidence, changed condition, expected outcome and measured delta.
2. Within one method family for the same defect, allow at most **two failed attempts**. At failure 2, **STOP THAT METHOD FAMILY**; do not attempt a third by tuning percentages or renaming it.
3. Immediately perform root-cause analysis and choose a genuinely different method with its own hypothesis, risks and acceptance checks. Continue autonomously if in approved, non-destructive scope. Do not stop the whole task solely because the first family exhausted its limit.
4. No universal cap on distinct methods or total development attempts. Still constrain time/cost to expected final-quality gain; if no credible alternative or evidence, mark BLOCKED and state exactly what is missing.
5. Never weaken G1 canon/source protection, G2 independent art QA, G3 technical QA, G4 game/runtime QA. Record PASS/FAIL/BLOCKED/NOT_RUN independently; a technical PASS is not artistic adoption.
6. Preserve prior ledger entries, IDs, method families, hashes, baseline assets and failed artifacts. Record new method family and **specific causal difference**; never reset the old counter. If the shared ledger schema/validator is incompatible, extend it in a separate tested change rather than erasing history or bypassing the gate.
7. Preserve authorized branch/Draft PR workflow. No direct main writes, main merge, canonical replacement, destructive deletion, or publication without explicit director approval.

## Morwen example
- Eyelid and mouth polar annulus/zipper method: two failed trials, face folding and UV inversion; **STOP polar annulus family**.
- New eyelid method: corner-anchored, curve-constrained local quad topology with independently shaped upper/lower eyelid loops. Separate hypothesis, geometry, QA and ledger entry.
- New mouth method: corner-constrained quad flow and deformable lip loops, independently tested. Do not conflate its failures with eyelid failures.
- Existing nose candidate depth 0.5 and source hashes remain protected. Full v5.61 canonical image comparison is BLOCKED until the actual image binary is verified.

## Reporting contract
For each method switch report: task/asset, defect, root cause, exhausted method and cumulative failed count, new method and causal distinction, baseline/source SHA, tests and renders, G1–G4 statuses, remaining BLOCKED/NOT_RUN, next concrete deliverable.

## Compatibility with historical rules
This document replaces the **retry/stop semantics only** of the earlier general 3-retry soft limit, 3-attempt asset loop rule and strict 3D two-failure hard stop. Older text remains for provenance. Their protections and quality gates remain binding. Existing CI validator prohibition of a third same-family failure is correct and must stay in place. Cross-branch attempt-ledger synchronization is NOT_IMPLEMENTED unless independently verified; handoffs must explicitly carry history.
