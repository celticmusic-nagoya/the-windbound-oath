# MORWEN-BLENDER-23 | Canonical four-view art review and anatomy fitting contract

## Source
BLENDER-22 four-view SVG overlays, GitHub Actions artifact 13991106128, independently rendered and visually inspected on 2026-11-13. Original reference PNGs remain SHA-locked and unchanged.

## Visual observations (confirmed)
- Front: shoulder-to-neck transition is softly sloped, not a straight horizontal cap. Upper chest is broader than waist. Waist narrows smoothly; hips widen progressively.
- Left/right: bust protrudes anteriorly; ribcage transitions to an inward waist, then outward gluteal/pelvic curve. Front/back asymmetry is intentional anatomy, not equal-depth ellipses.
- Back: upper back narrows toward waist, pelvis and gluteal region broaden below. Front and back silhouette differ due to body anatomy and costume.
- Hair, straps, arms, hands, garments and stockings contribute to alpha contours and must not be treated as torso skin boundaries.

## BLENDER-23 geometry design gate
1. Build separate **thorax** and **pelvis** control sections and connect through smooth waist loops, with strict monotonic Z and consistent winding.
2. Use independent anterior and posterior cubic curves, and left/right lateral radii; do not force equal front/back depth.
3. Model sloping trapezius/shoulder-neck transition as a continuous surface. Shoulder sockets remain a future attachment task.
4. Preserve canonical body proportions and all official costume/asymmetry. Do not invent missing anatomy measurements from garment-only contours.
5. Produce **front, left, right, back and 3/4** flat unlit silhouette and neutral clay views with fixed camera scale. Compare directly to reference images at corresponding anatomical heights.
6. QA: no non-manifold faces, no inverted winding, no rings out of order, no abrupt radius jumps; compare baseline dimensions; record deviations. Independently inspect all views before art approval.

## Status
**Visual baseline REVIEWED; 3D geometry NOT_BUILT.** No artistic approval, main merge, production registration or publication.
