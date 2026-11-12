# MORWEN-RIG-09 — Measured candidate import

## Preconditions
Use the Android marker to measure all 12 points in all four views and export `morwen_anchors_candidate.json`. Do not upload original art to public GitHub. Coordinates are normalized to each full image and must be visually reviewed for cropped margins and foot grounding.

## Execution
`blender -b --python tools/blender/import_morwen_anchors.py -- --anchors /path/to/morwen_anchors_candidate.json --output-dir /tmp/morwen-rig-09`

Outputs: `morwen_measured_candidate.blend` and `qa.json`. Four separate direction-specific skeletons, 12 segments each. No art imported, no character mesh/skin, no animation, no official approval.

## Blocking conditions
- Missing anchor in any facing
- Out-of-bounds normalized coordinate
- Zero-length bone segment
- Invalid candidate status
- Visual canon disagreement, including asymmetric left-side accessories

**Note:** This creates measured visual guides, not a retargetable animation-ready common armature. A mapping from these segments to the common 17-bone rig requires an additional reviewed step.
