# Morwen archived .blend binary inventory — 2026-11-18

Scope: source archives extracted from original Actions Artifacts, read-only. This is **binary identity QA, not Blender bpy QA**. No new geometry, render, adoption, or main merge.

| PR | Filename | Bytes | SHA-256 |
|---|---|---:|---|
|316|MORWEN_ELM_04_CANDIDATE.blend|8627692|6c5a9919fd6733a0a1ec8d261fb647e5825cb3dfbc4092ed12c0e7baab26de5c|
|318|MORWEN_EYELID_05_CANDIDATE.blend|8640804|db9576531f7da777bc8a67af791af4b39b4975bf8d82adb3082c46742a556ff9|
|399|morwen_head_study_UNAPPROVED.blend|15930885|4e818c24d9d05258bd0c4f5a1cc6116826807a234aa7819f65fc49cc01f307d7|
|399|morwen_head_landmark_review_UNAPPROVED.blend|15488401|d47d140586ba27ca2bc83dabbe3620b39a4d3e91dae57a65874d42defc60836e|
|407|morwen_sculpt02_v02_UNAPPROVED.blend|29066567|90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b|

All five are Zstandard-compressed .blend binary files (magic 28 b5 2f fd). Original ZIPs in persistent ChatGPT Library `/THE_WINDBOUND_OATH/Morwen_Artifact_Recovery_20261118/`. Existing QA documents already mark #399/#407 G2 FAIL and #318 deformation G3 FAIL; this inspection does not alter those verdicts.

**Blocker:** Blender executable and bpy were not available in the local inspection environment. Actual mesh object/vertex/topology, UV, shape keys, armature, file re-open, camera-matched render and G1 silhouette overlay remain NOT_RUN. Do not claim structural compatibility from the binary hashes.

**Next:** use existing GitHub Actions Blender runner (verify runtime acquisition first) to load exact SHA-locked originals and emit machine-readable object/mesh/UV/shape-key/armature inventory and consistent orthographic renders as artifacts; compare to official Layer 0 references. Avoid spawning new branches or rewriting source files.
