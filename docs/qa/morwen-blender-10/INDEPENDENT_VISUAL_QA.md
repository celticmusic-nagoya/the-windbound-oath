# MORWEN-BLENDER-10 — independent visual QA

Evidence: Actions 43227490742, artifact 13948751581, inspected all four 384x1024 renders.

**TECHNICAL_QA: PASS**: four PNGs render, alpha margins valid, 17 bones retained, source guide lines absent.

**ART_QA: FAIL**: frontal/back torso is now proportionate and vertical rather than the excessively wide slab in 08. However torso is a straight rectangular cylinder with hard cut at shoulders and hips; head and neck are separate ellipsoids; thighs have a large visible gap to pelvis; elbows, wrists, knees, ankles and feet have conspicuous disconnected joints. Side views reveal a box-like torso with one visible arm and leg, not a credible anatomical contour. No face, hair, knee-high socks, garments or asymmetrical approved Morwen design yet. This is a structural blockout only.

**ROOT CAUSE**: The 09 core fixes landmark-derived width and height, but only replaces torso/pelvis surfaces. The remaining 14 segments are independent ellipsoids with no connecting surface or joint topology. The existing QA tests ratios and clipping, not manifold continuity or shape quality.

**NEXT APPROACH**: Stop local radius-only adjustments. Introduce a single skinned continuous anatomical body mesh with joined shoulder, hip, neck, arm and leg topology, keeping the 17-bone armature and landmark-derived proportions. Add connectivity / manifold tests and inspect 4 views before attempting costume, hair or textures. Do not change canonical references or merge.
