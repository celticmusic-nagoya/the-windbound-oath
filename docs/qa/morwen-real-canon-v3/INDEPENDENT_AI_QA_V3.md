# Morwen real-canon v3: independent visual QA

Reviewer: independent (did not make these images). No repository files were modified. Work files are in /tmp/indep_v3/.
Method: per-column lowest pixel with alpha>=128 in x 490-710; alpha-profile reads at single columns; 4x zooms of the feet with anchor/ground/±4 px ticks (feet_{dir}_{white,dark,grey}.png); lineup.png; alpha_classes.png; edges_{dark,white,mag}.png; byte comparison of shifted v2 against v3.

## 1. Boot ground contact (anchor 600,1540, tolerance ±4 px)
- FRONT: PASS. Both soles bottom out at y=1540 (alpha about 231 there, 1541 is the antialias edge). The contact span at 1540 runs x 548-655, centre 601.0 (within 4 px of the bottom: 529-672, centre 600.4). Offset is about -1 px horizontally and 0 px vertically. The anchor sits in the gap between the two boots.
- BACK: PASS. Heel bottoms are at 1539/1540, with heels at x 548-588 and 608-648. The centre between the heels is 598, so the offset is +2 px horizontally and 0 to 1 px vertically. The forefoot soles sit higher (about 1525), which is plausible perspective.
- LEFT (facing screen-left): PASS. The forefoot sole is at 1540 (x 512 to about 604) and the heel at 1538 (x 643-687). The toe-to-heel span is 512-687, midpoint 599.5, so the offset is about +0.5 px. The heel is 2 px above the line, which is within tolerance.
- RIGHT (facing screen-right): FAIL. The forefoot sole is at 1539/1540 (x about 596-677), but the block heel (x 510-562) bottoms at y=1533 (alpha 174-213, gone by 1534/1535). That leaves it 6-7 px above the ground line, so the boot reads slightly toe-down or tiptoe. The heel-to-toe span is 510-677, midpoint 593.5, so the anchor is +6.5 px toward the toe, outside ±4. Measured against the grounded forefoot only (x 598-662 within 2 px of the bottom, centre 630), the offset is -30 px. The mirror view (left) has the heel within 2 px of the ground, so this is direction-specific. It already exists in the official right.png art and is not a v3 regression. Fixing it needs either an art correction (about 2.3 degrees of rotation about the toe, or redrawing the heel down by 6 px) or at least a +6 px x shift if only the horizontal is fixed.
- The bottom-most pixel being 1540 was not taken as proof. All four have their solid (alpha>=128) bottom at 1540. The rows below 1541 hold only alpha<=2 noise.

## 2. Cross-direction consistency at the anchor
PASS (with note). All four put their solid ground contact on y=1540. Silhouette heights are 1506 / 1500 / 1508 / 1491 px (F/R/B/L), within about 1%. Left is the shortest because the hat is tilted. None visibly floats or sinks in lineup.png. The exception is the right view's raised heel (item 1), which makes that direction look like it is standing slightly on its toes.

## 3. Design consistency (4 v3 directions and the official originals)
FAIL, but all of these are inherited. v3 matches the official originals for every item: v3 equals v2 shifted, and v2 equals the originals at about 0.99-1.0 scale. None of it is a v3 regression. Contradictions between directions:
- Cape length: in the back view the cape is much shorter than the side views imply. The lowest cape pixel outside the boots is y=1316 (back) against 1443 (front), 1515 (right) and 1482 (left). The side views show the rear of the cape reaching mid or low calf. The back view hem ends around the knee or upper calf.
- Hat crystal: the right view has an extra large crystal pendant hanging from the ribbon under the flower, in addition to the one on the hat tip. Front and back show only the tip crystal.
- Hat laurel embroidery: front, right and back show a gold laurel sprig on the crown. In the back view it is on the character's left side, which faces the viewer in the left view, but the left view's crown has no laurel, only band ornaments.
- Hat flower: front and right show a two-flower cluster with green leaves. The back shows a single flower with gold leaves. This is minor.
- Consistent items: big purple witch hat with gold bands, flower and ribbon on the character's right, and the tip pointing to her right in front and back. Dark short blunt bob with bangs. Round gold glasses (F/R/L). Flower hair clips on both sides (F/R/L). Crystal earrings. Capelet with the book-and-laurel crest (both shoulders in front, upper back in back, near shoulder in the side views). Purple plaid skirt panel. Dark thigh-high stockings with the garter clip on the right thigh only (visible in front and right, correctly absent in left). Shoulder bag on the right hip, crossbody from the left shoulder: correct in front and back, visible in right, hidden in left with only the strap over the left shoulder. Potion vials at front-centre/left of the belt, visible in F/R/L, absent in back. These are all consistent.

## 4. Fringe / halo / shadow
PASS (with notes). On near-black, white and green, the hat brim, cape hems, ribbons, hair and boots show no light or dark halo and no drop shadow beyond the art's own dark lineart. The 1-3 px ring just outside the solid edge has mean luminance 67-73, darker than the inner edge (81-102), which matches the lineart. Pixels with luminance >200 and alpha>=32 in that ring number 0-4 per image. Notes:
- Invisible matte residue: 2,500-4,600 speck pixels per image more than 6 px from the figure, all alpha<=5, with a few hundred more than 20 px away (alpha 1). The bounding box at alpha>=1 is much wider than the figure (for example right: x 12-994 against a solid x 150-766). Nothing shows when composited, but a renderer or packer that trims by alpha>0 will produce oversized bounds. Zeroing alpha<8 would clean it.
- The body is not fully opaque: the median alpha is 253 and most pixels are 250-254 (front has no alpha-255 pixel at all). The originals are the same. The background shows through by about 1%, which is invisible in normal use but may matter for stacking or effects.
- No sub-ground shadow: row 1541 is only the antialiased sole edge (alpha <=28 front, <=69 left), and everything below 1542 is alpha<=2.

## 5. Pure translation of v2
PASS. For all four directions, shifting v2 by the stated (dx,dy) gives a byte-identical RGBA match with v3: max abs difference 0, 0 differing pixels. Front (+22,-18), right (-96,-18), back (+36,-18) and left (+79,-18) were all verified. Non-zero-alpha pixel counts are identical, so nothing was clipped.

## Summary
v3 does exactly what it claims (pure translation), and front, back and left are anchored within ±2 px. The right view fails ground contact: its heel floats 6-7 px and the anchor sits 6.5 px toe-ward of the heel-to-toe midpoint. Design contradictions exist between directions (back cape length, extra right-view crystal, missing laurel in left), but they all come from the official originals.

OVERALL: FAIL. The blocker is right-view ground contact. Design items in Q3 are inherited notes for the art owner, and Q4 items are optional cleanups.
