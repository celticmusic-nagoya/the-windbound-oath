# Adopted Lind world PNG — exact-source registration handoff

Status: **BLOCKED_ORIGINAL_BYTES_NOT_EXPOSED**. The 2026-11-16 follow-up contains
a visible image preview, but no readable local attachment path or downloadable
file identifier was supplied to this execution environment. No SHA comparison of
that attachment and no PNG registration have been performed. This is a file
delivery limitation, not an image mismatch or revocation of director adoption.

Expected original SHA-256:
`abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`.
The approved master records 1536×1024 RGB PNG; preview dimensions or appearance
cannot establish byte identity. Do not save a screenshot, re-encode the preview,
generate a substitute, or change the expected hash to force acceptance.

## Registration procedure

Dedicated branch: `feature/lind-source-register-01`, Draft PR #344.
When the original PNG bytes are available, use that branch and run:

```sh
python3 tools/map_blender/lind/register_source.py --source /path/to/original.png --check-only
python3 tools/map_blender/lind/register_source.py --source /path/to/original.png
```

The CLI compares the exact source SHA before creating anything. It writes the
same bytes to `assets/sources/lind-world-20261116/original.png` and creates a
manifest with source SHA, byte count and `processing: NONE`. Existing source
directories/images are refused. Read back and verify the committed blob bytes
before reporting GitHub registration PASS; push only the dedicated feature branch.
Registration does not imply world-scale spatial approval or full G1–G4 PASS.

WORLD, HOME, BUILD and ECO must all use that same immutable committed source
reference once registered. Until then retain G1 source registration BLOCKED.
The illustrated scale bar is decorative, not an approved metric calibration.
No source image is currently present at the planned path.

## Follow-on repair delivered separately

Draft PR #345 isolates historical pixel assembly under `tools/map_blender/legacy/`;
the supported gateway blocks new-world execution until an approved metric
contract exists. Historical reproduction requires `--legacy-layout` and refuses
an existing output. The original implementation remains byte-identical.

Its technical-render workflow pins Ubuntu 24.04's Blender package
`4.0.2+dfsg-1ubuntu8` and Blender runtime `4.0.2`, with SHA checks for both binary
and data packages plus installed version checks. The local Blender 4.3.2 was not
replaced. This pin applies to the isolated technical pipeline; it does not
declare compatibility with unreviewed production models or fix all OS dependency
versions. Independent QA and actual CI render evidence are recorded separately.

SAVE fixture repair executes the real return-scene lexical state and current DEV
function block. Product HTML/JS, SAVE version and accepted artwork are unchanged.
