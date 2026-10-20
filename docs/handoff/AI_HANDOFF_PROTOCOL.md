# AI Handoff Protocol v1 — THE WINDBOUND OATH

Status: PROPOSED (PR review required)  
Tracking: https://github.com/celticmusic-nagoya/the-windbound-oath/issues/5

## 1. Purpose and source of truth
Use GitHub Issues, pull requests, commit SHAs and linked reports for Claude ↔ Codex ↔ ChatGPT handoffs. Stop copying lengthy reports into chat; use a short summary and direct links.

This protocol **supplements, and does not replace**, `AGENTS.md`, `docs/handoff/codex-standing-orders.md`, and confirmed user decisions. If instructions conflict, stop and request a decision rather than silently overriding existing rules.

GitHub files and comments **do not automatically launch** browser-based Claude, Codex or ChatGPT. A human or a separately authorized runner must initiate the next agent until a tested trigger integration exists.

Canon/lore: the official lore master is private; its index and reference rules are in `docs/lore/README.md` (see also `AGENTS.md` §0). If you cannot read it, do not guess lore: report `LORE_INACCESSIBLE` (what you tried and the error).

Canon adoption and implementation are separate decisions. A canon item being adopted (設定確定) does **not** mean it is implemented or approved for code; implementation needs its own approved task, and the result is checked against the canon (要コード照合).

## 2. Responsibility
- **ChatGPT — director:** clarify scope, track decisions and priorities, review QA evidence and request user decisions. Do not imply background monitoring or automatic execution without a configured mechanism.
- **Claude (Claude Code) — implementer / fixer / integrator:** implement approved work in feature branches, run tests, open/update PRs, address review findings, prepare integration (fixed head SHA, residual-diff check, rollback ref) and merge in-scope PRs under §5-6.
- **Codex — independent reviewer:** inspect exact PR/head SHA, reproduce relevant tests, identify regressions and post a verdict. Review should be independent from implementation evidence. May also implement independently within the user-approved scope (`codex-standing-orders.md` §1) and merge in-scope PRs under §5-6. Work is reviewed by an agent that did not write it. (scope per `codex-standing-orders.md`).
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
- `Approval status`: not requested / pending / scoped-work approved / integration approved (individually, or via the standing pre-approval in §5-6 when its conditions are met) / rejected or withdrawn
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
6. **Merging to `main` is pre-approved (user decision 2026-10-20) for Claude and Codex, per PR, when ALL of these hold:** (a) canon and user-confirmed specs are not changed; (b) the change is within the user-approved development scope; (c) required tests pass (never relaxed) and an independent QA of this exact head SHA, by an agent other than the author, has the verdict PASS (verdict handling below); (d) there is no serious unresolved issue or unexpected regression; (e) immediately before merging, the head SHA equals the QA'd SHA and the diff and conflict state are re-checked, with a rollback ref prepared; (f) after merging, the result and the new main SHA are reported. **Verdict handling:** PASS → may merge if the other conditions hold. CONDITIONAL → never treated as PASS: resolve each condition (or record evidence that it is non-blocking), re-confirm what the condition required (a new independent QA if the head changed), then proceed; a condition that cannot be resolved within scope → consult the user. FAIL → merging is prohibited; fix it and obtain a new independent QA PASS on the new head. BLOCKED → no merge until unblocked; consult the user if the blocker needs a decision. Otherwise stop and consult the user (§7). Never silently merge outside these conditions.
7. Close issue only after integration evidence, regression status and remaining QA gaps are documented.

No agent should assert that another agent has been triggered or completed work without actual evidence.

## 6. Safety and quality gates
- Never force push or rewrite history. The default route to `main` is a scoped branch and PR under §5-6. Direct pushes are allowed only in the exact cases `COLLABORATION.md` §1 (last bullet) and §6 already permit; do not read them more broadly. Every permitted route to `main` (PR merge or such a direct push) carries the same conditions: canon/spec unchanged, an independent QA PASS of the exact head by someone other than the author, a pre-landing check of head, diff and conflicts, a rollback ref, and a post-landing report. PLAYER QA (human playtest) may follow landing on `main`; it never replaces independent QA.
- Preserve battle balance, story, canonical artwork, save compatibility and confirmed UI without explicit authorization.
- P0/P1 unresolved or new severe regression => `BLOCKED_DECISION` / HOLD; do not label READY.
- Keep Lou faint v5 HOLD and P0-D CONDITIONAL unless superseded by documented evidence and approval.
- Tests that print `FAIL` but exit 0 must be detected; do not treat a green process exit as sufficient evidence. Follow existing serial execution guidance.
- Record known baseline failures separately from newly introduced failures.
- Android physical QA not executed => `NOT_RUN`; desktop/emulation cannot be represented as physical verification. Safe non-Android-gated development may continue with rollback.
- Before any authorized integration, capture current main SHA, prepare a verifiable rollback ref, check exact PR diff and tests. No destructive branch deletion/history rewriting.

## 7. Decision escalation
Request user decision for changes to gameplay numbers/difficulty, story, final asset adoption/replacement, save-breaking changes, major UX direction, unresolved critical regression, publication/security settings, auto-merge enablement, or destructive operations. Also stop and consult the user when: canon or game spec must change; QA returns a FAIL or BLOCKED that cannot be fixed or unblocked within scope, or a CONDITIONAL whose condition cannot be resolved (§5-6); an unexpected conflict or regression appears; data loss or save-compatibility is a concern; GitHub Pages settings, repository visibility or migration to a new repository would change. For routine in-scope implementation, review and merge under §5-6, proceed within the existing standing authorization.

## 8. Future automation (not yet enabled)
GitHub Actions can run checks and publish artifacts, but launching Claude/Codex browser sessions requires a separately configured and authorized integration. Before enabling: verify provider support, least-privilege tokens, cost limits, idempotency, retry bounds, branch protection, and safe stop behavior.

## 9. Pilot
Use a separately scoped issue for normal goblin KO dissolve; first verify what exists on `main` versus feature branches, then run implementation → independent review → fix → acceptance. Do not assume assets in a PR are active on main.
