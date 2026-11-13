# MORWEN BASE-MESH-SELECTION-01 (research only)

## Recommendation: MPFB / MakeHuman core CC0 base mesh
- Official license: https://www.makehumancommunity.org/about/license.html
- MPFB license: https://github.com/makehumancommunity/mpfb2/blob/master/LICENSE.md
- MPFB Blender extension: https://extensions.blender.org/add-ons/mpfb/
- MPFB core base mesh and targets: CC0; generated output may be used in commercial games. Source code is GPLv3; do not confuse code license with graphical asset license.
- Third-party community clothing/skins/hair may have different terms; verify each asset before import.
- Blender extension supports human mesh creation, body parameter editing and rigging; Blender 4.2+.
- Candidate only: human realism and topology are not yet evaluated against Morwen's anime face; do not call it approved or use unmodified.

## Alternatives
- MB-Lab anime base: archived upstream; licensing of base/output and current compatibility must be audited separately. Not selected.
- Hand sculpt + retopo from licensed CC0 base: fallback if MPFB head cannot match approved anime style without excessive modification.

## Required next checks (NOT RUN)
1. Install MPFB in an isolated headless Blender GitHub Actions job (pinned version + source SHA).
2. Generate core-only base face mesh, verify mesh density, eye and mouth edge loops, deformation suitability.
3. Sculpt to official front/right/back/left references, compare to supplemental face close-up.
4. Five view renders displayed inline; art QA independent of geometry checks.
5. No official asset overwrite, no main merge, no production approval until G1-G4.

## Explicit status
Research completed. No base mesh downloaded, imported, rendered, or approved in this task.
