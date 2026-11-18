# LIND Blender runner failure RCA — 2026-11-18

Scope: GitHub Actions run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44233677269 job 134564548439 (PR #421). **Read-only investigation. No rerun, no Blender render, no workflow edits.**

## Evidence from actual job log
- Checkout PASS; existing immutable packed source artifact download PASS.
- Step `Install Blender (bounded package step)` ran `timeout --signal=TERM --kill-after=15s 300s sudo -E apt-get install -y --no-install-recommends blender python3-numpy libegl1 libgl1 libopengl0 libgl1-mesa-dri`.
- Runner Ubuntu 24.04.5 LTS, Azure runner image `ubuntu24/20261111.370`.
- Package `libgstreamer-plugins-base1.0-0_1.24.2-1ubuntu0.6_amd64.deb` returned **404 Not Found** from `azure.archive.ubuntu.com`/apt-mirrors; `apt-get` exit **100**.
- Blender render and independent reopen/hash verification were **SKIPPED**. Upload artifact succeeded but was only **418 bytes**: no evidence of a Blender scene or three PNG renders.
- This is an APT stale package index/mirror mismatch, **not** the earlier Blender mirror HTTP 530 and not a mesh defect.

## Minimal targeted correction proposal (not executed)
On existing PR #421 branch only, before `apt-get install`, run a bounded `sudo apt-get update -o Acquire::Retries=2` (timeout, no global fallback loop), then install with existing 300s timeout. Verify exact `blender --version` and run existing actual reopen/render tests. Record package version; Ubuntu repository Blender 4.0.2 is **not** the pinned 4.3.2 used by other Morwen workflows, so cross-team version compatibility remains BLOCKED pending agreed pinning and real .blend reopen. If apt refresh still fails, stop and switch to an independently SHA-verified distribution path, not a blind repeat. Do not use `--fix-missing` to hide dependency failures.

## Status
G1 source acquisition PARTIAL; G2 NOT_RUN; G3 Blender NOT_RUN; G4 NOT_RUN. Production readiness NO-GO. No main merge or new branch/PR.
