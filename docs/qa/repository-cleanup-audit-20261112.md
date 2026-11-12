# Repository cleanup audit — 2026-11-12

Status: AUDIT_ONLY / NO_DELETION. Base main: `cab9aa52da653198a712bd986992adc03ea4bfe2`.

## Inventory
- 4,436 tracked blobs (4,829 total tree entries including directories).
- 623 files with `.log` or `.log.gz` extensions in the initial filename-based candidate set.
- 5 `qa_preview_*.html` files (7,080,933 bytes combined); one is already slated for removal in Draft PR #242.
- 31 open pull requests at the time of inspection, including active Blender/rig work and PR #242.

## Disposition
- **KEEP / PROTECT**: adopted images, original references, manifests, SHA locks, Blender source and rig materials, active runtime code, test scripts, official canon, and evidence needed for open PR review.
- **ALREADY IN PROGRESS**: PR #242 proposes removing 12 old Morwen preview/diff files; do not repeat those deletions.
- **REVIEW**: historical QA logs and self-contained preview HTML files. Filename/extension alone is not evidence that deletion is safe.
- **BLOCKED**: other candidate sprites, masks, old animation variants, and unmerged PR assets pending reference/manifest/ownership audit.

## Required deletion gate
1. Rebase onto the latest main and exclude paths already changed in open PRs.
2. Search runtime, scripts, docs, manifests, GitHub workflows, and PR references for every proposed path.
3. Preserve source assets, SHA-locked originals and essential QA evidence; classify each path with reason and original blob SHA.
4. Run tests and check broken links; provide a diff review before merge.
5. Never force-push, merge or publish as part of this audit.

No files are deleted by this audit. The next cleanup PR must contain a concrete verified deletion manifest rather than blanket removal of QA folders.
