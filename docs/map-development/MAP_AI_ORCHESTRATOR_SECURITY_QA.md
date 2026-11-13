# MAP-AI-ORCHESTRATOR-01 Security verification record

## Current mode
**DRY_RUN_ONLY**. The workflow does not reference Anthropic/OpenAI secrets, install agent CLIs, or execute paid API calls. The Python request validator rejects `execute` even if someone supplies it via a modified JSON request.

## Protections
- Workflow permissions: `contents: read`.
- Checkout: `persist-credentials: false`.
- Fixed allowlist of agent/task combinations; no arbitrary command, prompt or path from user input.
- Job timeout: 25 minutes. Artifact retention: 7 days.
- Existing main, canonical assets and game runtime remain unchanged.
- A future paid executor requires a separate reviewed change and explicit authorization; it is not enabled by the presence of repository secrets.

## Free QA matrix
1. Claude + MAP-ASSET-RESEARCH-01 + dry_run => ACCEPT.
2. Codex + MAP-PIPELINE-01 + dry_run => ACCEPT.
3. Claude + Codex-only task => REJECT.
4. Arbitrary task ID => REJECT.
5. Unexpected `command` key => REJECT.
6. Unknown mode => REJECT.
7. Non-object request => REJECT.
8. Claude + execute => REJECT.
9. Codex + execute => REJECT.

## Unverified
- CI run status for this revision must be checked on GitHub Actions.
- Work packet retrieval must be verified via generated artifact, not only a green check.
- This pipeline is not an autonomous agent and cannot create code patches or PRs.
- External code execution risks in GitHub Actions dependencies and branch controls require further review before paid execution is considered.
