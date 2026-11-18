# Layer 0 anatomical registration — pending authored targets

The four approved PNG bytes and direction mapping PASS. Source import is now possible.
This is not approval of a particular reconstructed body or camera calibration.

- Full source image canvas: 384×1024, upright, pixel aspect 1:1. Scene canvas height 2.0 is dimensionless. No world-space stature has been adopted.
- Directly visible: front/back body outline, chin contour, hand/foot ends, left/right profile contours. Scalp crown is covered by hair; skeletal joint centers and unclothed surface under fabric are inferred. Mark those separately in the next landmark table.
- The supplied illustrations are not a calibrated orthographic scan. View-dependent pose, visible hand arrangement and perspective/stylization may change apparent width. Do not force every pixel to a single 3D cross section.
- RGBA is not a clean binary silhouette: the alpha audit finds maximum 254, no fully opaque pixels, and low-alpha nonzero border pixels. Alpha>0 bounds span full image width and sometimes full height. These bounds are invalid anatomical landmarks.
- Preserve the PNG bytes. Use explicit reviewable subject contour/landmark annotations for measurement rather than silently modifying alpha or treating background residue as body geometry.
- 7.5–8 heads is the director's target. Hair-top to chin is not a measured skull height. Do not claim measured agreement until cranium estimate and ground landmark uncertainty have been reviewed.
- Feet are illustrated with stance/depth; identical canvas alignment does not establish common floor contact. Register foot soles per view and record any adjustment as scene transforms, not image edits.

Required next evidence: landmark/contour coordinates with observation vs inference tags; body source intake review; full-body sculpt/retopology candidate; front/back/profiles/oblique renders; independent full-body art QA before detailed face, hair, costume or rig work.

G1 body source PASS. Body registration NOT_RUN. G2 character NOT_RUN. No final visual acceptance or independent QA claimed.
