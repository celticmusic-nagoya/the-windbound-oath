# MORWEN canonical registration v2 — 2026-11-10

- Official pixel left: `originals/pixel/left.png` supplied in latest nine-file attachment. Older left variants are SUPERSEDED / EXCLUDE_FROM_PRODUCTION.
- All nine original assets are byte-preserved; see MANIFEST.json for SHA-256.
- `display/pixel/` has four 1200x1600 transparent RGBA display derivatives, aligned to ground anchor (600,1540). Preserve originals.
- Pixel derivative normalization uses nearest-neighbor scaling only if needed. This is for visual alignment, not the final in-game 69px sprite.
- Audit existing GitHub binaries by SHA-256 before uploading. Add only absent files. Update references on draft branches only, keep main/production untouched until QA.
- Verify front/left/right/back visual consistency, alpha, foot anchor, accessory preservation, and actual game scale before publishing.
- Do not use old left, do not replace canonical real images, and do not mix with old chibi walk animations.
- GitHub upload, PR, integration and Android QA: NOT_RUN in this package.
