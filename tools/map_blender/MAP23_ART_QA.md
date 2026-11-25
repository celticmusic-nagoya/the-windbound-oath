# MAP23 independent art QA — 2026-11-13
Source run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43333477665
Artifact: 13995184989
Rendered file: map23_original_kit.png, SHA256 73196ce4cbb64a0fe18b60e03ce202d9624b1f515547437079ee674b239979e8
Result: TECH PASS / ART FAIL. Candidate only; no main merge or game integration.

Image observations:
- Cottage: silhouette is a simple box; timber framing largely unreadable from camera; missing windows, roof overhang thickness, chimney and lived-in detailing.
- Roof: basic pitched silhouette, but no shingle/slate courses, gable edge or believable material breakup.
- Wall: repetitive identical-looking bricks in straight columns; lacks staggered irregular fieldstone pattern.
- Coastal rocks: basic icospheres with little weathering or clustering.
- Trees: foliage masses are disconnected from upright pole trunks; no branches, wind-shaped silhouette fails.

Root causes:
1. Tree script places foliage far from trunk without any branch geometry. This is a structural, not texture, issue.
2. Wall uses fixed row alignment and repeated regular block proportions.
3. House script is greybox construction without facade/roof detail modules.
4. Materials and camera lighting flatten most details.

Next MAP23-B candidate should:
- Generate connected tapered trunk/branch skeleton before leaves, with explicit junction overlap QA.
- Use alternating offset irregular stone courses, color variation from a constrained palette.
- Add original window frames, visible beams, roof thickness and shingle strips with deterministic seeds.
- Maintain the same camera for before/after comparisons.
- Stop after two unsuccessful similar art revisions and switch modeling strategy.

QA checklist:
[x] Blender workflow completed successfully
[x] PNG inspected
[x] PNG SHA256 verified
[ ] Art accepted — FAIL
[ ] Android readability/runtime collision — NOT_VERIFIED
