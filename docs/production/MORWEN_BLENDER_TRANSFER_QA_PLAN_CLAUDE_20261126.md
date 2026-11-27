# Morwen VRM→Blender transfer: independent QA baseline and improvement priority (Claude, 2026-11-26 07:40 JST)

Read-only. No native/VRM/Blender write, no dispatch, no merge.
Sync: main `2d9c967d`; policy PR #565 `a71abcbd` (open, early Blender transfer; director approval #427 comment 7176343338); #427 `df986c7e`; #540 parent `65e67979`.
Launch: launcher `2e19ae75` / child `db7b9f4e` unchanged on main; no pushed Codex launch diff; no VRM export run exists yet. → VRM/Blender G2/G3 **NOT_RUN**.

## 1. Inputs actually verified
- Transfer source checkpoint artifact 15018109141 (run 45605491226) ZIP `b210fb49…` = API digest; `face-mouth-candidate-not-adopted.vroid` SHA256 `acc7805b6a5b63913bccb7c28e30e1c9e4da6473ed083b5c0673f73cdca9e23a` (= policy), parent `55cf70f2…`; only change vs parent: Mouth Width −0.026→0.044, reopen equal. **Expires 2026-12-02T11:52:56Z** — preserve before then.
- Layer0 four views (archive `d7e006a3…`, 7807–7810) and clothed design (archive `a290131b…`).
- Existing-model images: A run 45634559551 baseline front/right4/left8/left4 and checkpoint `mouth-reopened.png`.
- Photo-style generated material sheets: not in the repository (local to director/ChatGPT) → **SYNC_UNVERIFIED**; material-only reference per policy.

## 2. Existing VRoid model vs references (what Blender must fix)
| Module | Observation (measured where possible) | Priority |
|---|---|---|
| Body proportion | No existing capture shows full body with feet → head-count **not measurable** from VRoid images. Layer0 front: visible height 987 px (y17–1003), hair top→chin(y≈178) 161 px → **≈6.1–6.7 heads** (u ±0.3). Project 3D policy is 7.5–8 heads. Conflict between Layer0 image and policy → **director decision (D0) required before body sculpt**; measure the VRM in Blender (metres, armature) first. | Critical |
| Outfit | Entire outfit is VRoid stock (navy school blazer, ribbon tie, grey/candidate plaid skirt, bare legs, short black socks). Canon: purple-black capelet/coat with gold rune border and back sigil, vest/corset, white frilled blouse + purple bow, dark pleated skirt with right-front plaid inset, thigh stockings + right garter, lace-up heeled boots, hat, glasses, bag, vials. Nothing is reusable as final. | Critical (largest gap) |
| Hair | VRoid: centre-parted straight hair to ~shoulder, flat, side-swept bangs; edge speckle (light pixels on hair silhouette) in all captures. Layer0: layered bob ending near jaw/neck, fringe over brows, volume at crown and outward-flicked ends. Colour: VRoid median 92,56,92; Layer0 front/back 71,46,71 / 101,62,100 (purple); clothed master 47,33,53 (near-black violet). **Hair colour differs between the two canon sources → director D0 decision** (proposal: clothed master for final, Layer0 for shape). | Major |
| Face | Face is ≈60 px in every capture → eye/mouth shape **not assessable**; only colour family (violet iris) matches. Layer0: larger almond eyes, defined upper lash line, small nose, soft V jaw. Do face QA from Blender close renders (≥512 px face). | Major (HOLD for evidence) |
| Body surface | Stock skin shading, visible jagged outline pixels on legs/arms (outline width). | Minor (material stage) |

Improvement order in Blender: **(1) proportion decision + body/base mesh scale → (2) face (close renders vs Layer0 front/profile) → (3) hair shape (HairHarpy evaluation per policy) and colour decision → (4) innerwear/legwear/garter per Layer0 → (5) outer costume pieces (skirt C1 logic, vest, blouse, capelet, coat, boots) → (6) props (hat, glasses, bag, vials, book)**. Costume before body proportion is fixed would be rework.

## 3. VRM→Blender transfer QA checklist (G3 first, then G2)
Acceptance for the first transfer (record value, tolerance, result):
1. Provenance: VRoid version 2.16.0, source `.vroid` SHA = `acc7805b…`, VRM file SHA, VRM spec (0.x/1.0), license/meta fields copied; add-on name+version+SHA, Blender 5.3.0 build hash.
2. Scale: total height in m (from mesh bounds, A-pose), head height (crown–chin) → head count; compare to D0 decision.
3. Armature: humanoid bone map complete (hips…toes, 3-finger chains, eyes, jaw if present), bone count equal VRM vs Blender import; rest pose A/T recorded.
4. Mesh: per-object vertex/face counts equal to VRM accessor counts; no non-manifold introduced; normals preserved (split normals).
5. Skin weights: every vertex weighted, max 4 influences, no zero-weight; deformation test at 6 poses (arms up/forward, sit, step, head turn) with render.
6. Expressions: blendshape/expression count and names equal; 5 visemes + blink L/R + 4 emotions render.
7. Spring bones/colliders: count preserved (or documented loss).
8. UV/Textures: each texture decoded pixel SHA equal to VRM-embedded image; UV channel count equal; MToon→Blender material mapping documented (outline, shade colour, emission).
9. Save `.blend`, close, reopen; repeat 3–8 counts; file SHA recorded.
10. Matched renders: same 4 views + 3/4 as Layer0 (orthographic, camera at chest height, same framing ratio), flat/unlit pass and lit pass; face close-up ≥512 px; then G2 comparison.

## 4. Launch audit delta
No new pushed launcher/child change since `0a3c3577`. The new VRM export step will need a new mode; under current `eligible()` that again requires hard-coded transition edits — reinforces replacing it with the stage record + shared lease (audit `0785b264`). The VRM export stage must hold the canonical Morwen native lease while VRoid runs; the Blender import stage writes a different asset key (blend) and can run in parallel only on its own key.
