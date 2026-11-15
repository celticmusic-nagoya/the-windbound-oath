# MAP-BLENDER-QA-BRIDGE-01 — Non-destructive integration contract

Status: PROPOSED / NOT WIRED / NO RENDER EXECUTED

## Scope
Connect the Aidan's Home Blender rendering job (Draft PR #295) to the map asset intake QA (Draft PR #299) only after the render job's actual workflow path, artifact names, output formats, and canonical source hashes are verified. Do not infer those paths from task titles.

## Artifact boundary
1. Blender runs in its own isolated job and writes **candidate** renders to a new temporary output directory, never the canonical asset directory.
2. Publish an artifact containing candidate PNG files, a manifest, Blender version, render script commit, deterministic seed and renderer settings.
3. An independent QA job downloads only that artifact into a temporary directory, validates its SHA-256 manifest, checks expected PNG count, dimensions, RGBA/alpha and non-empty files, and reports PASS/FAIL.
4. Store the QA JSON, logs, and a contact sheet as separate evidence. No automated approval or overwrite of original PNGs.
5. G1 canonical matching and G2 artistic review remain explicit independent gates; technical PASS is not a production-quality verdict. G4 requires in-game and Android checks.

## Security and cost controls
- No Anthropic/OpenAI secrets, API calls, subscription tokens or AI CLIs.
- GitHub Actions permissions: contents: read; checkout persist-credentials: false.
- Timeout and artifact retention limits; no push, PR merge or deployment from the job.
- Pin third-party actions to reviewed immutable SHAs before promotion.
- Avoid cross-branch artifact trust until source run and commit are verified.

## Preconditions before implementation
- Verify actual Aidan's Home Blender workflow and output path in PR #295.
- Verify accepted asset manifest schema and test results from PR #299.
- Obtain a successful isolated render artifact and its commit SHA.
- Review runtime cost of Blender execution within the repository's GitHub Actions allowance.

## Acceptance
- G3: reproducible technical checks and artifact SHA evidence PASS.
- G1/G2/G4: separately reviewed; never inferred from G3.
- Both original branches remain Draft and main untouched.
