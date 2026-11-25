# Production Studio handoff view — QA contract

Scope: `tools/production-studio/handoff-readiness.js` in Draft PR #484. This is a read-only display; it is not a takeover service.

## Static acceptance

- The HTML has exactly one `handoff-cards`, `handoff-status`, `handoff-refresh`, and loads `handoff-readiness.js` once.
- The view fetches PR metadata for #468, #485, #427, #421, #364, #484 with GET only; it does not write GitHub state.
- Unknown STOP_ACK, CAS/lease/fencing, checkpoint bytes/independent restore, all-event Actions, G1–G4 must remain explicitly **未検証**.
- A successful PR fetch, HEAD or recent `updated_at` cannot change **SYNC_UNVERIFIED** to PASS or authorize a backup writer.
- A failed PR request is displayed without erasing other successfully fetched cards. GitHub 403/429 is identified as API limitation or access refusal, not as owner failure.
- A stale refresh response must not overwrite a newer refresh result.
- #468/#485 cards may display the 2026-11-23 PR #468 report as **ISOLATED_PASS** with a direct evidence link. They must keep P0-A **BLOCKED / SYNC_UNVERIFIED**, P0-B–E and G1–G4 **NOT_RUN**, and Release upload **HTTP 401 / 未完了**. The reported tests are not independent Studio QA or production acceptance.
- The report snapshot is dated and source-attributed; newer PR metadata alone must never silently promote or overwrite its QA classification.
- Mobile view supports narrow screens and keyboard focus; no HTML injection from GitHub data (use `textContent`).

## Browser / device acceptance (NOT_RUN)

1. Open the branch's Studio page in a local preview; confirm six cards, status text, links and refresh.
2. Simulate one 404, one 403 and one delayed response; confirm partial failure, API warning and stale-response protection.
3. Test 360px Android viewport and keyboard focus; verify no horizontal overflow.
4. Confirm published gallery, ZIP verification, image selection and GLB/VRM viewer have no regressions.
5. Confirm no private source, lease token, checkpoint bytes, secret or unpublished artifact appears in public output.

## Production integration (NOT_RUN)

Read-only owner/lease/checkpoint evidence may be added only from an authenticated, access-controlled and provenance-verified backend, with an explicit disclosure policy. Never derive takeover eligibility from PR timestamps. No automated reassignment until cross-run restore and fencing are independently proven.

Record actual tested HEAD, browser/device, run IDs, QA outcome and defects in PR #484. CI green alone does not satisfy these acceptance criteria.
