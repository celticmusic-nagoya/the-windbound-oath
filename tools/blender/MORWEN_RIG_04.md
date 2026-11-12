# MORWEN-RIG-04 — reference registration gate

Status: CANDIDATE_ONLY. Uploaded clothed references are **not** automatically canonical.

## Required inputs (private local package, not committed)
- front: 7694.png (JPEG bytes despite .png suffix)
- left: 7693.png (JPEG bytes despite .png suffix)
- right: 7684.png (PNG)
- back: 7776.png (PNG)

Use `python3 tools/blender/audit_morwen_references.py --input-dir /path/to/references --report /tmp/morwen-reference-audit.json`. Requires Pillow.

The audit validates SHA-256, decoded format and dimensions; it does not place images, derive joint coordinates, convert JPEG to transparent PNG, or confirm official adoption. Those require explicit visual review against the authoritative reference. Do not upload the original images to a public repository merely to run CI.

## Alignment plan
- Align all facings to one ground plane and normalized body height.
- Identify per-facing head center, shoulder, elbow, wrist, pelvis, knee and ankle anchors.
- Store measured pivots in a separate reviewed profile. Never guess from silhouette alone.
- Check left-facing accessory exclusions and right-facing asymmetry against approved turnaround.
- Create a rig-only overlay proof before any production sprite render.

## Gates
1. All four SHA/format/dimension checks PASS.
2. Director-approved canonical mapping confirmed.
3. Measured joint pivots reviewed.
4. Blender overlay candidate QA and alpha checks PASS.
5. Only then produce a candidate front-facing frame.
