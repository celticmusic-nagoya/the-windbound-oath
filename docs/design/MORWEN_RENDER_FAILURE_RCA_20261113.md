# MORWEN-PRODUCTION-08 Render Failure RCA / Prevention

Date: 2026-11-13. Scope: feature/mvp-blockout-01. No main changes.

## Evidence
- Existing workflow `Morwen Blockout 01 Candidate Export` completed successfully at [run 43364690329](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43364690329). Its Blender install and four-view blockout jobs succeeded. Thus Blender is usable on GitHub-hosted runners.
- New `morwen-layer-diagnostic.yml` exists on the feature branch, but no execution of this new workflow has been independently confirmed. Existing blockout success must not be attributed to it.
- Local Blender installation timed out. This is a **different environment** and not evidence of GitHub Actions Blender failure.
- The diagnostic model is primitive geometry and lacks official reference matching. Even a successful 16-PNG render cannot be called final-quality art.

## Root cause classification
1. **Confirmed:** previous status conflated an old blockout workflow with the new Layer 0–3 pipeline; this is a reporting/verification defect.
2. **Confirmed:** local installation timeouts prevented local execution; avoid local apt installation as primary renderer.
3. **Unverified:** GitHub did not start the new workflow; potential workflow registration, trigger, permission, or workflow YAML issue. Do not assert which without GitHub Actions event/validation logs.
4. **Quality blocker:** diagnostic script does not ingest official reference images or construct production-quality topology. Render execution alone cannot close art QA.

## Corrective controls
- GitHub Actions as primary Blender runtime; local execution optional only.
- Keep `workflow_dispatch` plus branch `push` trigger; ensure `paths` includes workflow and script.
- Use plain printable YAML; PNG signature validation via `bytes.fromhex('89504e470d0a1a0a')`.
- QA gate: require actual workflow run URL, completed/success conclusion, 16 valid PNGs, .blend, and QA.json in Artifact.
- QA gate: visually compare front/right/back/left against director-provided canonical references, including right-leg-only garter.
- Never promote primitive diagnostic model to official art or overwrite originals.
- Limit retries of the same failed method to two; then switch to existing registered workflow or different execution mechanism.

## Next verification
Check [workflow runs](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/workflows/morwen-layer-diagnostic.yml) and the feature branch after commit `5a10e2e`. If still not registered, use the already registered workflow as a controlled entry point, without merging into main. Any such modification needs its own QA and run evidence.

**Status:** ROOT_CAUSE_PARTIAL / PREVENTION_DOCUMENTED / 16_FRAME_RENDER_NOT_VERIFIED.
