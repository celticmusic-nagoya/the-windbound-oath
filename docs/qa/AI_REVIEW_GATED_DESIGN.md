# AI-assisted PR review — gated design (proposal only)

Status: DESIGN_ONLY. No AI API invocation is implemented or enabled.

## Existing free gates
- Common Syntax QA: PR #236 (Draft, independent).
- PR Diff Review Report: PR #237 (Draft), no-cost deterministic report.
- Preserve all existing project-specific QA workflows.

## Future opt-in API review
1. Trigger: `workflow_dispatch` only; no automatic PR, push or cron invocation.
2. Require an explicit `enable_ai_review` input, default false.
3. Pin an approved model and a maximum input/output token budget.
4. Fetch only a bounded diff, never repository secrets or private canon.
5. Strip or reject credentials and personal data before sending any content.
6. Send read-only code-review instructions; output findings as suggestions.
7. Do not write code, alter branches, comment automatically, merge or publish.
8. Keep `permissions: contents: read`; no write token.
9. If no API credential exists, skip with a clear status; do not fail the free QA.
10. Track usage and costs outside the repository; stop on budget exhaustion.

## Security and QA acceptance gates
- [ ] Director approves provider, model and spending ceiling.
- [ ] Confirm provider retention and data handling terms.
- [ ] Verify bounded diff extraction and secret redaction.
- [ ] Test with mocked API response before enabling paid calls.
- [ ] Confirm no change to canonical lore, design assets, or production build.
- [ ] Confirm API errors cannot block existing free QA.

## Canon
At every task, read current `AGENTS.md` and the latest private canon main where accessible.
If canon is unavailable, do not guess or modify canon-dependent content.
Current explicit ages: Aidan, Fiona, Morwen are all 18.

## Current decision
Do not enable API calls or add credentials. Keep this as a non-executable specification.
