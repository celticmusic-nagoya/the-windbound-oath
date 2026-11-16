# Source-review technical QA — LIND-SPATIAL-CODEX-01

Existing implementation was executed, not rebuilt. Baseline d18f7a5 path repair was checked; all 8 topology/mutation tests pass. Local Blender 4.3.2 generated a source-review blend and reopened it in a separate process.

Initial local output lost the packed reference because its image datablock had no users. The failed blend and logs remain. Minimal builder change sets `use_fake_user=True`; corrected reopened blend contains exact approved PNG bytes, 11 hidden/unplaced semantic nodes and 7 named LIND modular collections. Default empty Collection also exists; mesh count remains zero. This is a reference container, not terrain art.

The workflow referenced the existing PR345 pinned checksum manifest but did not include it. The exact existing file was copied (not independently redesigned). New reopened-file verifier hashes packed bytes, checks node identities, seven modular collections and absent geometry. Both Blender workflow invocations now use `--python-exit-code 1`; previously AssertionError could still return exit0. Build/verify logs and JSON are included in Actions artifacts. CI run/retry is owned by coordinator; local evidence here is 4.3.2, while workflow is pinned 4.0.2.

Evidence: execution.json, verification.json, topology-tests.log, build.log, verify.log, plus failed before-fix logs. G1 source-byte subset PASS; full canon/CG/spatial G1 BLOCKED. G2 and G4 NOT_RUN, G3 source-review subset PASS only. No source image, approved asset, game code or metric spatial contract was changed.
