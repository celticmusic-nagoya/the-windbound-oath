# Environment reuse qualification for #493 (Claude, #474)

Input for the Environment Reuse Manager (#493, Codex implementation owner). This is qualification evidence and
a technical specification, not a cache implementation. Machine-readable values: `env_reuse_evidence.json`.
`CI_*` values are read back from existing hosted-runner jobs; `LOCAL_*` values come from this sandbox (2 vCPU)
and are not runner measurements. No Actions were dispatched for this record.

## 1. Compatibility of #474 with current main (#468 + #485 merged)
| Check | Result |
| --- | --- |
| `session_plan.py`, `bounded_operation.py` | byte-identical to the #474 pin `5c067e51` |
| #468 API used by #474 (`acquire`, `publish_checkpoint`, `digest_record`, `execute_factory_stage`, `fingerprint`, `run`, `run_operation`) | signatures unchanged |
| VRoid checkpoint bridge contract test (main planner + #427 pin `340c693b`) | PASS |
| Morwen L0 hair G1 oracle tests (code now in private storage, see PR #474) | 5/5 PASS |
| HairHarpy v4 session against main `4143ef02` #468 (local, isolated fencing remote) | COMPLETE in 668 s; 205/205 PASS; measured values identical to CI run 45097145790 (max abs diff 0.0); same target SHA |
| #485 `residual.evaluate` on CI and local v4 observations | 205 PASS on both |

Only provenance fields differ (engine dependency fingerprint, fresh base-hairmesh bytes, fresh head file). The CI pins
in `two-native-env-qualification.yml` stay unchanged; a hosted-runner regression run is not repeated.

## 2. Blender (cache-eligible, conditions below)
* Official archives: 5.3.0 `dacb8264…` 406,944,100 B (build `02f0899d78e3`); 5.2.4 `2fd14c50…` 385,047,680 B (build `cd5dc428cce1`).
* Pristine extracted tree: 5.3.0 1,292,442,515 B, 5,693 files, 85 symlinks, 0 unsafe; manifest `1dabcbf2…` (6,671 entries), identical across
  independent extractions. 5.2.4 1,237,845,968 B, 5,596 files, 79 symlinks, 0 unsafe; manifest `afe69c69…`.
* **The first headless startup writes into the install tree**: +311 `__pycache__` entries (5.3.0) and +479 (5.2.4). A real HairHarpy
  session added further entries. The current installers run a runtime check before returning, so a tree saved after the
  installer is already mutated and runner-dependent.
  - Qualified ways to keep the tree immutable (both verified, manifest unchanged, startup OK): run as a non-root user on a
    read-only tree (hosted runners use the non-root `runner` user), or `--python-use-system-env` with `PYTHONDONTWRITEBYTECODE=1`.
    The second changes Python environment semantics for existing scripts; prefer the read-only tree.
  - Required: snapshot the tree from the SHA-verified archive **before** any execution; make it read-only; verify the manifest
    before first execution and again after the job (detects mutation); never save a tree that was executed.
* CI install cost today: 5.3.0 installer median 24 s (n=13, 20–65 s); home-p0 26 s (n=3); 5.2.4 fetch+verify 27.5 s (n=12, 22–73 s);
  `bpy==5.3.0` wheel 21 s (n=11). LOCAL: download 4.5 s (5.3.0) vs 129.6 s (5.2.4, slow mirror), xz extraction ~21 s,
  zstd-3 tree image 502,435,743 B (larger than the 407 MB official archive), pack 3.3 s, unpack 3.0 s, manifest 1.2 s.
  Expected saving is therefore bounded (extraction ~20 s plus mirror variance) and must be measured in #493 acceptance B;
  do not report estimates as savings. Two variants are worth comparing: (a) extracted read-only tree (fast restore, larger,
  needs the full manifest) and (b) official `.tar.xz` only (407 MB, provenance = official SHA, still pays ~20 s extraction).
* Storage: 5.3.0 + 5.2.4 images ~1 GB of the default 10 GB repository cache; usage beyond 10 GB is billed, so #493 needs a
  hard size budget and must not rely on overage. Entries unused for 7 days are evicted (cold rebuild must stay correct).
* License: GPL; caching the unmodified official build is permissible. Keep official URL + SHA in the manifest.

## 3. HairHarpy v2.0.0 (binary not cache-eligible)
* License §2.1 forbids distributing the Software or any part "except by linking to the author's own repository and releases".
  Public-repository Actions caches can be restored by fork pull requests targeting the base branch, so a cached binary or
  extracted app would be distributable. **Do not cache, upload, release or commit HairHarpy binaries or files.**
* Qualified reuse route (already used by #474): download from the author release each run, verify SUMS + API digest
  (`f8e6f398…`, 47,854,908 B) and tag source identity. Download is small; CI prep (apt + download + SHA + tag clone) was
  32 s in run 45039748645, dominated by apt. Ubuntu `.deb` dependencies are a separate, license-permitted cache candidate
  (only if #493 measures a real gain and apt still verifies them).
* Corrected in this revision: `hairharpy_runtime.sh` no longer copies `LICENSE.md` into the artifact; it records the license
  SHA-256 and the author URL. Artifact 14761141827 (expires 2026-12-22) still contains that copy; deletion is destructive
  and needs explicit approval.
* Output determinism: native output bytes differ across environments while all 205 measurements are identical. Reuse
  acceptance must compare measured values and manifests, not output hashes.

## 4. VRoid Studio (BLOCKED, owner #427/#450)
* VRoid Studio Guidelines (Terms of Use art. 5): distributing VRoid Studio to third parties without pixiv's express permission,
  and reverse engineering/decompiling, are prohibited. Caching the installer or the installed folder in a public-repo cache
  is therefore not eligible without permission; inspecting install folders must not decompile binaries.
* Windows/macOS GUI only; nothing is testable on these Linux runners. Registry, dependency and GUI-startup qualification
  needs the owner's runner and a license decision.
* Observed risk for owner/director review: `morwen-vroid-macos-probe.yml` on `feature/morwen-artdirected-sculpt-20261119`
  caches `vroid.dmg` with `actions/cache` (key `vroid-macos-arm64-2.16.0-d3d8900b6397e9ed7`). Not modified here.

## 5. Requirements handed to #493
1. Exact key as in the #493 design, plus the snapshot-before-execution rule and a run mode (read-only, non-root).
2. Manifest = files (SHA-256 + mode), symlinks (target, no absolute/escaping targets), directories; reject special files.
   Verify before first execution and after the job; the post-job mismatch is a failure, not a resave.
3. Allowlist per tool: Blender official builds only. HairHarpy and VRoid binaries are denied by license.
4. Report actual hit/miss, restore bytes and seconds against the cold install of the same job; read repository cache usage
   in the job (`actions: read`); this session cannot read it (proxy 403).
5. Probe used here: `probe_blender_tree.py` (qualification oracle only; #493 owns the implementation).
