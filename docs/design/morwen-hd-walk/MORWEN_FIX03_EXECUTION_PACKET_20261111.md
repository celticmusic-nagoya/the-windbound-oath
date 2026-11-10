# MORWEN-FIX-03 execution packet

Status: READY FOR BASE-BODY RECONSTRUCTION; IMAGE EDIT NOT RUN
Source: FIX-02 UPPER_BODY_EDIT_SPEC.md, director decisions in MORWEN_FIX03_DIRECTOR_DECISIONS_20261111.md.

## Step 1 — Lock common body
- Work from approved front-view and existing four-view aligned images; record source commit SHA and file hashes.
- Produce BASE_BODY_SPEC.json with coordinate convention, head/neck, shoulders, elbows, wrists, pelvis, hips, knees, ankles and ground contacts, confidence for obscured joints, and cross-view landmark comparisons.
- Use (600,1540) as nominal foot-contact anchor, distinguishing actual heel and forefoot contact.
- Do not treat clothing outer contour as bone location. Obtain independent visual QA and only then freeze the base.

## Step 2 — Rebuild back upper body as a new candidate
- Use FIX-01 back boots and lower-body composition as protected reference, preserve heel-level flared robe tails and central rear slit.
- Redraw hair lower section to match front bob length: diagnostic target ends around y370–380, subject to locked base-body anatomy.
- Align shoulders and cape upper edge around y384 and first cape lower edge around y540; preserve academy insignia and cape layering.
- Reconstruct upper arms naturally between the raised shoulders and existing cuffs around y780–790, keeping approved outward arm pose and no robe/sleeve intersection.
- Reconnect crossbody strap to stationary bag; preserve buckle, flower green leaves, gold laurel, skirt and approved garter ornaments.
- Hat crown/brim position should match front-view height; do not accept 14–20px offset as final. Adjust hat placement anatomically, not by distorting artwork.
- Edit masks from FIX-02 must be visually revalidated before use (revision NOT_RUN).
- No whole-image stretching, flip, automatic redraw of protected details, or fabricated pixel QA.

## Step 3 — QA and delivery
- New candidate PNG with alpha=0 outside subject; store original source separately.
- Compare all four directions at 1200x1600 and fixed feet; measure head, hat, shoulders, cuffs, pelvis, socks, boot top and soles.
- Check robe front opening, back slit, long side hems, asymmetric check on character-right skirt side only, cape/sleeve occlusion, bag and hat ornaments.
- Provide comparison PNG, base-body overlay, masks, PROCESSING_FIX03.json, QA_REPORT_FIX03.md, MANIFEST SHA-256, independent visual QA evidence.
- Store on work branch under assets/candidates/morwen/real-canon-final-04/fix03/ and append to Draft PR #221.
- Any missing rendering or independent QA must be BLOCKED/NOT_RUN. Do not overwrite official art, merge main, integrate game or publish website.

## Next gate
Independent body and costume QA PASS -> director approval of FIX-03 candidate -> only then HD pixel-art planning.
