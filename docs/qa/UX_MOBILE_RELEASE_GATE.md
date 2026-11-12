# UX-MOBILE-25 — Release candidate gate (draft)

Status: **BLOCKED — no approved production artifact generator or Pages source verified**.

## Separation contract
- Development repository root `index.html` is **not** a release candidate.
- The `?releasePreview=1` option only hides UI. It is **not** a security boundary.
- A production generator must explicitly exclude debug menu, instant-kill handlers, `devJump`, preview flag, and any other debug entry points. Removing DOM controls alone is insufficient.
- Do not rewrite, delete, or publish approved game assets while establishing the build.
- Do not enable GitHub Pages deployment or merge this PR as part of QA.

## Required release procedure
1. Confirm the actual GitHub Pages source (branch/directory or Actions workflow) with repository settings.
2. Define a deterministic, reviewed generator that outputs a complete standalone release directory with relative asset references.
3. Run `python tools/qa/check_release_ui.py RELEASE_DIR/index.html`. A PASS covers **known signatures only**, not all debug routes.
4. Run `python tools/qa/stage_release.py RELEASE_DIR NEW_STAGING_DIR` to stage without overwriting existing output.
5. Independently test story, battle, asset loads, mobile geometry, and Android Chrome against the staged candidate.
6. Obtain explicit director approval before any publication or main merge.

## Current CI scope
`.github/workflows/release-ui-audit.yml` only self-tests the audit and staging guards. It does **not** produce or approve a real release artifact.

## Open blockers
- Actual Pages source / deployment configuration: NOT_VERIFIED
- Approved production generator: NOT_IMPLEMENTED
- Complete debug execution route inventory: NOT_VERIFIED
- Release candidate runtime and Android physical-device QA: NOT_RUN

## UX-MOBILE-26: repository metadata verification
- Repository visibility: PUBLIC (this does not establish GitHub Pages configuration).
- Default branch: `main`.
- GitHub Pages source: still NOT_VERIFIED; repository metadata alone does not expose the configured Pages branch, directory, or Actions deployment.
- **Do not assume** `main` root, `/docs`, or an Actions artifact is the active Pages source.
- No release generation, deployment, or production asset changes are authorized by this audit.

## UX-MOBILE-27: full workflow directory inventory
- Inspected all 23 files under `.github/workflows/` on the working branch.
- No workflow filename or inspected listing indicates a Pages deployment workflow; this does **not** prove GitHub Pages is disabled.
- Direct GitHub Pages settings endpoint was unavailable through the connected GitHub fetch capability.
- Actual Pages source remains `NOT_VERIFIED`. Do not infer source from `main` being the default branch.
- Release generator implementation remains blocked until source and runtime/debug exclusion design are confirmed.
