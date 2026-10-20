# AI Handoff Protocol v1 — THE WINDBOUND OATH

Status: PROPOSED (PR review required)  
Tracking: https://github.com/celticmusic-nagoya/the-windbound-oath/issues/5

## 1. Purpose and source of truth
Use GitHub Issues, pull requests, commit SHAs and linked reports for Claude ↔ Codex ↔ ChatGPT handoffs. Stop copying lengthy reports into chat; use a short summary and direct links.

This protocol **supplements, and does not replace**, `AGENTS.md`, `docs/handoff/codex-standing-orders.md`, and confirmed user decisions. If instructions conflict, stop and request a decision rather than silently overriding existing rules.

GitHub files and comments **do not automatically launch** browser-based Claude, Codex or ChatGPT. A human or a separately authorized runner must initiate the next agent until a tested trigger integration exists.

Canon/lore: the official lore master is private; its index and reference rules are in `docs/lore/README.md` (see also `AGENTS.md` §0). If you cannot access it, report "inaccessible" and do not guess lore.

## 2. Responsibility
- **ChatGPT — director:** clarify scope, track decisions and priorities, review QA evidence and request user decisions. Do not imply background monitoring or automatic execution without a configured mechanism.
- **Claude — implementer/integrator:** implement approved work in feature branches, run tests, open/update PRs, address review findings; follow existing main integration restrictions.
- **Codex — independent reviewer:** inspect exact PR/head SHA, reproduce relevant tests, identify regressions and post a verdict. Review should be independent from implementation evidence. May also implement independently when the user has approved it (scope per `codex-standing-orders.md`).
- **User — product authority:** approve creative/spec changes, critical risks, destructive operations, and any changes to merge/deploy permissions.

## 3. One issue per scoped task
Each task issue should include:
- `Owner`: Claude / Codex / ChatGPT / user
- `Scope`: exact goal and affected surfaces
- `Acceptance`: verifiable completion criteria
- `Constraints`: rules and excluded changes
- `Base SHA`: immutable baseline for comparison
- `PR / Artifact`: link(s) to code, tests and reports
- `QA`: PASS / FAIL / NOT_RUN / BASELINE_FAIL, with environment and exact command
- `Next actor`: who acts next and what to do
- `Approval status`: not requested / pending / scoped-work approved / integration approved / rejected or withdrawn
- `Approver and approval evidence`: who approved, exact scope, and an immutable link to the decision (or `none`)
- `Permitted operations`: exact authorized read/write/PR/merge/deploy operations; unspecified operations are not authorized
- `Decision needed`: explicit user choice or `none`

`Decision needed: none` only means no question is pending; it **does not** mean implementation, merge, or deployment was approved. A status label or reviewer recommendation never expands permitted operations. Do not duplicate large documents into comments. Link versioned files and use immutable commit SHA URLs where practical.

## 4. Compact handoff comment
Post this to the task issue or PR after every completed handoff:

```text
STATUS: READY_FOR_CODEX | CHANGES_REQUESTED | READY_FOR_CLAUDE | BLOCKED_DECISION | READY_TO_MERGE | DONE
OWNER: Claude | Codex | ChatGPT
ISSUE: <issue URL or #number>
BRANCH: <branch name>
SHA: <full commit SHA (head)>
PR: <URL or none>
FILES: <changed files / areas>
PURPOSE: <one line: why this change>
TESTS: PASS <count>; FAIL <count>; NOT_RUN <count>; BASELINE_FAIL <count>; evidence <link>
REMAINING: none | <open items>
BLOCKERS: none | <precise blocker>
NEXT: <actor> — <one concrete action>
DECISION_NEEDED: none | <question for user>
```

`READY_FOR_CODEX` is a handoff request, **not proof that Codex has started**. `READY_TO_MERGE` is a review recommendation, **not automatic merge authorization**.

## 5. Suggested workflow
1. Triage issue; check scope, acceptance and base SHA.
2. Claude works on feature branch; tests and commits; opens PR.
3. Claude posts `READY_FOR_CODEX` with PR and SHA.
4. Codex independently reviews that exact SHA; posts `CHANGES_REQUESTED`, `BLOCKED_DECISION` or `READY_TO_MERGE`.
5. Claude addresses findings; any new commit invalidates the prior SHA-specific review; request a fresh review.
6. Existing integration authority decides merge after required checks and rollback preparation. Never silently merge to main.
7. Close issue only after integration evidence, regression status and remaining QA gaps are documented.

No agent should assert that another agent has been triggered or completed work without actual evidence.

## 6. Safety and quality gates
- Never force push or directly modify `main`; use scoped branches and PRs.
- Preserve battle balance, story, canonical artwork, save compatibility and confirmed UI without explicit authorization.
- P0/P1 unresolved or new severe regression => `BLOCKED_DECISION` / HOLD; do not label READY.
- Keep Lou faint v5 HOLD and P0-D CONDITIONAL unless superseded by documented evidence and approval.
- Tests that print `FAIL` but exit 0 must be detected; do not treat a green process exit as sufficient evidence. Follow existing serial execution guidance.
- Record known baseline failures separately from newly introduced failures.
- Android physical QA not executed => `NOT_RUN`; desktop/emulation cannot be represented as physical verification. Safe non-Android-gated development may continue with rollback.
- Before any authorized integration, capture current main SHA, prepare a verifiable rollback ref, check exact PR diff and tests. No destructive branch deletion/history rewriting.

## 7. Decision escalation
Request user decision for changes to gameplay numbers/difficulty, story, final asset adoption/replacement, save-breaking changes, major UX direction, unresolved critical regression, publication/security settings, auto-merge enablement, or destructive operations. For routine in-scope implementation and review, proceed within the existing standing authorization.

## 8. Future automation (not yet enabled)
GitHub Actions can run checks and publish artifacts, but launching Claude/Codex browser sessions requires a separately configured and authorized integration. Before enabling: verify provider support, least-privilege tokens, cost limits, idempotency, retry bounds, branch protection, and safe stop behavior.

## 9. Pilot
Use a separately scoped issue for normal goblin KO dissolve; first verify what exists on `main` versus feature branches, then run implementation → independent review → fix → acceptance. Do not assume assets in a PR are active on main.
