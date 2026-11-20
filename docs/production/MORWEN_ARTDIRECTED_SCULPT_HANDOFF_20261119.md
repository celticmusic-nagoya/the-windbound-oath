# MORWEN HEAD｜Art-directed sculpt production handoff
Status: PRODUCTION PREPARATION / NOT AN ART ASSET / G2 NOT_RUN FOR NEW METHOD
Owner: character sculpt production; independent art QA: separate reviewer
Branch: `feature/morwen-artdirected-sculpt-20261119`
Baseline: `fcecec10eb33c260f9abdd8b67ec0379002c78c0`; Draft PR #425; Issue #426

## Production source hierarchy
1. Director-approved Layer 0 four-direction sheets and latest approved design decisions.
2. Visually verified equivalent existing images, with provenance and actual SHA-256.
3. The old generated head study is **technical failure evidence only**, not a sculpt base to patch.
Read main AGENTS.md, SESSION_CONTINUITY_INDEX.md and the private handoff canon. No unverified visual references should be called canonical.

## Required actual sculpt
- **Native editable .blend** with independent head/eye/hair/glasses modules, real sculpted facial surface and editable volumetric hair clumps. Not a regenerated ring mesh, disconnected spheres, or curve bevels.
- Face: forehead-to-glabella transition, recessed orbital rim, cheek-to-nasolabial planes, nasal bridge/tip/alar wings, philtrum, upper/lower lip, jaw/chin, ear placement.
- Hair: layered front bangs with V-shaped negative space, roots adhering to scalp, temple locks, staggered nape bob with taper and silhouette control in four orthographic views.
- Eyeglasses: slender oval under-rim aesthetic, pupils and irises visible, measured depth clearance; no Z-fighting.
- Provisional local space: +Z up, -Y forward; record transform/scale. No canonical dimensions assumed.
- Production source should be committed as a **new candidate** only if repository size/licensing rules allow; otherwise store in Actions Artifact with SHA and immutable source locator, never claim Git-tracked .blend.

## Visual acceptance evidence
Render `front.png`, `right.png`, `back.png`, `left.png`, `face_closeup.png`, plus three-quarter and wireframe views. Include 1:1 final display-size crops. Record reference overlay and landmark deltas. Independent reviewer must check hair silhouette, facial planes, eye/iris/glasses readability and intersections.

## Gate separation
- G1 BLOCKED until exact source/reference evidence is logged per region; visual equivalence is permitted but not byte identity.
- G2 NOT_RUN until actual new sculpt render exists; previous procedural candidate remains FAIL.
- G3 NOT_RUN for new method; verify Blender reopen, manifold/degenerate/intersection checks, UV/normals, material and glTF roundtrip separately.
- G4 NOT_RUN until integrated WebGL/Android device review.
- Never merge to main, replace original SHA, or declare PASS from CI alone.

## Failure circuit breaker
Current procedural ring face + spherical details and Bezier hair methods failed art QA. Solid section-mesh procedural clumps also failed art QA. Do not resume those method families by parameter tuning. For new sculpt method, record causal hypothesis and maximum two failed attempts for the same root cause.

## Next executable checkpoint
Locate/verify approved reference image bytes; acquire an editable sculpt environment; save first authored head volume and five-angle comparison. If no sculpt-capable environment exists, mark actual sculpt BLOCKED and keep this preparation separate from asset production.
