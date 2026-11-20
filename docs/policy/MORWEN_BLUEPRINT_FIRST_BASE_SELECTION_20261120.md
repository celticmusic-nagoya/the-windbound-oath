# Morwen 3D — director-approved blueprint-first and fair base evaluation (2026-11-20)

**Status: DIRECTOR-APPROVED PRODUCTION METHOD / NOT an asset adoption.** Applies to ChatGPT, Codex, Claude, Gemini and any other AI or automation working on Morwen. Read with current main AGENTS.md, docs/production/SESSION_CONTINUITY_INDEX.md, official Layer 0 four-direction reference, and the private canonical repository. Later formal design approvals take precedence. No canon image or asset is replaced by this policy.

## Mandatory decision and correction
- **Do not reject VRoid Studio, VRM, or VRoid-derived anime-styled base meshes as a class based on previous Morwen candidate failures.** Those G2 failures evaluate the particular outputs and insufficiently planned editing methods, not the inherent suitability of anime-styled bases.
- Anime-styled VRoid bases may provide a substantially closer visual starting point for Morwen than unmodified realistic free/CC0 human bases. Neither source category is automatically accepted or rejected.
- Past failed geometry approaches and their evidence remain preserved. Do not repeat stopped approaches without a documented structural improvement and measurable hypothesis. Distinguish *base choice* from *failed modification method*.
- The production order is **canonical reference audit → precise measured blueprint → matched base comparison → select production method → actual editable sculpt → independent G1–G4 QA**. Do not start speculative irreversible remodeling before establishing the reference and design constraints.

## Blueprint deliverables before base selection
1. Identify the latest approved Layer 0 front/back/left/right images, provenance, original SHA-256 where available, visually equivalent production references (explicitly distinguished from byte-identical originals), and adoption status. Unverifiable parts are BLOCKED; proceed on independently verified parts.
2. Produce registered orthographic front/side/back silhouettes and a three-quarter diagnostic; record camera type, projection, reference scale, provisional origin/axes/units and transformation assumptions. Never present guessed dimensions as measured canonical facts.
3. Establish a landmark table and tolerances for head/cranium, face outline, eyes and sockets, nose, mouth, jaw/chin, ears, hairline/fringe/crown/nape, neck, shoulders and asymmetric costume features. Capture front/side alignment and landmark confidence; mark occluded or ambiguous features.
4. Define editable geometry and pipeline requirements: topology/edge flow around eyes/mouth/joints, hair clump construction, face Shape Keys, weights, UV/PBR, rig, glTF/VRM interchange, LOD/Android/WebGL and render framing. The blueprint is a production specification, not a claim that 2D imagery uniquely determines 3D vertices/faces.
5. Save versioned blueprint and source-hash manifest next to the owning Morwen production PR. Preserve originals and all previous failure artifacts.

## Fair, controlled three-way candidate evaluation
- **A — VRoid/VRM anime-styled base:** lawful provenance and license; preserve strengths in face proportions, anime silhouette, expression rig and hair base while assessing Blender editability.
- **B — new art-directed stylized sculpt:** independent face/head/wardrobe authoring against the same blueprint.
- **C — licensed unmodified realistic CC0 base:** test only as a comparator; do not default to it merely because it is CC0.
- Compare at normalized scale with identical cameras, lighting, clay material, four orthographic views and three-quarter view. Quantify silhouette/landmark deviations and document visual strengths/defects; inspect topology, deformability, Shape Keys, weights, licensing, expected correction effort, reproducibility and final display-size readability.
- Choose only after real editable model and independent art review; if none meets the gate, improve the method, not simply change labels or rerun the same failed repair.

## QA and execution boundaries
- G1 reference/design/license, G2 sculpt and art, G3 geometry/UV/rig/render, G4 in-game/WebGL/Android: record PASS/FAIL/BLOCKED/NOT_RUN independently. A comparison sheet or CI success is not a completed 3D asset.
- Blender 5.3 is permitted for isolated new scenes after previously verified smoke/reference tests; preserve 5.2.4 originals. HairHarpy is optional and requires separate signed/hash/GUI/Vulkan/export validation; neither is a blocker for reference analysis and actual Blender modeling.
- Keep work on existing owning Morwen PR/branch where possible. This policy may be merged independently because the owning PR includes unfinished candidate assets and unrelated tests. No auto-approval of candidate, destructive deletion, source replacement, production release, or merge of unfinished assets.

## Mandatory handoff
Every agent must read this policy from current main **before** selecting a Morwen base or beginning face/hair/body sculpt. Record owning PR, branch/HEAD, official reference and hashes, blueprint version, candidate comparison evidence, prior failed method family, QA state and next executable step. If an old instruction asserts that VRoid is categorically rejected or realistic CC0 is automatically preferred, this later director correction supersedes that assertion **only for Morwen base-selection method**.
