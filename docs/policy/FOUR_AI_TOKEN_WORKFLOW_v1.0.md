# FOUR-AI TOKEN & WORKFLOW POLICY v1.0

Status: PROPOSED / development coordination; does not override AGENTS.md or approved canon.
Project: THE WINDBOUND OATH

## Ownership and routing

- ChatGPT: issue triage, requirements, packet authoring, GitHub audits, independent QA criteria, integration planning and release gates.
- Codex: scoped implementation, tests, commits and Draft PRs. Prefer bounded diffs and targeted test runs.
- Claude: specialized asset anatomy/rig architecture, hard debugging, or design-sensitive implementation that Codex cannot efficiently resolve.
- Gemini: independent visual/design comparisons, second-opinion review, and concise findings.
- Director: final art/canon adoption, merge and publication approvals.

Use a single accountable implementer per file and task. Other AIs review without editing the same paths concurrently.

## Small task packet contract

Each request contains only:
1. TASK_ID and one-line objective.
2. Repo/ref/HEAD SHA, exact paths and canonical references.
3. Non-negotiable invariants (SHA, dimensions, asymmetric details, approvals).
4. Allowed edits and explicit forbidden edits.
5. Acceptance tests and stop conditions.
6. Output: changed paths, commit/PR, PASS/FAIL/NOT_RUN with evidence, blockers.

Do not paste the entire project history. Fetch AGENTS.md and only referenced canonical specs as needed. Use one compact status report, no repeated verbose progress narration.

## Budget-aware execution

- Route simple deterministic edits and mechanical QA to ChatGPT/GitHub or scripts where possible.
- Use Codex in bounded batches, with targeted tests first and broader regression once per batch.
- Reserve Claude for ambiguity, high-sensitivity visual structures and failed approaches; hand it concrete artifacts and the smallest reproducible case.
- Use Gemini for independent visual inspection; findings must name specific frame/view and evidence.
- Maximum two similar attempts per issue; after two failures stop and produce root-cause analysis plus an alternative approach.
- Never treat reported tests as independently reproduced. Record tool/model, commit, commands, environment, and result.

## Parallel execution rules

- Separate branch per task; never have two writers to the same file or PR without an explicit handoff.
- Keep canonical files immutable; changes are candidates with manifests and SHA-256 checks.
- Draft PR until acceptance gates are met. No auto-merge, canon promotion, website publication or Android PASS claims.
- Shared task ledger records: task ID, owner, branch, base SHA, paths, dependency, status, tests, blockers and next owner.
- Hand-off on usage limits: save a short checkpoint with exact HEAD and outstanding checks; continue independent work on another non-overlapping task.
- Only a user-authorized agent can operate within its actual access; no claims of controlling other AIs or their quotas.

## Current near-term task routing

- CAS-RIG-v1.0: Codex runs and fixes the read-only rig audit + migration unit tests and adds stance-contact regression tests, without touching official images.
- CAS-VISUAL-v0.9: Gemini independently reviews four-view structure and Layer 0/1 composites, reports concrete evidence.
- CAS-LAYER: Claude only handles difficult rig/asset design issues uncovered by tests or visual review.
- ChatGPT reconciles results, checks SHA and design-protection gates, and prepares a final decision packet for the director.

## Definition of done

A task is done only with committed diff, scoped test evidence, regression comparison, no unexpected canonical SHA changes, and a concise PASS/FAIL/NOT_RUN matrix. Visual adoption and merge require director approval.
