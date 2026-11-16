# MORWEN EYELID-09P — root visibility redesign specification

Status: CANDIDATE DESIGN / NOT APPROVED. This is a structural redesign, not a texture pass.

## Evidence and baseline
- 09N fixes root triangle winding without moving vertices; 09M measured root/next-face normal angle ~14.745 degrees and root triangle quality ~0.33279.
- 09O renders six paired diagnostic views with identical cameras. The cage occludes much of the L00 lash; isolated lash appearance also requires aesthetic refinement.
- 09L's 48px image is a cropped root diagnostic, **not** a full-character 48px test.
- Canonical G1 remains BLOCKED until the official Morwen four-view art and design constraints are independently verified.

## 09P geometry architecture
1. Preserve original 08 model and 09N strip file unchanged; build 09P as a separate .blend candidate.
2. Work first on M09_L_LASH_CANDIDATE_00, preserving the remaining 17 lash strips byte-for-byte at the vertex/face data level.
3. Sample the actual eyelid cage surface and camera-facing silhouette. Record a cage-local surface normal, upper-margin tangent, and outward/forward visibility direction. Do not assume global +Y/-Y is outward.
4. Replace the root triangle/quad transition with a **smooth tapered ribbon** whose tangent is continuous at the attachment and whose visible segment exits the eyelid silhouette. Root attachment remains near the actual upper margin; no floating disconnected root.
5. Use a bounded, documented surface-normal clearance, not arbitrary global translations. Evaluate clearance against the actual cage via BVH and check for interpenetration over the entire ribbon.
6. Retain 09N distal tip as an initial *comparison constraint*, not an absolute requirement: if it prevents a coherent curve, create a separately named 09P-tip-variant and record the exact displacement.
7. Mirror/fit the right eye using right-eye geometry and independent visibility checks, never a blind left/right reflection.
8. Do not use generated textures to conceal a silhouette or topology defect. Hair cards/textures may be evaluated only after mesh and camera QA.

## Acceptance and test matrix
- G1: canonical Morwen facial design/eye proportions and accepted 4-view art cross-check. BLOCKED until source verified.
- G2: independent aesthetic review of root shape, lash silhouette, lid continuity, and both-eye consistency at native size. NOT_RUN.
- G3: no unexpected BVH intersections; manifold ribbon where applicable; consistent winding and normals; preservation of unrelated 17 strips; deterministic geometry and input SHA-256. NOT_RUN.
- G4: full Morwen head and full-character renders at actual 48px game scale, with actual game camera/lighting and Android test. NOT_RUN.
- Render **paired isolated and cage-visible** front, oblique, and side views using identical camera transforms, plus full-face and full-character frames.
- If two independent redesign attempts fail for the same cause, stop and change architecture (e.g. switch to a dedicated lash-card geometry workflow), recording evidence.

## Execution constraints
- Keep all generated candidates under render_output/morwen_eyelid_09/09P or equivalent noncanonical candidate paths.
- Do not modify official assets, overwrite 09N, merge main, or publish.
- CI success is only evidence of execution, not aesthetic approval.
- On success, attach manifests, images, scripts, version/seed, input hashes, and G1-G4 status to the Draft PR.
