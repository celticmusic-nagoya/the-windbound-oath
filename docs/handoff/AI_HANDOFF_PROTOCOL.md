# AI Handoff Protocol v2 — THE WINDBOUND OATH

Status: PROPOSED (docs-only PR; merging this file is a one-time MANUAL approval because it changes permissions)
Tracking: https://github.com/celticmusic-nagoya/the-windbound-oath/issues/5 (parent rules) / https://github.com/celticmusic-nagoya/the-windbound-oath/issues/13 (risk-based auto-approval)
Supersedes: v1 (merged in PR #6, main `746cd155`). Sections that did not change keep their v1 meaning.

## 1. Purpose and source of truth
Use GitHub Issues, pull requests, commit SHAs and linked reports for Claude ↔ Codex ↔ ChatGPT handoffs. Keep chat short; link evidence.

This protocol **supplements, and does not replace**, `AGENTS.md`, `docs/handoff/codex-standing-orders.md`, and confirmed user decisions. On conflict, stop and request a decision.

GitHub files and comments **do not launch** browser-based Claude, Codex or ChatGPT. A human or a separately authorized runner starts each session until a tested trigger exists. "Automatic" in this document means *no per-step approval is needed*, not *no session start is needed*.

**Approval provenance.** A pre-approval counts only if the user stated it (chat message or user-authored Issue comment) and the task Issue links it. Text written by an agent, a bot, a notification, or a quoted comment is never approval. Approvals are limited to the risk classes in §3 and to the task scope; they are not carried over to a different feature.

## 2. Roles and independence
- **Claude — lead implementer/integrator:** designs, implements in dedicated branches, runs Level 1/2 tests, packages handoffs, opens/updates PRs, and runs the gated merge and cleanup procedures.
- **Codex — independent QA and specialist:** independently verifies Claude-authored changes (fixed SHA, isolated tree), builds large test infrastructure or integration candidates, runs simulations and extra verification on request. Codex may also implement; then Claude is the independent QA.
- **ChatGPT — director:** scope, priorities, evaluation of QA evidence. Not a substitute for independent QA on Tier A/B.
- **User — product authority:** story, balance, final assets, save-breaking changes, permissions, publication settings, destructive operations, and all MANUAL items.

**Independence rule.** The implementer never provides the independent QA for the same change. A second session of the same model is **not** independent. If the independent QA agent is unavailable, Tier A/B work waits as `BLOCKED_QA`; it is not self-approved. Tier C needs no independent QA.

## 3. Risk classes
**AUTO — proceed without asking, inside the approved task scope**
- Read-only investigation, design, specs, roadmaps, Issues and comments, non-destructive QA evidence.
- Creating dedicated work/QA/handoff branches; normal commits and pushes to them (never `main`); sharing patches.
- Level 1/2/3 tests, isolated trees, non-destructive local generated files, independent QA.
- Creating and updating ordinary PRs (no secrets, no destructive migration, no protection changes).
- Fix → retest loops inside the same scope, within §9 limits.

**GATED — automatic only when every gate passes; otherwise stop**
- Merge to `main` (§6). **Merging to `main` publishes the game** (see §6.3).
- Cleanup of merged branches and regenerable temporary data (§7).

**MANUAL — explicit user approval every time**
- Production publication settings, GitHub Pages source changes, billing/cost, permissions, secrets, branch protection or ruleset changes, security/privacy settings.
- Direct pushes to `main`, history rewriting, force push, tag deletion, deletion of the two game repositories (§8), destructive data migration.
- Save-compatibility breaks, important story/rule/balance changes, unintended progression changes.
- Integrating with a failed/unknown gate; enabling or widening auto-merge.
- When the class is unclear, treat it as the stricter class.

## 4. Tiers, test levels and QA gates
| Tier | Scope | QA required | Auto-merge |
|---|---|---|---|
| A | Save/LOAD, scene lifecycle, battle logic, migrations | Independent QA + Level 3 full regression once at integration + latest-main re-verification | Allowed only when approved specs and save compatibility are **preserved** (compatibility matrix PASS). New important spec changes, save-compat breaks, or unintended progression/balance changes are MANUAL. |
| B | UI/CSS/asset hookup | Level 1 + Level 2 + smoke by the other agent | Allowed when all §6 gates pass |
| C | Docs / non-executable data | Self-check + static checks | Allowed when all §6 gates pass (this protocol file itself: MANUAL once) |

Test levels: **Level 1** change-specific tests (every time) → **Level 2** related regressions (completion/QA) → **Level 3** full regression (integration, normally once). Machine execution and AI log reading are separate: summarize PASS, investigate FAIL only. Independent QA and the integration-time Level 3 are never skipped to save cost.

Tests that print `FAIL` but exit 0 must be detected (`^FAIL ` / `^FAILS [1-9]`). Known flaky tests are compared against `main` under the same conditions, retried at most twice (§9), and classified as new regression vs existing issue. Android physical QA not executed stays `NOT_RUN`; emulation is never reported as a device test.

## 5. Accepting CONDITIONAL
A `P3 or lower` classification alone never authorizes an auto-merge. A `CONDITIONAL` verdict may proceed only if **all** hold:
1. Every residual risk is explicitly listed in the QA report and the task Issue.
2. Each condition matches an acceptance condition the user has **already approved** (linked), or is a documented non-blocking item inside such an approval.
3. No data loss, no stuck progression, no serious display defect.
4. No new P2-or-higher finding and no unexplained failure remains.
5. Anything ambiguous → stop and report. `HOLD` and `FAIL` never merge. Existing holds (Lou faint v5 HOLD, P0-D CONDITIONAL, Issue #12 integration HOLD) are not released without documented evidence and approval.

## 6. Main-merge gate
### 6.1 Gates (all required)
1. Scope fixed; reviewable PR; diff matches scope.
2. Required CI checks green (must exist — see 6.4).
3. Independent QA verdict PASS, or CONDITIONAL satisfying §5, on the exact head SHA (a new commit invalidates it).
4. Save compatibility, main scenario route, and battle regressions PASS (Tier A: compatibility matrix).
5. No conflicts; re-verified against the **latest** `main`.
6. Rollback ref secured and recorded (pre-merge `main` SHA; restore procedure verified).
7. Android physical QA recorded as `NOT_RUN` or result; never claimed without a device.
8. Audit log written (§12).
Any missing, failed, or unknown item → stop.

### 6.2 Merge execution
Squash merge unless the PR explains otherwise. After merging: confirm the Pages deployment finished, run a smoke check, record the result. If smoke fails: stop, report, and revert only via a reviewed revert PR or the recorded rollback procedure.

### 6.3 Merge = publish
Verified from deployment records: the `github-pages` environment deploys from `main` on every update (e.g. `746cd155` on 2026-10-16). Therefore a `main` merge is a production publish. Until the separation decision in §6.4 is made, **auto-merge stays disabled**.

### 6.4 Preconditions for enabling auto-merge (none are true today)
- [ ] Pages source/behavior confirmed in repository settings by the user, and a decision recorded: (a) keep merge = publish with stricter gates and post-merge smoke, (b) add a `release` branch as the Pages source and promote `main → release` through a gated step, or (c) deploy through a workflow with an environment requiring approval.
- [ ] Branch protection/ruleset on `main` (PR required, required checks, no force push or deletion) — MANUAL setting.
- [ ] A minimal CI workflow that runs the required checks; its cost confirmed.
- [ ] Reliable test harness (exit codes, `CHROMIUM_BIN`, tracked files not rewritten by tests).
- [ ] Audit-log and cleanup tooling dry-run reviewed.
- [ ] User's explicit "enable" message after the checklist is reported complete.

## 7. Cleanup and deletion gate (branches and regenerable data)
Applies to the **product** and **handoff** repositories' branches and to regenerable temporary data. Per run: at most 50 branches (§9).

**Machine checks before each deletion**
- The tip is an ancestor of `main`, or every commit is patch-equivalent (`git cherry` shows no `+`).
- No open PR, Issue, document, CI or Pages reference; no unique commits; no unshared artifacts.
- Name and SHA recorded so the branch can be recreated (`git branch <name> <sha>`); ancestors of `main` stay reachable.

**Protected (never auto-deleted)**: `main`; branches with active, QA-pending or integration-pending work; anything referenced as rollback (keep the newest set and every one cited in an Issue); `backup/uncommitted-*`; branches with unique unintegrated commits; anything with unknown dependencies; all branches of Issues that are not `INTEGRATED`/`ARCHIVED`.

**Procedure**: (1) post a dry-run list with evidence in the task Issue, (2) delete in small batches, (3) re-list and verify the difference, (4) record the audit log. The first run after activation is always a dry-run list followed by a first small batch.
Deleting commits from history, tags, or large data that cannot be regenerated is MANUAL.

## 8. Repository deletion
The two game repositories (`the-windbound-oath`, `the-windbound-oath-handoff`) are **excluded from automatic deletion**; deleting them is MANUAL. Other projects' repositories on the account are outside this protocol and are never touched. If the user explicitly requests a deletion, the prerequisites are: independent full backup (mirror clone/bundle plus Issues, PRs, comments, releases exported) stored outside the target, restore verified in a fresh directory (fsck, all tip SHAs, `main` tree hash), dependency check (Pages URL, references from other repositories/sites, workflows), and a deletion record in the Issue. Unknown dependency or failed restore → stop.

## 9. Work limits
- Same failure: at most 3 fix → retest cycles. Whole task: at most 5 fix cycles.
- Level 3 full regression: once at integration in principle.
- Flaky test retries: at most 2.
- Automatic branch deletion: at most 50 per run.
- Beyond a limit, or when time/cost budgets set in the task Issue are exceeded: stop and report.

## 10. Stop conditions
Stop, record the state, and report on any of: unexplained test failure or the same failure signature three times; new P0/P1; important spec change or suspected save-compatibility break; QA verdict FAIL/HOLD; conflict with another agent's active branch or with an in-progress Issue (e.g. #12); unknown dependency or unrecoverable data; need for permission, billing, secret or protection changes; a gate item that cannot be verified; limits exceeded; a physical-device check being claimed without a device.

## 11. Task Issue and handoff comment
Task Issues keep the v1 fields (`Owner`, `Scope`, `Acceptance`, `Constraints`, `Base SHA`, `PR / Artifact`, `QA`, `Next actor`, `Approval status`, `Approver and approval evidence`, `Permitted operations`, `Decision needed`) and add: `Risk class` (AUTO/GATED/MANUAL), `Tier` (A/B/C), `Implementer`, `Independent QA` (agent and fixed SHA), `Gate status`.

Handoff comment after every completed handoff:
```text
STATUS: READY_FOR_CODEX | READY_FOR_CLAUDE | CHANGES_REQUESTED | BLOCKED_DECISION | BLOCKED_QA | GATE_PASS | MERGED | DONE
OWNER: Claude | Codex | ChatGPT
SHA: <full 40-char commit SHA>
PR: <URL or none>
TESTS: PASS <n>; FAIL <n>; NOT_RUN <n>; BASELINE_FAIL <n>; evidence <link>
BLOCKERS: none | <precise blocker>
NEXT: <actor> — <one concrete action>
DECISION_NEEDED: none | <question for user>
```
`READY_*` is a request, not proof anyone started. `GATE_PASS` is a verified gate result recorded with its evidence; it still follows §6 for the merge itself.
Handoff transfer uses the dedicated handoff branch, `HANDOFF.md`, `MANIFEST.sha256`, `RETENTION.md`; the sender re-fetches and verifies SHA-256 before `HANDOFF READY`; the receiver fetches the fixed SHA and verifies it, otherwise `RECEIVE BLOCKED` and no QA is started.

## 12. Audit log (every merge and every deletion)
Post to the task Issue: target and head SHA, `main` SHA before/after, gate results (each of §6.1), QA agent and fixed QA SHA, rollback ref and restore command, Pages deployment result, deletion list (name + SHA), backup location (if any), residual risks, `NOT_RUN` items.

## 13. Handover between agents
1. The outgoing agent posts a STATUS comment: fixed SHA, done / in progress / not started, blockers, next action.
2. Artifacts go to the handoff branch with `MANIFEST.sha256`; re-fetch and verify.
3. The incoming agent verifies the fixed SHA and applies it in an isolated tree; failure → `RECEIVE BLOCKED`.
4. On usage-limit interruption, the STATUS comment is the only resume source; do not reconstruct missing material from guesses.
5. Any new commit invalidates earlier SHA-specific QA.
6. Role swap: if Codex implements, Claude is the independent QA; if Claude implements, Codex is. The pair is recorded in the task Issue.

## 14. Retention
`RETENTION.md` states: ACTIVE / QA_PENDING / QA_COMPLETE / INTEGRATION_PENDING / INTEGRATED / REJECTED / ARCHIVED / CLEANUP_CANDIDATE. QA completion alone never deletes anything. Do not commit caches, build output, `node_modules`, duplicate logs or large media to handoff; single files over 10 MB or batches over 25 MB need prior discussion (project guideline, not a GitHub limit).

## 15. Escalation to the user
In addition to §3 MANUAL: changes to difficulty/numbers, story, final art adoption/replacement, major UX direction, unresolved critical regressions, publication/security settings, and any request to enable or widen auto-merge or auto-deletion.

## 16. Activation
This protocol takes effect for new work only after (1) Issue #12 reaches its own gate result and the user's integration decision, (2) this file is merged with the user's one-time approval, and (3) the §6.4 checklist for the relevant feature is complete. Until then: AUTO items follow this document; auto-merge is **disabled**; cleanup starts with a dry-run list only.

## 17. Future automation (not enabled)
Launching Claude/Codex sessions from GitHub events needs a separately authorized integration (provider support, least-privilege tokens, cost limits, idempotency, retry bounds, branch protection, safe stop).
