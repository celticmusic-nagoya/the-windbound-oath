# THE WINDBOUND OATH — Character Asset Generation Guide v1.2

Status: Director-adopted production standard
Scope: Multi-angle character art, sprites, costumes, outfit variants and revisions
Relationship: Extends v1.1; complements CHARACTER_BASE_BODY_FIRST_WORKFLOW_v1.0.md and AI_ARTIFACT_SHARING_POLICY_v1.0.md.

## 1. Two locked bases
### 1.1 Base-body first
Before any clothing, headwear, bags or ornament, create a neutral non-explicit construction body for front, back and both sides. Lock stature, head/body ratio, shoulders, waist, hips, limbs, joints and foot contact. Separate actual anatomy from pose/perspective silhouette. Document inferred hidden joints and confidence. Freeze only after independent QA.

### 1.2 Anchor points and grids
On a shared master canvas, record pixel coordinates and normalized positions for crown, shoulders, waist, hip, knees, ankles, sole contact; add garment-specific anchors for belt, cape edges, robe hems, skirt and boot tops. Use body-relative fractions where meaningful, and explicit tolerances. Do not independently scale one angle to disguise anatomical mismatch.

## 2. Canonical design regulation (Morwen)
- Skirt: front and central panels plain purple; purple/yellow check only on the character's RIGHT pleated side beneath/near the bag. This is physically the same side in all angles, never mirrored automatically.
- Robe: long, voluminous, dramatically flared side hems; rear central V-shaped slit showing hip/thigh silhouette and approved garter ornaments. Front opening has clear negative space between legs without excess robe fabric.
- Hat: flower leaves GREEN; continuous GOLD laurel-leaf pattern on brim and band follows three-dimensional curvature. Maintain approved flower, ribbon, crystal, face, glasses, purple bob, bag, insignia.
- Match purple, gold, pink and green saturation/brightness across views against approved sampled palette; report measured color deviations, do not claim identical colors merely from a prompt.
- Costume occlusion must be physically coherent (shoulder, sleeve, robe, strap, skirt and leg).

## 3. One task / one intent
Every image-edit pass has one primary objective, source master canvas, protected regions, edit mask, acceptance criteria and before/after comparison. When a correction requires linked changes (e.g. shoulder, hair and sleeve), treat as one anatomically coupled rebuild with explicit subchecks, rather than destructive isolated pixel stretching.

## 4. Positive structural descriptions
Describe intended construction positively: the opening between legs shows transparent background, rear robe edges frame a V slit, robe lining follows its own cloth surface, shoulder-to-cuff path is continuous. Negative constraints are secondary.

## 5. Master canvas and hybrid retouch
- Always supply and preserve the full-body master canvas and grid/anchor overlay even for partial edits. Crop close-ups only as supplementary detail views.
- Keep approved hat, bag, ornaments and insignia as protected source layers when appropriate; manual composite approved pixels, then blend boundaries and texture. Review perspective and light direction before transplanting pixels.
- Preserve original PNGs and layer provenance. Do not overwrite source art, change unrelated areas or introduce baked checkerboards. Verify alpha transparency.

## 6. QA / delivery
Gate A: base-body and anchors measured and independently validated.
Gate B: multi-angle costume construction and asymmetric placement validated.
Gate C: palette, ornaments, transparent alpha, source hashes and master-canvas consistency validated.
Gate D: independent visual QA and director approval.

Deliver BASE_BODY_SPEC, ANCHOR_GRID_SPEC, MASTER_CANVAS reference, candidate layers, masks, before/after comparisons, process record, QA report, SHA-256 MANIFEST in GitHub work branch and Draft PR. Any unexecuted test is NOT_RUN; unresolved artwork is BLOCKED. Do not merge main, publish, or integrate without director authorization.

## 7. Morwen FIX-03 application
Follow the locked front-view base-body and shared 1200x1600 canvas, foot anchor nominal (600,1540). Reconstruct back upper body and hat/shoulder/hair/cape/arms without warping, preserve FIX-01 boots and lower robe. Validate revised FIX-02 masks before using them. The FIX-03 artwork and independent QA are not yet complete; do not begin HD pixel-art production until passed.
