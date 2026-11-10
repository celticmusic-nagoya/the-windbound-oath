# THE WINDBOUND OATH — Character Asset Generation Guide v1.1

Status: Director-adopted production standard
Scope: All future multi-angle character artwork and revisions
Supersedes: None. Complements CHARACTER_BASE_BODY_FIRST_WORKFLOW_v1.0.md and AI_ARTIFACT_SHARING_POLICY_v1.0.md.

## 1. Two fixed foundations
### 1.1 Base-body first
Before drawing costume, headwear, bags or ornaments, construct a neutral anatomical base body for front, back, left and right. Freeze stature, head-to-body ratio, shoulders, waist, hips, arms, legs, joints and feet. Distinguish actual anatomical landmarks from costume silhouette and angle-dependent pose. Record inferred or occluded joints with confidence and require QA before freeze.

### 1.2 Anchor and grid guide
Use a single aligned canvas and coordinate convention. Lock horizontal reference lines for crown, shoulder, waist, hip, knee, ankle and ground contact; add costume anchors for belt, cape edges, skirt hem, robe hem, boot tops and accessories. Express garment placements relative to stable body landmarks as well as pixel coordinates; record tolerances and angle-specific occlusions. For current Morwen work, use 1200x1600 canvas and nominal foot anchor (600,1540), subject to actual contact verification.

## 2. Canonical costume specification
### 2.1 Layered costume construction
Dress the frozen body in coherent layers. Never change the body to fit the costume; if a change is necessary, revise and reapprove the body specification first.

Morwen skirt: plain purple across the front/center, with asymmetric purple-and-yellow plaid only on the character's RIGHT side pleated section beneath/near the bag. Project this same physical location into every angle; do not mirror automatically.

Morwen robe: dramatic long and wide flared left/right side hems; central rear slit reveals hip/thigh silhouette and approved garter ornaments, with a clear opening and no extra central hanging panel concealing the legs. Keep physically coherent robe/sleeve overlap across views.

### 2.2 Fixed color and ornament anchors
Hat flower leaves are GREEN. Hat brim and band carry continuous GOLD laurel-leaf motifs following the curved surface. Preserve the approved face, glasses, purple bob, bag and crossbody strap, insignia and high-definition illustrative finish. Maintain original textures where possible.

## 3. Generation and editing discipline
### 3.1 One task per revision
Separate changes to stature/shoulder height, hair, robe structure, plaid, hat ornaments and angle. Every candidate must declare one primary correction, protected regions and measurable acceptance criteria. Where anatomy requires coupled redrawing, document the coupled dependency instead of performing a misleading isolated warp.

### 3.2 Positive structural prompts
Describe the intended visible structure concretely: e.g. the gap between legs shows transparent background; robe lining does not bridge the rear slit; shoulder-to-cuff connection follows the approved skeleton. Negative constraints may supplement but must not replace the positive description.

### 3.3 Hybrid image generation and manual compositing
Reuse approved high-quality details (hat, bag, emblems) via layered compositing or masks when technically appropriate; request AI redraw only for junctions, shading and texture harmonization. Preserve originals and record transforms and provenance. Pixel copy/paste across perspective changes must be visually reviewed; never assume it is automatically correct.

## 4. QA and GitHub delivery gates
Gate A: Base-body measurements and anchor overlays PASS.
Gate B: Costume structure, front/back/side continuity and asymmetry PASS.
Gate C: Color, ornaments, transparency and protected details PASS.
Gate D: Independent visual QA PASS and director approval.

Deliver BASE_BODY_SPEC, ANCHOR_GRID_SPEC, design spec, layered candidates, edit masks, process record, comparison images, QA report and SHA-256 MANIFEST to a work branch and Draft PR. Mark unrun checks NOT_RUN and blocked edits BLOCKED. Do not overwrite canonical originals, merge main, integrate into game or publish without explicit authorization.

## 5. Application to Morwen FIX-03
Reconstruct and independently validate the common base body before back upper-body redrawing. Align shoulder/cape, hair and hat landmarks with the front reference while protecting FIX-01 boots and approved robe silhouette. Treat earlier 45–55px hair and ~48px shoulder offsets as diagnostics, not instructions to stretch pixels. Do not begin HD pixel-art production before four-angle independent QA and director approval.
