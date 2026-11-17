# Morwen canonical vs generated turnaround — visual QA 2026-11-17

## Sources inspected directly
- GitHub Actions https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44006357800 (SUCCESS)
- Artifact 14293664979: five original images plus SOURCE_VERIFY.json, all 5/5 SHA256 and byte sizes match assets/canonical/morwen/2026-11-16/MANIFEST.json.
- Official design sheet: MORWEN_DESIGN_SHEET_APPROVED_SOURCE.jpg, SHA256 d9730dad8b1791204bb39f52697a176d4556e82a33442fdc0c101059bcc7113b.
- Layer0: front/back/left/right source PNGs directly inspected.
- Compared against the most recent ChatGPT-generated four-view art candidate in this conversation (NOT in repository, NOT approved).

## G1 discrepancies (generated candidate FAIL)
1. Hat ornament: canonical purple flower, large ribbon and hanging violet diamond; generated candidate substitutes a white flower and different ornament.
2. Crest: canonical open-book in laurel wreath on the left shoulder and matching academy motifs; generated crest is generic/alternate.
3. Skirt: canonical vivid purple checked/plaid pleated skirt; generated skirt is largely plain purple.
4. Legwear: canonical dark purple thigh-high stockings with exposed upper thigh and a distinct top band; generated knee/below-knee socks leave much more bare leg. The source refers to ニーソックス; follow source **visible stocking height** rather than generic sock naming.
5. Garter: canonical anatomical RIGHT leg, front viewer-left, back viewer-right, visible from the back; generated rear garter is absent.
6. Bag: canonical leather satchel with defined flap, star/ornament, buckles, strap placement and cross-body routing; generated geometry/decor differ.
7. Potion holders: canonical two gold-capped violet vials and connecting chain; generated layout is not source-faithful.
8. Silhouette: canonical cape length, trim pattern and drape differ; generated design cannot be accepted on aesthetic similarity alone.
9. Hair/face: purple bob, glasses, purple eyes broadly recognizable; exact facial proportions, side bangs, earrings, hat placement need detailed overlay review.
10. Target 7.75-head ratio: labels on generated sheet are NOT measured proof; head count remains NOT_RUN.

## Corrected production rules
- Treat approved design sheet as the sole current design authority; Layer0 four views for body/inner-layer construction. Do not use earlier generated candidate as an input reference for motifs or costume.
- New art must preserve purple flower/ribbon/diamond, book-laurel crest, checked skirt, dark thigh-high stockings, right garter rear continuity, accurate satchel, potion vials and chain, cape pattern.
- Four-view head/sole ruler must be measured from anatomical crown to chin, excluding hat, and verified independently. Four directions must align without mirror-copying asymmetric items.
- No invented motif, palette, hardware or clothing feature. When occluded in source, flag uncertainty rather than fabricate.
- Candidate art is rejected as a formal 3D geometry source; source originals remain untouched.

## Gates
G1 FAIL (generated candidate), G2 FAIL for fidelity, G3 generated candidate measured ratio NOT_RUN, G4 NOT_RUN. Canonical source integrity PASS. No model changes, main merge or publication.
