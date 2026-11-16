# MORWEN-09F | Codex / Claude execution-ready instructions

**Status:** INSTRUCTIONS_READY; external delegation NOT_RUN. Candidate only; do not edit official assets. Source: GitHub Actions [43787661277](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43787661277), artifact 14190972043 (20 files, ~9.2 MB), commit 94ca903. Work branch: `feature/morwen-eyelid-09-lash-architecture`, Draft PR #327, stacked on #326. Keep new implementation on a separate branch and Draft PR based on the exact audited parent; do not merge main.

## Actual measured 09E findings

| Candidate | Left cage pairs | Face IDs | Cage triangle IDs | G3 |
|---|---:|---|---|---|
| 09B | 4 | 0, 1 | 938, 940 | FAIL |
| 09D | 5 | 0, 1 | 938, 940 | FAIL |

09B: section 1 vertex on one side has signed nearest winding distance -0.000049197 m; negative edge samples on segment 0/1, plus segment 4 at cage triangle 950. 09D: section 1 negative -0.000055081 m; edge segment 0 side 1 at t=0.75 negative -0.000070989 m, triangle 941. Nearest local winding signs **do not prove inside/outside**; edge sampling is not exhaustive. The root face overlaps cage triangles 938/940 in both candidates. Distinct cage normals: triangle 938 [-0.261305302, 0.079394422, -0.961985528]; triangle 940 [0.827747464, 0.35552004, -0.434096396]. Normal discontinuity and ribbon swept face are the leading hypotheses, not verified root causes.

Model candidate SHA256: `9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4`, path `assets/candidates/morwen-eyelid-08-contact/inspection/CONTACT_CAGE_DISABLED_08.blend`. Official 4-view original binary reference not fully verified => G1 BLOCKED.

## Codex: TASK MORWEN-09F-TOPOLOGY

1. Fetch exact PR #327 HEAD and 09E artifact; verify model SHA. Inspect existing `check_strip_intersections_09.py`, `inspect_root_topology_09e.py`, and source cage winding. Do not change official models or the 09B/09D evidence.
2. Write a **read-only** adjacency and face-crossing report for cage triangles 938, 940, neighboring 941/946/950 and L00 first two faces. Include world-space coordinates, shared vertices/edges, per-triangle normals, face winding consistency, exact overlap pairs and signed-side limitations. Determine whether the cage is watertight; if not, explicitly forbid interpreting winding sign as containment.
3. Only if evidence establishes a viable surface topology, implement a new candidate-only root attachment that follows cage triangle adjacency, with a continuous ribbon whose **triangles** (not just vertices) clear the cage. This is a new structural method, not a scalar offset/normal average retry. Keep 17 other lash strips identical and verify their geometry hashes.
4. GitHub Actions: pin runtime, report NumPy import errors as a separate environment issue, generate candidate .blend + JSON; run BVH triangle intersection on 18 strips and closed/half-open/open eyelid poses where available. Report unavailable poses as NOT_RUN. Save evidence artifact with 7-day retention.
5. Stop after a second meaningful failure of the same root method. Do not claim art PASS from a zero-overlap result. Draft PR only; no merge.

**Exit:** actual Blender execution, L00 collision pair count 0 (otherwise FAIL), all 17 unchanged strips verified, reproducible hashes, no new intersecting eye geometry, and G1/G2/G4 accurately marked BLOCKED/NOT_RUN pending references, renders, and device QA.

## Claude: TASK MORWEN-09F-ART-DIRECTION

1. Review official Morwen design records and verified reference images only; do not invent canonical attributes. Check asymmetry and precise eyelid/eyelash silhouette, especially L00 root.
2. Review 09E measurements and Codex topology proposal. Evaluate plausible natural eyelash flow and attachment to eyelid surface at game display scale. **No aesthetic PASS without actual images**.
3. Once actual front/side/oblique and native-pixel-size PNG renders exist, provide a concise annotated issue list: silhouette, root tangency, thickness, eye readability, material and aliasing. Mark unavailable render or canonical references as NOT_RUN/BLOCKED.
4. Return prioritized corrections with measurable criteria. Avoid simple primitive placeholders and unauthorized design changes.

## Integrator / QA

ChatGPT reviews code, hashes, Blender logs, and independently checks gates. The director decides official adoption. External AI execution is NOT_RUN until an actual delegated session or connector execution is confirmed. No paid APIs, third-party uploads of private/official art, destructive changes, main merges, or publication.

**Current gate:** G1 BLOCKED / G2 NOT_RUN / G3 FAIL / G4 NOT_RUN.
