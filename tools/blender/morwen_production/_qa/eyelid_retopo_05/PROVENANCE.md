# EYELID-05 evidence provenance

- `SHEET_*.png`, `EYELID_05_REPORT.json`, `EYE_TARGETS_05*.{json,png}` and `EYELID_05_EVIDENCE_SUMMARY.json` come from the GitHub Actions artifact:
  - run 43587116653, commit a859c6b, artifact `morwen-eyelid-retopo-05`
  - This is attempt B2, the delivered evidence state; technical result FAIL.
- Local reference run vs this artifact:
  - The report JSON matches section by section.
  - All 5 sheets are pixel-identical (max difference 0).
- `ATTEMPT1_*`, `ATTEMPT2_*`, `ATTEMPT3_B1_*` are failure evidence from local runs of the superseded attempts (A1, A2, B1). Their code is replaced in this commit history; the numbers are recorded in the attempt ledgers.
- The `.blend` exists only in the CI artifact.
- Status: **technical FAIL, art QA NOT_RUN, not adopted.**
