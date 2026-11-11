# CLAUDE TASK PACKET — CHARACTER-ASSET-STUDIO-02

Repository: `celticmusic-nagoya/the-windbound-oath`
Base: inspect `AGENTS.md`, `docs/policy/CHARACTER_BASE_BODY_FIRST_WORKFLOW_v1.0.md`, and latest relevant Draft PR before modifying.

## Inputs

`character-asset-studio/` ZIP delivered by ChatGPT; contains v0.1 standalone browser MVP, candidate Morwen demo PNGs, JSON contract, QA guidance.

## Rules / non-negotiable

1. Canonical Morwen front/back/left/right originals are immutable. Verify SHA-256 against existing MANIFEST before/after. Do not replace source artwork, hairstyle, costume, accessories, color or asymmetry.
2. Demo images are **derived candidates**, never adopt as official. No merge to `main`, no deployment, no website publication. Use isolated work branch and Draft PR only.
3. Respect existing file structures; avoid overwrites, deletions and PR conflicts. Check `AGENTS.md` and existing branches first.
4. Two repair attempts maximum per same failure; stop and report structural cause if unresolved.
5. Explicitly distinguish PASS, FAIL, BLOCKED and NOT_RUN; don't claim Android/device QA without executing it.

## Scope for Claude

A. Inspect current repository and select non-conflicting location, e.g. `tools/character-asset-studio/`; integrate v0.1 without overwriting existing files.
B. Run browser-level tests (Playwright if already available; otherwise minimal headless tests) on mobile 390px and desktop 1440px: PNG loading, view switching, frame playback, landmark drag, JSON import/export, transparent composite export, and QA.
C. Harden: remove assumptions of fixed 1200x1600 for future presets; implement normalized world-space anchors and render-scale conversion while preserving 1200x1600 Morwen profile. Fix any discovered bugs before PR.
D. Add data-driven sprite/occlusion constraints for robe left/right hem, rear slit, bag strap, socks/garter; no auto repaint or inferred anatomy.
E. Define a safe `BASE_BODY_SPEC` versioned schema and per-view landmark confidence/source. R2.1 canonical reference unresolved: mark BLOCKED and do not invent coordinates.
F. Deliver Draft PR with SHA, changed files, test report and screenshots. No merge or publication.

## Acceptance criteria

- Four directions and at least 6 frames can be inspected without image corruption.
- PNG alpha and source SHA256 verified, all candidate assets identified as non-canonical.
- Deterministic exported JSON and PNG dimensions; guide/clean composite distinct.
- Preserved canonical assets and zero unexpected file changes.
- Mobile and desktop usability documented, blocked tests identified.

## Known MVP limitations to address

- No real animation rigging; frame viewer only.
- No automatic occlusion or anatomical consistency proof.
- No authenticated R2.1 body master.
- Demo PNGs require a local HTTP server; browser local file access restrictions apply.
