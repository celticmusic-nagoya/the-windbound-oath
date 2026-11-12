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


## Phase 2 — SHA duplicate and temporary-file classification
- Exact blob SHA duplicates: **239 groups** in the current main tree. This counts duplicate groups, not deletable files.
- The duplicates include Morwen `masks/` files repeated in `70/`, `71/`, `72/`, and proposal-specific directories; their relative paths and historical generation scripts may depend on these copies.
- No OS-generated junk matching `.DS_Store`, `Thumbs.db`, `desktop.ini`, `__pycache__`, `.pytest_cache`, `.tmp`, `.bak`, or `.orig` was found in the main tree.
- Five `qa_preview_*.html` files total **7,080,933 bytes**; `71/qa_preview_71.html` is already proposed for deletion in PR #242. The other four total **4,996,359 bytes** and are held for dependency review.
- **DELETE_APPROVED: 0 additional files**. **HOLD** all SHA duplicates, logs, and remaining previews until reference scanning establishes safe removal.
- No source assets, Blender rigs, canon files, QA evidence, or runtime files have been modified.

## Phase 3 — CI execution verified
- GitHub Actions run [43211465775](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43211465775): completed / success.
- Audit job: success; artifact `duplicate-audit-report` (artifact ID 13941486960) uploaded.
- This proves the read-only scan executed, **not** that any candidate is safe to delete. No new deletions approved.
